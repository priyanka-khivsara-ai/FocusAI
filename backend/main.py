<<<<<<< HEAD
# main.py
# FastAPI backend for Attention Detection System
import pandas as pd
import io
import random
import string
from fastapi import FastAPI, WebSocket, UploadFile, File
import uvicorn
import numpy as np
import math
import os
import time
from database import SessionLocal
from models import TelemetryRecord, UserAccount
=======
from fastapi import FastAPI
>>>>>>> 1cb583fc3cdfc4721c967663c818fca4fc056c20
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.routes import router as api_router
from api.auth import router as auth_router
from websocket.stream import router as websocket_router

app = FastAPI(title="FocusAI Cognitive Telemetry Engine")

# Allow the Next.js frontend to make HTTP requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
@app.get("/api/telemetry")
async def get_telemetry(user_id: Optional[str] = None):
    try:
        async with SessionLocal() as db:
            if user_id and user_id != "all":
                # Return data for a specific user (Admin mode)
                result = await db.execute(
                    select(TelemetryRecord)
                    .where(TelemetryRecord.user_id == user_id)
                    .order_by(TelemetryRecord.timestamp.desc())
                    .limit(100)
                )
            else:
                # Return data for all users (Super Admin mode)
                result = await db.execute(
                    select(TelemetryRecord)
                    .order_by(TelemetryRecord.timestamp.desc())
                    .limit(200)
                )
                
            records = result.scalars().all()
            
            output = []
            for r in records:
                output.append({
                    "timestamp": r.timestamp.isoformat(),
                    "focus_score": r.focus_score,
                    "status": r.status,
                    "is_tense": r.is_tense,
                    "mood": r.mood,
                    "user_id": r.user_id,
                    "eyebrows": r.eyebrows,
                    "yawning": r.yawning,
                    "lip_movement": r.lip_movement
                })
            return output
    except Exception as e:
        print(f"Error fetching telemetry: {e}")
        return []

@app.get("/api/telemetry/latest")
async def get_latest_telemetry():
    try:
        async with SessionLocal() as db:
            # Query the single most recent record for each distinct user_id
            result = await db.execute(
                select(TelemetryRecord)
                .distinct(TelemetryRecord.user_id)
                .order_by(TelemetryRecord.user_id, TelemetryRecord.timestamp.desc())
            )
            records = result.scalars().all()
            
            output = []
            for r in records:
                output.append({
                    "timestamp": r.timestamp.isoformat(),
                    "focus_score": r.focus_score,
                    "status": r.status,
                    "is_tense": r.is_tense,
                    "mood": r.mood,
                    "user_id": r.user_id,
                    "eyebrows": r.eyebrows,
                    "yawning": r.yawning,
                    "lip_movement": r.lip_movement
                })
            return output
    except Exception as e:
        print(f"Error fetching latest telemetry: {e}")
        return []

class LoginRequest(BaseModel):
    user_id: str
    password: str
    role: str

@app.post("/api/login")
async def login(req: LoginRequest):
    try:
        async with SessionLocal() as db:
            result = await db.execute(select(UserAccount).where(UserAccount.user_id == req.user_id, UserAccount.password == req.password, UserAccount.role == req.role))
            account = result.scalars().first()
            if account:
                return {"success": True, "message": "Login successful"}
            else:
                return {"success": False, "message": "Invalid credentials"}
    except Exception as e:
        return {"success": False, "message": f"Database Error: {e}"}

@app.post("/api/upload-users")
async def upload_users(file: UploadFile = File(...)):
    try:
        content = await file.read()
        
        # Parse CSV or Excel
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(".xlsx") or file.filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            return {"success": False, "message": "Only CSV and Excel files are supported!"}
        
        if "name" not in df.columns:
            # Assume first column is name if not explicitly named
            df.rename(columns={df.columns[0]: "name"}, inplace=True)
            
        generated_accounts = []
        
        async with SessionLocal() as db:
            for index, row in df.iterrows():
                name = str(row["name"]).strip()
                if not name or name.lower() == "nan": continue
                
                # Create a simple user ID: firstname_lastname_random
                base_id = name.lower().replace(" ", "_")
                rand_suffix = ''.join(random.choices(string.digits, k=3))
                user_id = f"{base_id}_{rand_suffix}"
                
                # Generate random 8-char alphanumeric password
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                # Default role to User, unless specified in file
                role = "User"
                if "role" in df.columns:
                    role_val = str(row["role"]).strip().title()
                    if role_val in ["User", "Admin", "Super Admin"]:
                        role = role_val
                
                account = UserAccount(user_id=user_id, password=password, role=role)
                db.add(account)
                
                generated_accounts.append({
                    "name": name,
                    "user_id": user_id,
                    "password": password,
                    "role": role
                })
            
            await db.commit()
            
        return {"success": True, "accounts": generated_accounts}
    except Exception as e:
        return {"success": False, "message": f"Failed to process file: {e}"}

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        agent = get_agent()
        # Pass the user context into the AI prompt!
        context = f"[Context: Analyzing data for {'all users (Super Admin)' if not req.user_id or req.user_id == 'all' else f'user {req.user_id}'}]. "
        messages = [HumanMessage(content=context + req.message)]
        
        # Run the LangGraph state machine with the user's prompt
        result = await agent.ainvoke({"messages": messages})
        
        # The agent's final response is the last message in the state
        final_message = result["messages"][-1].content
        return {"response": final_message}
    except Exception as e:
        return {"response": f"AI Error: Make sure your GROQ_API_KEY is valid! Details: {str(e)}"}
=======
# Include separated routers
app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(websocket_router)
>>>>>>> 1cb583fc3cdfc4721c967663c818fca4fc056c20

@app.get("/")
async def root():
    return {"message": "FocusAI Backend is running securely."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
