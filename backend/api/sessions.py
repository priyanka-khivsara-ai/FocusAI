import random
import string
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from database.connection import get_db
from models.relational import Session
from datetime import datetime

router = APIRouter()

def generate_meeting_code():
    # Generates a code like "AI-492" or "MEET-928"
    prefix = random.choice(["AI", "MEET", "CLASS", "ROOM"])
    suffix = "".join(random.choices(string.digits, k=3))
    return f"{prefix}-{suffix}"

@router.post("/create")
async def create_session(db: AsyncSession = Depends(get_db)):
    try:
        # Generate a unique code
        code = generate_meeting_code()
        
        # Ensure it doesn't already exist
        result = await db.execute(select(Session).where(Session.id == code))
        while result.scalar_one_or_none() is not None:
            code = generate_meeting_code()
            result = await db.execute(select(Session).where(Session.id == code))
        
        new_session = Session(
            id=code,
            status="active"
        )
        db.add(new_session)
        await db.commit()
        
        return {"session_id": code, "message": "Meeting created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_sessions(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Session).where(Session.status == "active").order_by(Session.start_time.desc())
        )
        sessions = result.scalars().all()
        return [{"session_id": s.id, "start_time": s.start_time} for s in sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
