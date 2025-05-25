from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.services.conversation_service import ConversationService
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/conversation", tags=["conversation"])


class TextMessageRequest(BaseModel):
    session_id: str
    message: str


class ConversationResponse(BaseModel):
    id: int
    session_id: str
    title: str
    created_at: str


@router.post("/create")
async def create_conversation(title: str = "New Conversation", db: Session = Depends(get_db)):
    """Create a new conversation"""
    service = ConversationService()
    conversation = service.create_conversation(db, title)
    return {
        "session_id": conversation.session_id,
        "title": conversation.title,
        "created_at": conversation.created_at
    }


@router.get("/{session_id}")
async def get_conversation(session_id: str, db: Session = Depends(get_db)):
    """Get conversation by session ID"""
    service = ConversationService()
    conversation = service.get_conversation(db, session_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get message history
    messages = service.get_conversation_history(db, conversation.id)

    return {
        "session_id": conversation.session_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "messages": [
            {
                "id": msg.id,
                "content": msg.content,
                "type": msg.message_type,
                "timestamp": msg.timestamp
            }
            for msg in reversed(messages)
        ]
    }


@router.post("/text-message")
async def send_text_message(request: TextMessageRequest, db: Session = Depends(get_db)):
    """Send a text message and get AI response"""
    service = ConversationService()

    # Get or create conversation
    conversation = service.get_conversation(db, request.session_id)
    if not conversation:
        conversation = service.create_conversation(db)

    # Process message
    result = await service.process_text_message(db, conversation.id, request.message)

    return {
        "transcript": result["user_text"],
        "ai_response": result["ai_response"]
    }


@router.post("/audio-upload")
async def upload_audio(session_id: str, audio: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload audio file for transcription and AI response"""
    service = ConversationService()

    # Get or create conversation
    conversation = service.get_conversation(db, session_id)
    if not conversation:
        conversation = service.create_conversation(db)

    # Read audio file
    audio_data = await audio.read()

    # Process audio
    result, error = await service.process_audio_message(db, conversation.id, audio_data)

    if error:
        raise HTTPException(status_code=500, detail=error)

    return {
        "transcript": result["transcript"],
        "ai_response": result["ai_response"]
    }