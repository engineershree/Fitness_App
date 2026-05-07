"""
Quotes related schemas for admin API
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class QuoteBase(BaseModel):
    text: str
    author: Optional[str] = None
    category: Optional[str] = None

class QuoteCreate(QuoteBase):
    pass

class QuoteUpdate(BaseModel):
    text: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None

class QuoteResponse(QuoteBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
