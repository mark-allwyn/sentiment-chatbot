from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import base64
from io import BytesIO

# Load environment variables
load_dotenv()

app = FastAPI(title="Scyla API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:2177"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Store conversation history per session (in production, use proper session management)
conversations = {}

# Store voice preferences per session
voice_preferences = {}


class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    userSentiment: str


class VoiceChatResponse(BaseModel):
    reply: str
    userSentiment: str
    transcription: str
    audioBase64: str


class VoiceConfig(BaseModel):
    voice: str  # "nova" or "shimmer"
    session_id: str = "default"


SYSTEM_PROMPT = """You are 'Scyla', a warm, wise, and empathetic female friend designed to support women going through menopause.
Your tone should be comforting, non-judgmental, validating, and casually conversational.
Avoid overly clinical language unless asked. Focus on emotional support and practical, gentle advice.

You have a secondary task: Analyze the user's input to determine their sentiment.
- If the user seems happy, relieved, excited, or grateful -> POSITIVE.
- If the user seems sad, frustrated, angry, anxious, or in pain -> NEGATIVE.
- If the user is just asking information, saying hello, or is matter-of-fact -> NEUTRAL.

You MUST always return a JSON object with two fields:
1. 'reply': Your supportive text response to the user.
2. 'userSentiment': One of 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'."""


@app.get("/")
async def root():
    return {"message": "Scyla API is running"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    try:
        # Get or create conversation history for this session
        if chat_message.session_id not in conversations:
            conversations[chat_message.session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]

        # Add user message to conversation
        conversations[chat_message.session_id].append({
            "role": "user",
            "content": chat_message.message
        })

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversations[chat_message.session_id],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        # Parse response
        assistant_message = response.choices[0].message.content
        response_data = json.loads(assistant_message)

        # Add assistant response to conversation history
        conversations[chat_message.session_id].append({
            "role": "assistant",
            "content": assistant_message
        })

        return ChatResponse(
            reply=response_data.get("reply", "I'm here for you."),
            userSentiment=response_data.get("userSentiment", "NEUTRAL")
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="I'm having a little trouble connecting right now, but I'm still here for you."
        )


@app.post("/api/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    session_id: str = Form("default")
):
    try:
        # Step 1: Transcribe audio to text using Whisper
        audio_content = await audio.read()
        audio_file = BytesIO(audio_content)
        audio_file.name = "recording.webm"

        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en",  # Specify language for faster processing
            response_format="text"  # Get plain text instead of verbose JSON
        )
        user_text = transcription if isinstance(transcription, str) else transcription.text

        # Step 2: Get or create conversation history for this session
        if session_id not in conversations:
            conversations[session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]

        # Step 3: Add user message to conversation
        conversations[session_id].append({
            "role": "user",
            "content": user_text
        })

        # Step 4: Call OpenAI API for chat response
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversations[session_id],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        # Step 5: Parse response
        assistant_message = response.choices[0].message.content
        response_data = json.loads(assistant_message)
        reply_text = response_data.get("reply", "I'm here for you.")
        sentiment = response_data.get("userSentiment", "NEUTRAL")

        # Step 6: Add assistant response to conversation history
        conversations[session_id].append({
            "role": "assistant",
            "content": assistant_message
        })

        # Step 7: Generate voice response using TTS
        # Get voice preference for this session (default to "nova")
        voice = voice_preferences.get(session_id, "nova")

        speech_response = client.audio.speech.create(
            model="tts-1",  # Using tts-1 (faster) instead of tts-1-hd
            voice=voice,
            input=reply_text,
            response_format="opus",  # Opus is more efficient than mp3
            speed=1.0  # Normal speed
        )

        # Step 8: Convert audio to base64 for JSON response
        audio_bytes = speech_response.content
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        return VoiceChatResponse(
            reply=reply_text,
            userSentiment=sentiment,
            transcription=user_text,
            audioBase64=audio_base64
        )

    except Exception as e:
        print(f"Voice chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="I'm having trouble with voice right now, but I'm still here for you."
        )


@app.post("/api/voice-config")
async def set_voice_config(config: VoiceConfig):
    """Set voice preference for a session"""
    if config.voice not in ["nova", "shimmer"]:
        raise HTTPException(status_code=400, detail="Voice must be 'nova' or 'shimmer'")

    voice_preferences[config.session_id] = config.voice
    return {"message": f"Voice set to {config.voice}", "voice": config.voice}


@app.get("/api/voice-config/{session_id}")
async def get_voice_config(session_id: str = "default"):
    """Get voice preference for a session"""
    voice = voice_preferences.get(session_id, "nova")
    return {"voice": voice}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2179)
