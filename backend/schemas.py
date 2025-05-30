from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

# Enums
class UserRole(str, Enum):
    SUPPLIER = "supplier"
    MANUFACTURER = "manufacturer"
    LOGISTICS = "logistics"
    CONSUMER = "consumer"
    ADMIN = "admin"

# Auth Models
class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    role: UserRole = UserRole.CONSUMER

class UserOut(BaseModel):
    id: int
    email: str
    username: str
    role: UserRole

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginData(BaseModel):
    username: str
    password: str

# Product Models
class ProductCreate(BaseModel):
    product_name: str
    category: str
    price: float
    ingredients: str

class ProductOut(BaseModel):
    id: int
    product_name: str
    category: str
    price: float
    ingredients: str
    supplier_id: int
    created_at: datetime
    status: str = "success"
    message: str = "Product registered successfully"
    blockchain_tx: Optional[str] = None
    fraud_confidence: Optional[float] = None
    is_flagged: bool = False
    
    class Config:
        from_attributes = True

class SupplierOut(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

class FlaggedProductWithSupplier(BaseModel):
    id: int
    product_id: int
    supplier_id: int
    reason: str
    created_at: datetime
    supplier: SupplierOut

    class Config:
        from_attributes = True

class FlaggedProductOut(BaseModel):
    id: int
    product_id: int
    supplier_id: int
    reason: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Supplier(BaseModel):
    id: int
    username: str
    email: str

class Product(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    created_at: datetime
    is_flagged: bool
    fraud_confidence: Optional[float]
    blockchain_tx: Optional[str]

class FlaggedProductWithDetails(BaseModel):
    id: int
    product_id: int
    supplier_id: int
    reason: str
    created_at: datetime
    supplier: Supplier
    product: Product

class OrderStatus(str, Enum):
    NEW = "NEW"
    CONFIRMED = "CONFIRMED"
    DELIVERED = "DELIVERED"

class OrderCreate(BaseModel):
    # product_id: int
    customer_name: str
    contact_number: str
    delivery_address: str

class OrderUpdate(BaseModel):
    status: OrderStatus
    estimated_delivery_days: Optional[int] = None
    delivery_notes: Optional[str] = None

class OrderOut(BaseModel):
    id: int
    # product_id: int
    customer_name: str
    contact_number: str
    delivery_address: str
    status: OrderStatus
    created_at: datetime
    estimated_delivery_days: Optional[int]
    delivery_notes: Optional[str]
    blockchain_tx: Optional[str]

class BalanceOut(BaseModel):
    total_balance: float

    class Config:
        orm_mode = True
        
class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"

class PaymentCreate(BaseModel):
    order_id: int
    amount: float

class PaymentSignature(BaseModel):
    signed: bool

class PaymentOut(BaseModel):
    id: int
    order_id: int
    amount: float
    status: str
    user_signed: bool
    producer_signed: bool
    admin_signed: bool
    blockchain_tx: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True