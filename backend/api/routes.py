from fastapi import APIRouter
from sqlalchemy import text
from typing import Optional
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from database.connection import SessionLocal
from services.agents.master_agent import get_agent

router = APIRouter()

def format_records(records):
    output = []
    for r in records:
        eyebrows = "Neutral"
        # Safely handle None values from LEFT JOIN
        raise_val = r.eyebrow_raise if hasattr(r, 'eyebrow_raise') and r.eyebrow_raise is not None else 0
        lower_val = r.eyebrow_lower if hasattr(r, 'eyebrow_lower') and r.eyebrow_lower is not None else 0
        
        if raise_val > 0.5:
            eyebrows = "Raised"
        elif lower_val > 0.5:
            eyebrows = "Lowered"

        if r.mood == "Absent" or r.focus_score == 0:
            status = "User Not Found"
        else:
            status = "Attentive" if r.focus_score > 60 else "Distracted"

        output.append({
            "timestamp": r.timestamp.isoformat(),
            "focus_score": r.focus_score,
            "status": status,
            "is_tense": bool(r.is_tense) if hasattr(r, 'is_tense') else False,
            "mood": r.mood or "Neutral",
            "user_id": r.user_id,
            "eyebrows": eyebrows,
            "yawning": bool(r.yawning) if hasattr(r, 'yawning') else False,
            "lip_movement": bool(r.lip_movement) if hasattr(r, 'lip_movement') else False
        })
    return output

@router.get("/telemetry")
async def get_telemetry(session_id: str, user_id: Optional[str] = None):
    try:
        async with SessionLocal() as db:
            if user_id and user_id != "all":
                query = text("""
                    SELECT a.timestamp, a.attention_score as focus_score, a.user_id,
                           e.emotion as mood, f.smile_type,
                           f.is_tense, f.yawning, f.lip_movement,
                           f.eyebrow_raise, f.eyebrow_lower
                    FROM attention_timeline a
                    LEFT JOIN emotion_timeline e ON a.timestamp = e.timestamp AND a.session_id = e.session_id
                    LEFT JOIN facial_metrics f ON a.timestamp = f.timestamp AND a.session_id = f.session_id
                    WHERE a.user_id = :uid AND a.session_id = :session_id
                    ORDER BY a.timestamp DESC
                    LIMIT 100
                """)
                result = await db.execute(query, {"uid": user_id, "session_id": session_id})
            else:
                query = text("""
                    SELECT a.timestamp, a.attention_score as focus_score, a.user_id,
                           e.emotion as mood, f.smile_type,
                           f.is_tense, f.yawning, f.lip_movement,
                           f.eyebrow_raise, f.eyebrow_lower
                    FROM attention_timeline a
                    JOIN users u ON a.user_id = u.username
                    JOIN roles r ON u.role_id = r.id
                    LEFT JOIN emotion_timeline e ON a.timestamp = e.timestamp AND a.session_id = e.session_id
                    LEFT JOIN facial_metrics f ON a.timestamp = f.timestamp AND a.session_id = f.session_id
                    WHERE r.name = 'User' AND a.session_id = :session_id
                    ORDER BY a.timestamp DESC
                    LIMIT 200
                """)
                result = await db.execute(query, {"session_id": session_id})
                
            records = result.fetchall()
            return format_records(records)
    except Exception as e:
        print(f"Error fetching telemetry: {e}")
        return []

@router.get("/telemetry/latest")
async def get_latest_telemetry(session_id: str):
    try:
        async with SessionLocal() as db:
            query = text("""
                SELECT DISTINCT ON (a.user_id) 
                       a.timestamp, a.attention_score as focus_score, a.user_id,
                       e.emotion as mood, f.smile_type,
                       f.is_tense, f.yawning, f.lip_movement,
                       f.eyebrow_raise, f.eyebrow_lower
                FROM attention_timeline a
                JOIN users u ON a.user_id = u.username
                JOIN roles r ON u.role_id = r.id
                LEFT JOIN emotion_timeline e ON a.timestamp = e.timestamp AND a.session_id = e.session_id
                LEFT JOIN facial_metrics f ON a.timestamp = f.timestamp AND a.session_id = f.session_id
                WHERE r.name = 'User' AND a.session_id = :session_id
                ORDER BY a.user_id, a.timestamp DESC
            """)
            result = await db.execute(query, {"session_id": session_id})
            records = result.fetchall()
            return format_records(records)
    except Exception as e:
        print(f"Error fetching latest telemetry: {e}")
        return []

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: Optional[str] = None

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        agent = get_agent(req.session_id)
        context = f"[Context: Analyzing data for {'all users (Admin)' if not req.user_id or req.user_id == 'all' else f'user {req.user_id}'} in meeting room '{req.session_id}']. "
        messages = [HumanMessage(content=context + req.message)]
        
        result = await agent.ainvoke({"messages": messages})
        final_message = result["messages"][-1].content
        return {"response": final_message}
    except Exception as e:
        return {"response": f"AI Error: Make sure your GROQ_API_KEY is valid! Details: {str(e)}"}
