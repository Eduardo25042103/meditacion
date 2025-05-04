from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr = Field(..., example="user@gmail.com")
    password: str = Field(..., min_length=6, example="Pass_3xampl3")

