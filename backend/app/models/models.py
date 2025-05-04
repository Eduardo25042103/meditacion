from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sessions = relationship("MeditationSession", back_populates="user")
    stats = relationship("UserStats", back_populates="user", uselist=False)
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)


class MeditationType(Base):
    __tablename__ = "meditation_types"
    id = Column(Integer, primary_key=True)
    name = Column(String) # "Mindfulness", "Metta", las clases que mencionare
    description = Column(String)
    duration_range = Column(String) # 5-30 mins
    tags = Column(ARRAY(String)) #[estrés, sueño, enfoque]
    meditations = relationship("Meditation", back_populates="meditation_type")


class Meditation(Base):
    __tablename__ = "meditations"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    duration = Column(Integer) #en mins
    difficulty = Column(String) #"beginner", "Intermediate", "advanced"
    type_id = Column(Integer, ForeignKey("meditation_types.id"))
    meditation_type = relationship("MeditationType", back_populates="meditations")
    sessions = relationship("MeditationSession", back_populates="meditation")


class MeditationSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    meditation_id = Column(Integer, ForeignKey("meditations.id"))
    duration_completed = Column(Integer) #Tiempo real
    date = Column(DateTime)
    user = relationship("User", back_populates="sessions")
    meditation = relationship("Meditation", back_populates="sessions")



class UserStats(Base):
    __tablename__ = "user_stats"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_minutes = Column(Integer, default=0)
    current_streak = Column(Integer, default=0) # Rachas diarias
    longest_streak = Column(Integer, default=0)
    user = relationship("User", back_populates="stats")


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    preferred_duration = Column(String) # short 5-10 mins medium 11 - 15 long 20 ++
    preferred_time = Column(String) # morning, evening
    goals = Column(ARRAY(String)) #["reduce_anxiety", "better_sleep"]
    user = relationship("User", back_populates="preferences")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    is_read = Column(Boolean, default=False)
    scheduled_time = Column(DateTime) #Para recordatorios 