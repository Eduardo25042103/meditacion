from pydantic import BaseModel, Field
from typing import List, Optional


# Meditation type
class MeditationTypeBase(BaseModel):
    name: str = Field(..., example="Mindfulness")
    description: Optional[str] = Field(None, example="Atención plena al momento presente") 
    duration_range: str = Field(..., example="5-30 mins")
    tags: List[str] = Field(..., example=["stress", "sleep", "focus"])


class MeditationTypeCreate(MeditationTypeBase):
    pass


class MeditationTypeUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    duration_range: Optional[str]
    tags: Optional[List[str]]


class MeditationTypeOut(MeditationTypeBase):
    id: int

    class Config:
        orm_mode = True


# Meditation
class MeditationBase(BaseModel):
    title: str = Field(..., example="Respiración consciente")
    duration: int = Field(..., example=10, description="Duración en minutos")
    difficulty: str = Field(..., example="beginner")
    type_id: int = Field(..., example=1)


class MeditationCreate(MeditationBase):
    pass


class MeditationUpdate(MeditationBase):
    title: Optional[str]
    duration: Optional[int]
    difficulty: Optional[str]
    type_id: Optional[int]


class MeditationOut(MeditationBase):
    id: int
    meditation_type: MeditationTypeOut

    class Config:
        orm_mode = True