from fastapi import FastAPI
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

# Include separated routers
app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(websocket_router)

@app.get("/")
async def root():
    return {"message": "FocusAI Backend is running securely."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
