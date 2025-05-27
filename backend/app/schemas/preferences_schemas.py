from pydantic import BaseModel
from typing import List


class PreferencesCreate(BaseModel):
    preferred_duration: str
    preferred_time: str
    goals: List[str]


class PreferencesOut(PreferencesCreate):
    id: int

    class Config:
        from_attributes = True
        orm_mode = True