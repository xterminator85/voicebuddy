from sqlalchemy.orm import Session
from backend.app.models import Conversation, Message
from ai_service import AIService
from speech_service import SpeechService
from datetime import datetime
import uuid


class ConversationService:
    def __init__(self):
        self.ai_service = AIService()
        self.speech_service = SpeechService()

    def create_conversation(self, db: Session, title: str = "New Conversation") -> Conversation:
        """Create a new conversation session"""
        conversation = Conversation(
            session_id=str(uuid.uuid4()),
            title=title
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    def get_conversation(self, db: Session, session_id: str) -> Conversation:
        """Get conversation by session ID"""
        return db.query(Conversation).filter(Conversation.session_id == session_id).first()

    def add_message(self, db: Session, conversation_id: int, content: str,
                    message_type: str, audio_duration: int = None) -> Message:
        """Add a message to conversation"""
        message = Message(
            conversation_id=conversation_id,
            content=content,
            message_type=message_type,
            audio_duration=audio_duration
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def get_conversation_history(self, db: Session, conversation_id: int, limit: int = 50):
        """Get conversation message history"""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp.desc()).limit(limit).all()

    async def process_audio_message(self, db: Session, conversation_id: int, audio_data: bytes):
        """Process audio message: transcribe + get AI response"""
        # Transcribe audio
        transcript = await self.speech_service.transcribe_audio(audio_data)
        if not transcript:
            return None, "Failed to transcribe audio"

        # Save user audio message
        user_message = self.add_message(
            db, conversation_id, transcript, "user_audio"
        )

        # Get conversation history for context
        history = self.get_conversation_history(db, conversation_id, 10)
        history_data = [
            {
                "content": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.timestamp
            }
            for msg in reversed(history)
        ]

        # Get AI response
        ai_response = await self.ai_service.get_response(transcript, history_data)

        # Save AI response
        ai_message = self.add_message(
            db, conversation_id, ai_response, "ai_response"
        )

        return {
            "transcript": transcript,
            "ai_response": ai_response,
            "user_message_id": user_message.id,
            "ai_message_id": ai_message.id
        }, None

    async def process_text_message(self, db: Session, conversation_id: int, text: str):
        """Process text message: get AI response"""
        # Save user text message
        user_message = self.add_message(
            db, conversation_id, text, "user_text"
        )

        # Get conversation history for context
        history = self.get_conversation_history(db, conversation_id, 10)
        history_data = [
            {
                "content": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.timestamp
            }
            for msg in reversed(history)
        ]

        # Get AI response
        ai_response = await self.ai_service.get_response(text, history_data)

        # Save AI response
        ai_message = self.add_message(
            db, conversation_id, ai_response, "ai_response"
        )

        return {
            "user_text": text,
            "ai_response": ai_response,
            "user_message_id": user_message.id,
            "ai_message_id": ai_message.id
        }