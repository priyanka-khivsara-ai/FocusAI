from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from database.connection import Base

# TimescaleDB requires the partitioning column (timestamp) to be part of the Primary Key
# We use a composite primary key: (timestamp, session_id)

class AttentionTimeline(Base):
    __tablename__ = "attention_timeline"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False, default="unknown")
    attention_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)

class EmotionTimeline(Base):
    __tablename__ = "emotion_timeline"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False, default="unknown")
    emotion = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)

class FacialMetrics(Base):
    __tablename__ = "facial_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False, default="unknown")
    ear = Column(Float, nullable=True)
    mar = Column(Float, nullable=True)
    blink_rate = Column(Float, nullable=True)
    smile_score = Column(Float, nullable=True)
    smile_type = Column(String, nullable=True)
    eyebrow_raise = Column(Float, nullable=True)
    eyebrow_lower = Column(Float, nullable=True)
    head_pitch = Column(Float, nullable=True)
    head_roll = Column(Float, nullable=True)
    head_yaw = Column(Float, nullable=True)
    gaze_x = Column(Float, nullable=True)
    gaze_y = Column(Float, nullable=True)
    is_tense = Column(Boolean, default=False)
    yawning = Column(Boolean, default=False)
    lip_movement = Column(Boolean, default=False)

class BodyMetrics(Base):
    __tablename__ = "body_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False, default="unknown")
    shoulder_angle = Column(Float, nullable=True)
    head_position = Column(String, nullable=True)
    hand_position = Column(String, nullable=True)
    posture = Column(String, nullable=True)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False, default="unknown")
    event_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    duration = Column(Float, nullable=True)
    metadata_info = Column(JSON, nullable=True)

class WarningRecord(Base):
    __tablename__ = "warnings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False, default="unknown")
    warning_type = Column(String, nullable=False)
    reason = Column(String, nullable=True)

class LivenessCheck(Base):
    __tablename__ = "liveness_checks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False, default="unknown")
    challenge = Column(String, nullable=False)
    result = Column(String, nullable=False)
    latency = Column(Float, nullable=True)
