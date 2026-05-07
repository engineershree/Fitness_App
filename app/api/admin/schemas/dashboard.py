"""
Dashboard related schemas for admin API
"""
from pydantic import BaseModel

class OverviewResponse(BaseModel):
    total_users: int
    total_workouts: int
    total_meals: int
    active_subscriptions: int
