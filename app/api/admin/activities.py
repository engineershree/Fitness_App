from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.models.user_activity_log import UserActivityLog
from app.utils.activity_logger import time_ago
from .dependencies import get_current_admin


def get_recent_activities(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
) -> List[Dict[str, Any]]:
    """
    Get recent user activities for admin dashboard.
    
    Args:
        limit: Number of recent activities to fetch (default: 20)
        db: Database session
        current_admin: Current authenticated admin
    
    Returns:
        List of activity objects with username, description, and time fields
    """
    try:
        # Fetch latest activity logs ordered by created_at DESC
        recent_logs = db.query(
            UserActivityLog
        ).order_by(
            desc(UserActivityLog.created_at)
        ).limit(limit).all()
        
        # Format the response
        activities = []
        for log in recent_logs:
            activities.append({
                "username": log.username,
                "description": log.description,
                "time": time_ago(log.created_at)
            })
        
        return activities
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch recent activities: {str(e)}"
        )
