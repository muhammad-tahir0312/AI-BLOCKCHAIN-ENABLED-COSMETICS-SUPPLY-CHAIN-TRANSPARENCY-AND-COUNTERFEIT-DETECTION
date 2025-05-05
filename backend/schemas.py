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

class FlaggedProductOut(BaseModel):
    id: int
    product_id: int
    supplier_id: int
    reason: str
    created_at: datetime
    
    class Config:
        from_attributes = True