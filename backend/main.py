from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, auth
from database import SessionLocal, engine
from services.fraud_detection import FraudDetectionService
from services.blockchain_service import BlockchainService
from contextlib import asynccontextmanager
from loguru import logger

fraud_detector = FraudDetectionService()
blockchain_service = BlockchainService()

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    if not await blockchain_service.init_stream():
        logger.warning("Application starting in offline mode (no blockchain)")
    yield
    # Shutdown
    logger.info("Shutting down application...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication Endpoints
@app.post("/auth/signup", response_model=schemas.UserOut, status_code=201)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_pw = auth.get_password_hash(user.password)
    logger.debug(f"Hashed password: {hashed_pw}") 
    
    new_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_pw,
        role=user.role  
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=schemas.Token)
def login(request: schemas.LoginData, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(models.User).filter(models.User.email == request.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not auth.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = auth.create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}

# Product Endpoints
@app.post("/products", response_model=schemas.ProductOut)
async def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != models.UserRole.SUPPLIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only suppliers can register products"
        )
        
    # Check for blocked supplier
    penalty = db.query(models.SupplierPenalty).filter(
        models.SupplierPenalty.supplier_id == current_user.id
    ).first()
    
    if penalty and penalty.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is blocked due to {penalty.penalty_count} violations"
        )
        
    try:
        # Check for counterfeit
        logger.info(f"Running fraud detection for product: {product.product_name}")
        is_counterfeit, confidence, reason = fraud_detector.get_counterfeit_confidence(
            product.model_dump()
        )
        logger.info(f"Prediction result: {is_counterfeit}, Confidence: {confidence:.2%}, Reason: {reason}")
        
        # Remove description before passing to ORM
        product_data = product.model_dump()
        product_data.pop("description", None)
        
        # Create product
        new_product = models.Product(
            **product.model_dump(),
            supplier_id=current_user.id,
            is_flagged=is_counterfeit,
            fraud_confidence = float(confidence) if confidence is not None else None
        )
        
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        if is_counterfeit:
            flagged_product = models.FlaggedProduct(
                product_id=new_product.id,
                supplier_id=current_user.id,
                reason=reason
            )
            
            db.add(flagged_product)
            
            if not penalty:
                penalty = models.SupplierPenalty(supplier_id=current_user.id)
                db.add(penalty)
                
            penalty.penalty_count += 1
            
            if penalty.penalty_count >= 3:
                penalty.is_blocked = True
                
            db.commit()
            
            new_product.status = "warning"
            new_product.message = f"Product flagged as potentially counterfeit. Confidence: {confidence:.2%}"
            
        else:
            try:
                blockchain_tx = await blockchain_service.store_product(new_product.__dict__)
                new_product.blockchain_tx = blockchain_tx
            except Exception as e:
                logger.error(f"Blockchain error: {str(e)}")
                new_product.status = "partial_success"
                new_product.message = "Product registered but blockchain storage failed"
                db.commit()  # Still commit the product without tx hash
                db.refresh(new_product)
            else:
                db.commit()  # Commit with tx hash
                db.refresh(new_product)
                
        return new_product
        
    except Exception as e:
        db.rollback()
        logger.error("Product registration failed: {}", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register product: {str(e)}"
        )

@app.get("/products", response_model=List[schemas.ProductOut])
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return products

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)