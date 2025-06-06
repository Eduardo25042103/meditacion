from pydantic import BaseModel
from typing import List, Optional
from app.schemas.auth_schemas import UserResponse


class PreferencesCreate(BaseModel):
    preferred_duration: str
    preferred_time: str
    goals: List[str]


class PreferencesOut(PreferencesCreate):
    id: int

    class Config:
        from_attributes = True
        orm_mode = True


class PreferencesAllOut(PreferencesCreate):
    id: int
    user_id: int
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True
        orm_mode = True
