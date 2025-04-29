# models.py

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float, DateTime,Enum as SQLAlchemyEnum
from enum import Enum
from database import Base
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class UserRole(str, Enum):
    SUPPLIER = "supplier"
    MANUFACTURER = "manufacturer"
    LOGISTICS = "logistics"
    CONSUMER = "consumer"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.CONSUMER)

    products = relationship("Product", back_populates="supplier")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, index=True)
    ingredients = Column(String)
    price = Column(Float)
    category = Column(String)
    label = Column(String)
    supplier_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_flagged = Column(Boolean, default=False)  # Add this line
    fraud_confidence = Column(Float, nullable=True)  # Add this line
    blockchain_tx = Column(String, nullable=True)  # Add this line
    status = Column(String, default="success")  # Add this line
    message = Column(String, default="Product registered successfully")  # Add this line

    supplier = relationship("User", back_populates="products")

class SupplierPenalty(Base):
    __tablename__ = "supplier_penalties"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"))
    penalty_count = Column(Integer, default=0)
    is_blocked = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class FlaggedProduct(Base):
    __tablename__ = "flagged_products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    supplier_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))