# models.py

from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum
from enum import Enum
from database import Base

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