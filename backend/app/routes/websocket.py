from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from backend.app.services.conversation_service import ConversationService
from backend.app.database import get_db
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_text(json.dumps(message))


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, session_id: str, db: Session = Depends(get_db)):
    await manager.connect(websocket, session_id)
    conversation_service = ConversationService()

    # Get or create conversation
    conversation = conversation_service.get_conversation(db, session_id)
    if not conversation:
        conversation = conversation_service.create_conversation(db, f"Session {session_id[:8]}")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data["type"] == "text_message":
                # Process text message
                result = await conversation_service.process_text_message(
                    db, conversation.id, message_data["content"]
                )

                # Send response back
                await manager.send_message(session_id, {
                    "type": "ai_response",
                    "transcript": result["user_text"],
                    "ai_response": result["ai_response"],
                    "timestamp": str(datetime.utcnow())
                })

            elif message_data["type"] == "audio_data":
                # Handle audio data (base64 encoded)
                import base64
                audio_bytes = base64.b64decode(message_data["audio"])

                result, error = await conversation_service.process_audio_message(
                    db, conversation.id, audio_bytes
                )

                if error:
                    await manager.send_message(session_id, {
                        "type": "error",
                        "message": error
                    })
                else:
                    await manager.send_message(session_id, {
                        "type": "ai_response",
                        "transcript": result["transcript"],
                        "ai_response": result["ai_response"],
                        "timestamp": str(datetime.utcnow())
                    })

            elif message_data["type"] == "ping":
                await manager.send_message(session_id, {"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)