from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class TelemetryRecord(Base):
    """
    Core ORM Model for storing high-frequency cognitive telemetry.
    This table will be converted into a TimescaleDB Hypertable partitioned by timestamp.
    """
    __tablename__ = "telemetry_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    # TimescaleDB requires the partitioning column (timestamp) to be part of the Primary Key!
    timestamp = Column(DateTime(timezone=True), primary_key=True, server_default=func.now(), nullable=False)
    
    # Session tracking
    session_id = Column(String, index=True, nullable=False, default="default_session")
    
    # Cognitive Metrics
    focus_score = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # e.g., 'Attentive', 'Distracted'
    mood = Column(String, nullable=False)    # e.g., 'Neutral', 'Genuine Smile'
    is_tense = Column(Boolean, default=False, nullable=False)
