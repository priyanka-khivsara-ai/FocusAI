from typing import Optional

from fastapi import APIRouter
from sqlalchemy import text

from database.connection import SessionLocal

router = APIRouter()


def _record(row):
    return {
        "timestamp": row.timestamp.isoformat(),
        "user_id": row.user_id,
        "score": row.presence_score,
        "status": row.presence_status,
        "confidence": row.confidence,
        "blink_count": row.blink_count,
        "facial_motion": row.facial_motion,
        "frozen_seconds": row.frozen_seconds,
        "replay_detected": row.replay_detected,
    }


@router.get("/latest")
async def latest_presence(session_id: str, user_id: Optional[str] = None):
    """Latest passive-presence state for one participant or each session participant."""
    try:
        async with SessionLocal() as db:
            if user_id and user_id != "all":
                result = await db.execute(text("""
                    SELECT timestamp, user_id, presence_score, presence_status, confidence,
                           blink_count, facial_motion, frozen_seconds, replay_detected
                    FROM presence_timeline
                    WHERE session_id = :session_id AND user_id = :user_id
                    ORDER BY timestamp DESC LIMIT 1
                """), {"session_id": session_id, "user_id": user_id})
                row = result.fetchone()
                return _record(row) if row else None
            result = await db.execute(text("""
                SELECT DISTINCT ON (user_id) timestamp, user_id, presence_score, presence_status,
                       confidence, blink_count, facial_motion, frozen_seconds, replay_detected
                FROM presence_timeline
                WHERE session_id = :session_id
                ORDER BY user_id, timestamp DESC
            """), {"session_id": session_id})
            return [_record(row) for row in result.fetchall()]
    except Exception as exc:
        print(f"Presence latest query failed: {exc}")
        return [] if not user_id or user_id == "all" else None


@router.get("/timeline")
async def presence_timeline(session_id: str, user_id: str, limit: int = 120):
    """Recent score series for the participant dashboard; bounded for inexpensive polling."""
    limit = min(max(limit, 1), 600)
    try:
        async with SessionLocal() as db:
            result = await db.execute(text("""
                SELECT timestamp, user_id, presence_score, presence_status, confidence,
                       blink_count, facial_motion, frozen_seconds, replay_detected
                FROM presence_timeline
                WHERE session_id = :session_id AND user_id = :user_id
                ORDER BY timestamp DESC LIMIT :limit
            """), {"session_id": session_id, "user_id": user_id, "limit": limit})
            return list(reversed([_record(row) for row in result.fetchall()]))
    except Exception as exc:
        print(f"Presence timeline query failed: {exc}")
        return []
