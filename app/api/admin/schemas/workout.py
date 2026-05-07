"""
Workout related schemas for admin API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WorkoutBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int
    calories_burned: Optional[int] = None
    difficulty_level: Optional[str] = None
    category: Optional[str] = None
    workout_type: Optional[str] = None
    workout_image_url: Optional[str] = None
    workout_video_url: Optional[str] = None

class WorkoutCreate(WorkoutBase):
    pass  # No user_id needed for admin workouts

class WorkoutUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    calories_burned: Optional[int] = None
    difficulty_level: Optional[str] = None
    category: Optional[str] = None
    workout_type: Optional[str] = None

class WorkoutResponse(WorkoutBase):
    id: int
    created_at: Optional[datetime] = None
