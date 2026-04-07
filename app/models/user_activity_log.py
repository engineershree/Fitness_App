from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.sql import func
from app.core.database import Base


class UserActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True, comment="Foreign key, nullable for system events")
    username = Column(String(100), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, comment="Whether notification has been read by admin")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp stored in UTC internally"
    )

    # Add indexes for performance optimization
    __table_args__ = (
        Index('idx_activity_logs_created_at', 'created_at'),
        Index('idx_activity_logs_user_created', 'user_id', 'created_at'),
        Index('idx_activity_logs_is_read_created', 'is_read', 'created_at'),
        Index('idx_activity_logs_type_read_created', 'activity_type', 'is_read', 'created_at'),
    )
