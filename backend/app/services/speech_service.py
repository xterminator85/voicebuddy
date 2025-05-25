import whisper
import os
import tempfile
import aiofiles
from typing import Optional


class SpeechService:
    def __init__(self):
        model_name = os.getenv("WHISPER_MODEL", "base")
        self.model = whisper.load_model(model_name)

    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio bytes to text using Whisper"""
        try:
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name

            # Transcribe using Whisper
            result = self.model.transcribe(temp_path)

            # Clean up temp file
            os.unlink(temp_path)

            return result["text"].strip()

        except Exception as e:
            print(f"Speech transcription error: {e}")
            return None

    async def transcribe_audio_file(self, file_path: str) -> Optional[str]:
        """Transcribe audio file to text"""
        try:
            result = self.model.transcribe(file_path)
            return result["text"].strip()
        except Exception as e:
            print(f"Speech transcription error: {e}")
            return None