import anthropic
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()


class AIService:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.conversation_context = []

    async def get_response(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """Get AI response for user input with conversation context"""
        try:
            # Build conversation context
            messages = []

            # Add system prompt for VoiceBuddy
            system_prompt = """You are VoiceBuddy, a real-time AI assistant designed to help users have realtime conversations. 

Your role:
- Provide quick, helpful responses to interview questions
- Offer coding hints and solutions for technical problems  
- Give conversation coaching and suggestions
- Be concise but thorough - users need fast, actionable advice
- Adapt your tone to be supportive and confident

Keep responses under 150 words for real-time use unless specifically asked for more detail."""

            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages for context
                    if msg['message_type'] == 'user_audio' or msg['message_type'] == 'user_text':
                        messages.append({"role": "user", "content": msg['content']})
                    elif msg['message_type'] == 'ai_response':
                        messages.append({"role": "assistant", "content": msg['content']})

            # Add current user input
            messages.append({"role": "user", "content": user_input})

            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=300,
                system=system_prompt,
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            print(f"AI Service Error: {e}")
            return "Sorry, I'm having trouble processing that right now. Could you try again?"

    async def get_interview_help(self, question: str, context: str = "") -> str:
        """Specialized method for interview assistance"""
        prompt = f"""
        Interview Question: {question}
        Context: {context}

        Please provide:
        1. A suggested answer framework
        2. Key points to mention
        3. What to avoid saying

        Keep it concise for real-time use.
        """

        return await self.get_response(prompt)

    async def get_coding_help(self, problem: str, language: str = "python") -> str:
        """Specialized method for coding assistance"""
        prompt = f"""
        Coding Problem: {problem}
        Language: {language}

        Please provide:
        1. Approach/algorithm hint
        2. Key concepts to consider
        3. Potential edge cases

        Don't give the full solution unless specifically asked.
        """

        return await self.get_response(prompt)