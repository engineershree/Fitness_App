"""
Explore Activity related schemas for admin API
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ExploreActivityBase(BaseModel):
    activity_name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    duration: str = Field(..., min_length=1)
    activity_type: str = Field(..., min_length=1)
    image: Optional[str] = None
    video: Optional[str] = None

class ExploreActivityCreate(ExploreActivityBase):
    pass

class ExploreActivityUpdate(BaseModel):
    activity_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    duration: Optional[str] = Field(None, min_length=1)
    activity_type: Optional[str] = Field(None, min_length=1)
    image: Optional[str] = None
    video: Optional[str] = None

class ExploreActivityResponse(ExploreActivityBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
