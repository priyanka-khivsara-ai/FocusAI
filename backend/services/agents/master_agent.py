import os
from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from sqlalchemy import text
from database.connection import SessionLocal

def get_agent(session_id: str):
    """
    Initializes the LangGraph ReAct agent.
    The agent acts as a data analyst capable of querying the TimescaleDB.
    Requires GROQ_API_KEY in the environment.
    """
    
    @tool
    async def query_recent_telemetry(user_id: str = "all", limit: int = 50) -> str:
        """
        Queries the TimescaleDB database for the most recent cognitive telemetry records.
        Returns a chronological list of focus scores and mood over time. 
        MAXIMUM LIMIT is 100. You cannot fetch more than 100 records at a time.
        """
        limit = min(limit, 100) # Cap limit to prevent Token Rate Limit errors
        try:
            async with SessionLocal() as db:
                if user_id == "all":
                    query = text("""
                        SELECT a.timestamp, a.attention_score as focus_score, a.user_id, e.emotion as mood
                        FROM attention_timeline a
                        LEFT JOIN emotion_timeline e ON a.timestamp = e.timestamp AND a.session_id = e.session_id
                        WHERE a.session_id = :session_id
                        ORDER BY a.timestamp DESC
                        LIMIT :limit
                    """)
                    result = await db.execute(query, {"limit": limit, "session_id": session_id})
                else:
                    query = text("""
                        SELECT a.timestamp, a.attention_score as focus_score, a.user_id, e.emotion as mood
                        FROM attention_timeline a
                        LEFT JOIN emotion_timeline e ON a.timestamp = e.timestamp AND a.session_id = e.session_id
                        WHERE a.user_id = :uid AND a.session_id = :session_id
                        ORDER BY a.timestamp DESC
                        LIMIT :limit
                    """)
                    result = await db.execute(query, {"uid": user_id, "limit": limit, "session_id": session_id})
                    
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

    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    tools = [query_recent_telemetry]
    
    system_prompt = (
        "You are an AI data analyst for FocusAI. You have access to ONLY ONE tool: `query_recent_telemetry`. "
        "DO NOT use or attempt to call any other tools such as `brave_search`. "
        "Answer the user's questions based ONLY on the data returned by your tool."
    )
    
    # create_react_agent builds a StateGraph under the hood
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    return agent
