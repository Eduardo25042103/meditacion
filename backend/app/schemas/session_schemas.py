from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Optional
from app.schemas.meditation_schemas import MeditationOut


class SessionCreate(BaseModel):
    meditation_id: int = Field(..., example=1)
    duration_completed: int = Field(..., example=10, description="Minutos completados")
    date: datetime = Field(..., example="2025-05-16T16:30:00Z")

    @field_validator('date')
    def convert_date_to_naive(cls, v):
        # Convierte a UTC y elimina información de zona horaria
        if v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


class SessionOut(BaseModel):
    id: int
    meditation: Optional[MeditationOut]
    duration_completed: int
    date: datetime


    class Config:
        orm_mode = True
        from_attributes = True