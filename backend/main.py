# app/main.py

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

# app = FastAPI()

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

@app.post("/auth/signup", response_model=schemas.UserOut, status_code=201)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_pw = auth.get_password_hash(user.password)

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
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}

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
        is_counterfeit, confidence, reason = fraud_detector.get_counterfeit_confidence(
            product.model_dump()
        )
        
        # Create product
        new_product = models.Product(
            **product.model_dump(),
            supplier_id=current_user.id,
            is_flagged=is_counterfeit,
            fraud_confidence=confidence
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
                new_product.status = "partial_success"
                new_product.message = "Product registered but blockchain storage failed"
                print(f"Blockchain error: {str(e)}")
        
        return new_product
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register product: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)