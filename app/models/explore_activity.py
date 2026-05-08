from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.core.database import Base

class ExploreActivity(Base):
    __tablename__ = "explore_activities"

    id = Column(Integer, primary_key=True, index=True)
    activity_name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    image = Column(String, nullable=True)  # URL to uploaded image
    video = Column(String, nullable=True)  # URL to uploaded video
    duration = Column(String, nullable=False)  # Following project convention of String for duration
    activity_type = Column(String, nullable=False, index=True)  # Enum values: meditation, yoga, cycling, treadmill, outdoor, mindful_cooldown
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ExploreActivity(id={self.id}, activity_name={self.activity_name}, activity_type={self.activity_type})>"
