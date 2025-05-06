from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr = Field(..., example="user@gmail.com")
    password: str = Field(..., min_length=6, example="Pass_3xampl3")


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orn_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str