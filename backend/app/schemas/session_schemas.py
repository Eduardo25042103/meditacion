from pydantic import BaseModel, Field 
from datetime import datetime
from typing import Optional
from app.schemas.meditation_schemas import MeditationOut


class SessionCreate(BaseModel):
    meditation_id: int = Field(..., example=1)
    duration_completes: int = Field(..., example=10, description="Minutos completados")
    date: datetime = Field(..., example="2025-05-16T16:30:00Z")


class SessionOut(BaseModel):
    id: int
    meditation: Optional[MeditationOut]
    duration_completed: int
    date: datetime


    class Config:
        orm_mode = True
        from_attributes = True