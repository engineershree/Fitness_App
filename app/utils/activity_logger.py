from sqlalchemy.orm import Session
from datetime import datetime, timezone
import pytz
from typing import Optional
from app.models.user_activity_log import UserActivityLog

# Define IST timezone
IST = pytz.timezone("Asia/Kolkata")


def log_activity(db: Session, user_id: Optional[int], username: str, activity_type: str, description: str) -> UserActivityLog:
    """
    Log user activity to the database.
    
    Args:
        db: Database session
        user_id: ID of the user performing the activity (nullable for system events)
        username: Username of the user
        activity_type: Type of activity (e.g., "signup", "profile_update", "subscription_purchase")
        description: Human-readable description (e.g., "Suraj signed up", "Suraj updated profile")
    
    Returns:
        UserActivityLog: The created activity log entry
    """
    activity_log = UserActivityLog(
        user_id=user_id,
        username=username,
        activity_type=activity_type,
        description=description,
        created_at=datetime.utcnow()  # Store UTC internally
    )
    
    db.add(activity_log)
    db.commit()
    db.refresh(activity_log)
    
    return activity_log


def time_ago(utc_time: Optional[datetime]) -> str:
    """
    Convert a UTC timestamp to a human-readable time difference in IST.
    
    Args:
        utc_time: UTC datetime from database
    
    Returns:
        str: Human-readable time difference (e.g., "just now", "2 min ago", "1 hr ago")
    """
    if not utc_time:
        return "Unknown time"
    
    try:
        # Ensure timestamp is timezone-aware (UTC)
        if utc_time.tzinfo is None:
            utc_time = utc_time.replace(tzinfo=timezone.utc)
        
        # Convert UTC to IST
        ist_time = utc_time.astimezone(IST)
        
        # Get current IST time
        now_ist = datetime.now(IST)
        
        # Calculate time difference
        time_diff = now_ist - ist_time
        seconds = int(time_diff.total_seconds())
        
        # Apply formatting rules
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} min ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hr ago"
        elif seconds < 604800:  # 7 days
            days = seconds // 86400
            return f"{days} days ago"
        else:
            # Return formatted date for older timestamps
            return ist_time.strftime("%d %b %Y, %I:%M %p")
            
    except Exception as e:
        # Fallback to formatted timestamp if there's any error
        try:
            if utc_time.tzinfo is None:
                utc_time = utc_time.replace(tzinfo=timezone.utc)
            ist_time = utc_time.astimezone(IST)
            return ist_time.strftime("%d %b %Y, %I:%M %p")
        except:
            return "Unknown time"
