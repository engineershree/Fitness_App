"""
BMI Classification related schemas for admin API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BMIClassificationBase(BaseModel):
    category_name: str
    min_bmi: Optional[float] = None
    max_bmi: Optional[float] = None

class BMIClassificationCreate(BMIClassificationBase):
    pass

class BMIClassificationResponse(BMIClassificationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class BMIClassificationUpdate(BaseModel):
    category_name: Optional[str] = None
    min_bmi: Optional[float] = None
    max_bmi: Optional[float] = None
