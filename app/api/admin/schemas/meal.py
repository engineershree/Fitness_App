"""
Meal related schemas for admin API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MealBase(BaseModel):
    bmi_category_id: int
    meal_type: str  # breakfast, lunch, dinner
    food_item: str
    calories: int
    description: Optional[str] = None
    meal_image: Optional[str] = None

class MealCreate(MealBase):
    pass  # No user_id needed for admin meals

class MealUpdate(BaseModel):
    food_item: Optional[str] = None
    calories: Optional[int] = None
    meal_type: Optional[str] = None
    bmi_category_id: Optional[int] = None
    description: Optional[str] = None
    meal_image: Optional[str] = None

class MealResponse(MealBase):
    id: int
    created_at: Optional[datetime] = None
