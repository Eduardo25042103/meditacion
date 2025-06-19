from pydantic import BaseModel
from datetime import datetime


class NotificationOut(BaseModel):
    id: int
    message: str
    is_read: bool
    scheduled_time: datetime

    class Config:
        orm_mode = True
        from_attributes = True