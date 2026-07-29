import os
from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from sqlalchemy import select
from database import SessionLocal
from models import TelemetryRecord

@tool
async def query_recent_telemetry(limit: int = 50) -> str:
    """
    Queries the TimescaleDB database for the most recent cognitive telemetry records.
    Returns a chronological list of the user's focus score, facial tension, and mood over time.
    """
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(TelemetryRecord).order_by(TelemetryRecord.timestamp.desc()).limit(limit)
            )
            records = result.scalars().all()
            
            if not records:
                return "No telemetry data found in the database."
            
            # Reverse to make it chronological (oldest to newest in the time window)
            output = []
            for r in reversed(records):
                time_str = r.timestamp.strftime("%H:%M:%S")
                output.append(f"[{time_str}] Focus Score: {r.focus_score}/100 | Mood: {r.mood} | Tense: {r.is_tense}")
            
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
