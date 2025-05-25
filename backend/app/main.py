from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.app.database import engine, get_db
from backend.app.models import Base
from backend.app.routes import conversation, websocket
import os
from dotenv import load_dotenv

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="VoiceBuddy API",
    description="Real-time AI conversation assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversation.router)

# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint_route(websocket: WebSocket, session_id: str, db: Session = Depends(get_db)):
    await websocket.websocket_endpoint(websocket, session_id, db)

@app.get("/")
async def root():
    return {"message": "VoiceBuddy API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "voicebuddy-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)