from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, auth
from database import SessionLocal, engine
from services.fraud_detection import FraudDetectionService
from services.blockchain_service import BlockchainService
from services.order_service import OrderService
from services.payment_service import PaymentService
from contextlib import asynccontextmanager
from loguru import logger
from models import UserRole

fraud_detector = FraudDetectionService()
blockchain_service = BlockchainService()
order_service = OrderService()
payment_service = PaymentService()


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

    valid_products = []
    for product in products:
        if (
            product.created_at is not None and
            product.status is not None and
            product.message is not None and
            product.is_flagged is not None
        ):
            valid_products.append(product)
        else:
            logger.warning(f"Invalid product data: {product}")

    return valid_products

@app.delete("/products/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Fetch the product from the database
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if the current user is authorized to delete the product
    if current_user.role not in [models.UserRole.ADMIN, models.UserRole.SUPPLIER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this product"
        )
    
    if current_user.role == models.UserRole.SUPPLIER and product.supplier_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete products you own"
        )
    
    try:
        # Delete the product
        db.delete(product)
        db.commit()
        logger.info(f"Product with ID {product_id} deleted successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )
    
@app.post("/orders", response_model=schemas.OrderOut)
async def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        # Create order in database
        new_order = models.Order(
            **order.model_dump(),
            consumer_id=current_user.id,
            status="NEW"
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        # Store in blockchain
        tx_id = await blockchain_service.store_order(new_order.__dict__)
        if tx_id:
            # Update order with blockchain transaction ID
            new_order.blockchain_tx = tx_id
            db.commit()
            logger.info(f"Order created with blockchain tx: {tx_id}")
        
        return new_order

    except Exception as e:
        db.rollback()
        logger.error(f"Order creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.put("/orders/{order_id}", response_model=schemas.OrderOut)
async def update_order_status(
    order_id: int,
    order_update: schemas.OrderUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        for key, value in order_update.model_dump().items():
            setattr(order, key, value)

        # Store update in blockchain
        tx_id = await blockchain_service.update_order(order.__dict__)
        if tx_id:
            order.blockchain_tx = tx_id  # Store the latest transaction ID
            logger.info(f"Order updated with blockchain tx: {tx_id}")
        
        db.commit()
        return order

    except Exception as e:
        db.rollback()
        logger.error(f"Order update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/orders/my-orders", response_model=List[schemas.OrderOut])
async def get_my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return order_service.get_all_orders(db, current_user.id)

# get all the orders eg: GET /orders?status=DELIVERED&start_date=2025-01-01
@app.get("/orders", response_model=List[schemas.OrderOut])
async def get_filtered_orders(
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    consumer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Admins and logistics can see all or filter by consumer_id
    if current_user.role in [models.UserRole.ADMIN, models.UserRole.LOGISTICS]:
        if consumer_id:
            query = db.query(models.Order).filter(models.Order.consumer_id == consumer_id)
        else:
            query = db.query(models.Order)
    elif current_user.role == models.UserRole.CONSUMER:
        query = db.query(models.Order).filter(models.Order.consumer_id == current_user.id)
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    if status:
        query = query.filter(models.Order.status.ilike(f"%{status}%"))
    if start_date:
        query = query.filter(models.Order.created_at >= start_date)
    if end_date:
        query = query.filter(models.Order.created_at <= end_date)

    return query.all()

@app.get("/orders/{order_id}", response_model=schemas.OrderOut)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    order = order_service.get_order(db, order_id)
    
    # Check if user has access to this order
    if (current_user.role == models.UserRole.CONSUMER and 
        order.consumer_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    return order

@app.get("/orders/{order_identifier}/ledger")
async def get_order_ledger(
    order_identifier: str,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get order ledger by ID or transaction hash"""
    try:
        ledger = await blockchain_service.get_order_history(order_identifier)
        if not ledger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No blockchain records found for this order"
            )
        return ledger
    except Exception as e:
        logger.error(f"Failed to fetch ledger: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch order ledger"
        )
    
# display all flagged-products along with their supplier
@app.get("/flagged-products", response_model=List[schemas.FlaggedProductWithDetails])
async def get_flagged_products(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view flagged products"
        )

    # Query FlaggedProduct along with associated User (supplier) and Product
    flagged_products = (
        db.query(models.FlaggedProduct)
        .join(models.User, models.FlaggedProduct.supplier_id == models.User.id)
        .join(models.Product, models.FlaggedProduct.product_id == models.Product.id)
        .add_entity(models.User)
        .add_entity(models.Product)
        .all()
    )

    result = []
    for fp, user, product in flagged_products:
        result.append({
            "id": fp.id,
            "product_id": fp.product_id,
            "supplier_id": fp.supplier_id,
            "reason": fp.reason,
            "created_at": fp.created_at,
            "supplier": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            },
            "product": {
                "id": product.id,
                "name": product.product_name,
                "category": product.category,
                "ingredients": product.ingredients,
                "price": product.price,
                "description": getattr(product, "description", None),  # Handle missing description
                "created_at": product.created_at or "1970-01-01T00:00:00Z",  # Default datetime
                "is_flagged": product.is_flagged if product.is_flagged is not None else False,  # Default boolean
                "fraud_confidence": product.fraud_confidence,
                "blockchain_tx": product.blockchain_tx
            }
        })

    return result

@app.post("/orders/{order_id}/payment", response_model=schemas.PaymentOut)
async def create_payment(
    order_id: int,
    payment: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        # Check if user is consumer
        if current_user.role != models.UserRole.CONSUMER:
            raise HTTPException(
                status_code=403, 
                detail="Only consumers can create payments"
            )
        
        print(order_id)
        # Get order with consumer validation
        order = order_service.get_order(
            db, 
            order_id=order_id, 
            consumer_id=current_user.id
        )
        
        # Check if payment already exists
        existing_payment = db.query(models.Payment).filter(
            models.Payment.order_id == order_id
        ).first()
        
        if existing_payment:
            raise HTTPException(
                status_code=400,
                detail="Payment already exists for this order"
            )
        
        # Create payment
        return await payment_service.create_payment(
            db, 
            order_id=order_id, 
            amount=payment.amount
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment creation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create payment"
        )

@app.post("/payments/{payment_id}/sign", response_model=schemas.PaymentOut)
async def sign_payment(
    payment_id: int,
    signature: schemas.PaymentSignature,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role not in [UserRole.CONSUMER, UserRole.SUPPLIER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to sign payments")
    
    return await payment_service.process_signatures(
        db, 
        payment_id, 
        current_user.role, 
        signature.signed
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)