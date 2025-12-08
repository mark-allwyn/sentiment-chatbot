from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import base64
from faster_whisper import WhisperModel
import edge_tts
import tempfile

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

# Initialize Faster-Whisper model (use tiny model for speed)
import subprocess
import time

whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
print("Whisper model loaded: tiny model on CPU (int8) - optimized for speed")

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
        # Step 1: Transcribe audio to text using Faster-Whisper (local)
        start_time = time.time()
        audio_content = await audio.read()
        print(f"Received audio: {len(audio_content)} bytes")

        # Save audio to temporary file for Faster-Whisper processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(audio_content)
            temp_audio_path = temp_audio.name

        print(f"Temp audio file: {temp_audio_path}")

        # Convert webm to wav using ffmpeg for better compatibility with Faster-Whisper
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            temp_wav_path = temp_wav.name

        try:
            # Convert webm to wav using ffmpeg
            try:
                ffmpeg_start = time.time()
                convert_result = subprocess.run(
                    ["ffmpeg", "-i", temp_audio_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", temp_wav_path, "-y"],
                    capture_output=True,
                    check=True
                )
                print(f"Audio converted to WAV: {temp_wav_path} (took {time.time() - ffmpeg_start:.2f}s)")
            except subprocess.CalledProcessError as e:
                print(f"FFmpeg conversion failed: {e}")
                print(f"FFmpeg stderr: {e.stderr.decode() if e.stderr else 'No stderr'}")
                raise ValueError(f"Failed to convert audio file: {e}")

            # Transcribe with Faster-Whisper using the WAV file
            transcribe_start = time.time()
            segments, info = whisper_model.transcribe(
                temp_wav_path,
                language="en",
                beam_size=1,  # Faster with minimal quality loss
                vad_filter=True  # Remove silence
            )
            user_text = " ".join([segment.text for segment in segments]).strip()
            print(f"Transcription (Faster-Whisper): '{user_text}' (took {time.time() - transcribe_start:.2f}s)")

            # If transcription is empty, return an error
            if not user_text:
                raise ValueError("No speech detected in audio")
        finally:
            # Clean up temp files
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            if os.path.exists(temp_wav_path):
                os.unlink(temp_wav_path)

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
        gpt_start = time.time()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversations[session_id],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        print(f"GPT-4o-mini response (took {time.time() - gpt_start:.2f}s)")

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

        # Step 7: Generate voice response using Edge-TTS (local, fast)
        # Edge-TTS voices: en-US-AvaNeural (female, professional), en-US-JennyNeural (friendly female)
        edge_voice = "en-US-AvaNeural"  # High-quality female voice

        # Generate speech with Edge-TTS
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_tts:
            temp_tts_path = temp_tts.name

        try:
            # Edge-TTS is async, so we need to run it in the event loop
            tts_start = time.time()
            communicate = edge_tts.Communicate(reply_text, edge_voice)
            await communicate.save(temp_tts_path)

            # Read the generated audio file
            with open(temp_tts_path, "rb") as audio_file:
                audio_bytes = audio_file.read()

            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            print(f"TTS generated: {len(audio_bytes)} bytes (took {time.time() - tts_start:.2f}s)")
            print(f"Total voice chat time: {time.time() - start_time:.2f}s")
        finally:
            # Clean up temp file
            os.unlink(temp_tts_path)

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
