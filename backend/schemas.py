from pydantic import BaseModel
from typing import Optional
from enum import Enum

# Enums
class UserRole(str, Enum):
    SUPPLIER = "supplier"
    MANUFACTURER = "manufacturer"
    LOGISTICS = "logistics"
    CONSUMER = "consumer"
    ADMIN = "admin"

# Models
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

# 🔑 Add this LoginData model
class LoginData(BaseModel):
    username: str
    password: str