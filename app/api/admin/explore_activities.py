from fastapi import Depends, Query, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from math import ceil
from datetime import datetime
import os

from app.models.explore_activity import ExploreActivity
from app.models.admin import Admin
from app.core.database import get_db
from app.services.explore_activity_media_service import ExploreActivityMediaService
from .dependencies import get_current_admin
from .schemas import (
    ExploreActivityResponse, ExploreActivityCreate, ExploreActivityUpdate, PaginatedResponse, PaginationInfo
)

# Initialize media service
media_service = ExploreActivityMediaService()

async def create_explore_activity(
        activity_name: str = Form(...),
        description: str = Form(...),
        duration: str = Form(...),
        activity_type: str = Form(...),
        image: Optional[UploadFile] = File(None),
        video: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        current_admin: Admin = Depends(get_current_admin)
):
    
    # Validate activity_type
    valid_activity_types = ["meditation", "yoga", "cycling", "treadmill", "outdoor", "mindful_cooldown"]
    if activity_type not in valid_activity_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"activity_type must be one of: {', '.join(valid_activity_types)}"
        )

    # Create new activity
    db_activity = ExploreActivity(
        activity_name=activity_name,
        description=description,
        duration=duration,
        activity_type=activity_type
    )
    
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    
    # Upload media if provided
    if image or video:
        try:
            image_url, video_url = await media_service.save_activity_media(
                image_file=image,
                video_file=video,
                activity_id=db_activity.id,
                activity_name=activity_name
            )
            
            # Update activity with media URLs
            if image_url:
                db_activity.image = image_url
            if video_url:
                db_activity.video = video_url
                
            db.commit()
            db.refresh(db_activity)
            
        except Exception as e:
            # If media upload fails, delete the activity and raise exception
            db.delete(db_activity)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload media: {str(e)}"
            )
    
    return db_activity

def get_explore_activities_paginated(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    activity_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    # Build query
    query = db.query(ExploreActivity)
    
    # Filter by activity_type if provided
    if activity_type:
        valid_activity_types = ["meditation", "yoga", "cycling", "treadmill", "outdoor", "mindful_cooldown"]
        if activity_type not in valid_activity_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"activity_type must be one of: {', '.join(valid_activity_types)}"
            )
        query = query.filter(ExploreActivity.activity_type == activity_type)
    
    # Search functionality
    if search:
        query = query.filter(
            or_(
                ExploreActivity.activity_name.ilike(f"%{search}%"),
                ExploreActivity.description.ilike(f"%{search}%")
            )
        )
    
    # Order by latest first
    query = query.order_by(ExploreActivity.created_at.desc())
    
    # Count total records
    total = query.count()
    
    # Calculate pagination
    offset = (page - 1) * limit
    total_pages = ceil(total / limit)
    
    # Get paginated results
    activities = query.offset(offset).limit(limit).all()
    
    # Convert SQLAlchemy models to Pydantic schemas
    activity_responses = [ExploreActivityResponse.from_orm(activity) for activity in activities]
    
    return {
        "data": activity_responses,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

def get_explore_activity_by_id(
    activity_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    activity = db.query(ExploreActivity).filter(ExploreActivity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Explore activity not found"
        )
    
    return ExploreActivityResponse.from_orm(activity)

async def update_explore_activity(
    activity_id: int,
    activity_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    duration: Optional[str] = Form(None),
    activity_type: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    
    # Get existing activity
    db_activity = db.query(ExploreActivity).filter(ExploreActivity.id == activity_id).first()
    
    if not db_activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Explore activity not found"
        )
    
    # Validate activity_type if provided
    if activity_type:
        valid_activity_types = ["meditation", "yoga", "cycling", "treadmill", "outdoor", "mindful_cooldown"]
        if activity_type not in valid_activity_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"activity_type must be one of: {', '.join(valid_activity_types)}"
            )
        db_activity.activity_type = activity_type
    
    # Update text fields if provided
    if activity_name:
        db_activity.activity_name = activity_name
    if description:
        db_activity.description = description
    if duration:
        db_activity.duration = duration
    
    # Handle media uploads
    old_image_url = db_activity.image
    old_video_url = db_activity.video
    
    if image or video:
        try:
            # Upload new media
            new_activity_name = activity_name if activity_name else db_activity.activity_name
            image_url, video_url = await media_service.save_activity_media(
                image_file=image,
                video_file=video,
                activity_id=activity_id,
                activity_name=new_activity_name
            )
            
            # Update activity with new media URLs
            if image_url:
                db_activity.image = image_url
            if video_url:
                db_activity.video = video_url
            
            # Delete old media from Cloudinary
            media_service.delete_old_activity_media(
                old_image_url if image_url else None,
                old_video_url if video_url else None
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload media: {str(e)}"
            )
    
    # Update timestamp
    db_activity.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_activity)
    
    return ExploreActivityResponse.from_orm(db_activity)

def delete_explore_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    
    # Get existing activity
    db_activity = db.query(ExploreActivity).filter(ExploreActivity.id == activity_id).first()
    
    if not db_activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Explore activity not found"
        )
    
    # Delete media from Cloudinary
    media_service.delete_old_activity_media(db_activity.image, db_activity.video)
    
    # Delete activity from database
    db.delete(db_activity)
    db.commit()
    
    return {"message": "Explore activity deleted successfully"}
