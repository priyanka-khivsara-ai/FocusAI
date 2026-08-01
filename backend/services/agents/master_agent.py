import os
from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from sqlalchemy import text
from database.connection import SessionLocal

@tool
async def query_recent_telemetry(user_id: str = "all", limit: int = 50) -> str:
    """
    Queries the TimescaleDB database for the most recent cognitive telemetry records.
    Returns a chronological list of focus scores and mood over time.
    """
    try:
        async with SessionLocal() as db:
            if user_id == "all":
                query = text("""
                    SELECT a.timestamp, a.attention_score as focus_score, a.user_id, e.emotion as mood
                    FROM attention_timeline a
                    LEFT JOIN emotion_timeline e ON a.timestamp = e.timestamp AND a.session_id = e.session_id
                    ORDER BY a.timestamp DESC
                    LIMIT :limit
                """)
                result = await db.execute(query, {"limit": limit})
            else:
                query = text("""
                    SELECT a.timestamp, a.attention_score as focus_score, a.user_id, e.emotion as mood
                    FROM attention_timeline a
                    LEFT JOIN emotion_timeline e ON a.timestamp = e.timestamp AND a.session_id = e.session_id
                    WHERE a.user_id = :uid
                    ORDER BY a.timestamp DESC
                    LIMIT :limit
                """)
                result = await db.execute(query, {"uid": user_id, "limit": limit})
                
            records = result.fetchall()
            
            if not records:
                return "No telemetry data found in the database."
            
            output = []
            for r in reversed(records):
                time_str = r.timestamp.strftime("%H:%M:%S")
                mood = r.mood or "Neutral"
                output.append(f"[{time_str}] User: {r.user_id} | Focus Score: {r.focus_score}/100 | Mood: {mood}")
            
            return "\n".join(output)
    except Exception as e:
        return f"Database error: {str(e)}"

def get_agent():
    """
    Initializes the LangGraph ReAct agent.
    The agent acts as a data analyst capable of querying the TimescaleDB.
    Requires GROQ_API_KEY in the environment.
    """
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    tools = [query_recent_telemetry]
    
    # create_react_agent builds a StateGraph under the hood
    agent = create_react_agent(llm, tools)
    return agent
