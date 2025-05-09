from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr = Field(..., example="user@gmail.com")
    password: str = Field(..., min_length=6, example="Pass_3xampl3")
    role: Optional[str] = Field(default="user", example="user")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str