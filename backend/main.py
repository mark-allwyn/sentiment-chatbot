from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import base64
import tempfile
import asyncio
import websockets

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

print("OpenAI client initialized - using gpt-4o-mini-transcribe-2025-12-15 for transcription, gpt-4o-mini for chat, and tts-1 for speech")

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


class QuickVoiceResponse(BaseModel):
    reply: str
    userSentiment: str
    transcription: str


class VoiceConfig(BaseModel):
    voice: str  # OpenAI voices: "alloy", "echo", "fable", "onyx", "nova", "shimmer"
    session_id: str = "default"


SYSTEM_PROMPT = """You are 'Scyla', a warm, wise, and empathetic British female friend designed to support women going through menopause.
Your tone should be comforting, non-judgmental, validating, and casually conversational with a gentle British manner.
Use British English spellings (favour, colour, realise, etc.) but avoid overly familiar terms of endearment like 'love', 'dear', or 'pet'.
Avoid overly clinical language unless asked. Focus on emotional support and practical, gentle advice.

You have a secondary task: Analyse the user's input to determine their sentiment.
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

        # Call OpenAI API (using gpt-4o-mini for better quality and speed)
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
        import time
        import subprocess

        # Step 1: Transcribe audio to text using OpenAI gpt-4o-mini-transcribe
        start_time = time.time()
        audio_content = await audio.read()
        print(f"Received audio: {len(audio_content)} bytes")

        # Check if audio is too small (likely empty or corrupt)
        if len(audio_content) < 1000:
            raise ValueError("Audio file is too small - please record for at least 1 second")

        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(audio_content)
            temp_audio_path = temp_audio.name

        # Convert webm to mp3 for better OpenAI compatibility
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_mp3:
            temp_mp3_path = temp_mp3.name

        print(f"Temp audio file: {temp_audio_path}")

        try:
            # Convert webm to mp3 using ffmpeg with faster settings
            try:
                convert_result = subprocess.run(
                    ["ffmpeg", "-i", temp_audio_path, "-ar", "16000", "-ac", "1", "-b:a", "32k", "-q:a", "9", temp_mp3_path, "-y"],
                    capture_output=True,
                    check=True
                )
                print(f"Audio converted to MP3: {temp_mp3_path}")
            except subprocess.CalledProcessError as e:
                print(f"FFmpeg conversion failed: {e}")
                raise ValueError(f"Failed to convert audio file: {e}")

            # Transcribe with OpenAI gpt-4o-mini-transcribe (90% fewer hallucinations)
            transcribe_start = time.time()
            with open(temp_mp3_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe-2025-12-15",
                    file=audio_file,
                    response_format="json"
                )
            user_text = transcription.text.strip()
            print(f"Transcription (gpt-4o-mini-transcribe): '{user_text}' (took {time.time() - transcribe_start:.2f}s)")

            # If transcription is empty, return an error
            if not user_text:
                raise ValueError("No speech detected in audio")
        finally:
            # Clean up temp files
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            if os.path.exists(temp_mp3_path):
                os.unlink(temp_mp3_path)

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

        # Step 4: Call OpenAI API for chat response (using gpt-4o-mini for better quality)
        gpt_start = time.time()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversations[session_id],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        print(f"gpt-4o-mini response (took {time.time() - gpt_start:.2f}s)")

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

        # Step 7: Generate voice response using OpenAI TTS
        # Get user's preferred voice (default: fable for British-leaning tone)
        preferred_voice = voice_preferences.get(session_id, "fable")

        # Generate speech with OpenAI TTS
        # Note: Using tts-1 (optimized for speed) with speed parameter for faster generation
        tts_start = time.time()
        response_audio = client.audio.speech.create(
            model="tts-1",
            voice=preferred_voice,
            input=reply_text,
            speed=1.1  # Slightly faster speech for quicker responses
        )

        # Get audio bytes
        audio_bytes = response_audio.content
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        print(f"TTS generated: {len(audio_bytes)} bytes (took {time.time() - tts_start:.2f}s)")
        print(f"Total voice chat time: {time.time() - start_time:.2f}s")

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
    # OpenAI TTS voices: alloy, echo, fable, onyx, nova, shimmer
    valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    if config.voice not in valid_voices:
        raise HTTPException(
            status_code=400,
            detail=f"Voice must be one of: {', '.join(valid_voices)}"
        )

    voice_preferences[config.session_id] = config.voice
    return {"message": f"Voice set to {config.voice}", "voice": config.voice}


@app.get("/api/voice-config/{session_id}")
async def get_voice_config(session_id: str = "default"):
    """Get voice preference for a session"""
    # Using 'fable' as default for British-leaning voice
    voice = voice_preferences.get(session_id, "fable")
    return {"voice": voice}


def analyze_sentiment(text: str) -> str:
    """Enhanced sentiment analysis based on keywords and phrases with negation handling"""
    text_lower = text.lower()

    # Positive keywords
    positive_words = [
        'happy', 'great', 'good', 'better', 'wonderful', 'excited', 'glad',
        'relieved', 'thankful', 'grateful', 'love', 'excellent', 'amazing',
        'fantastic', 'joy', 'pleased', 'delighted', 'blessed', 'fortunate',
        'perfect', 'brilliant', 'awesome', 'super', 'proud', 'hopeful'
    ]

    # Negative keywords - expanded significantly
    negative_words = [
        'sad', 'bad', 'worse', 'awful', 'terrible', 'angry', 'frustrated',
        'anxious', 'worried', 'pain', 'hurt', 'difficult', 'hard', 'struggling',
        'depressed', 'upset', 'problem', 'issue', 'trouble', 'concern', 'stress',
        'overwhelm', 'exhaust', 'tire', 'sick', 'ill', 'uncomfortable', 'scary',
        'fear', 'afraid', 'nervous', 'tense', 'irritable', 'annoyed', 'miserable',
        'hopeless', 'helpless', 'lonely', 'isolated', 'crying', 'tears', 'suffer',
        'ache', 'sore', 'insomnia', 'sleepless', 'fatigue', 'weary', 'drained',
        'nausea', 'dizzy', 'headache', 'migraine', 'cramp', 'sweat', 'hot flash',
        'mood swing', 'irritat', 'anger', 'rage', 'panic', 'attack', 'unable',
        'can\'t', 'cannot', 'won\'t', 'fail', 'loss', 'lost', 'gone', 'missing'
    ]

    # Negation words
    negations = ['not', 'no', 'never', 'don\'t', 'dont', 'doesn\'t', 'doesnt', 'didn\'t', 'didnt', 'isn\'t', 'isnt', 'aren\'t', 'arent']

    # Strong negative phrases (MUST CHECK FIRST - highest priority to catch negations)
    strong_negative_phrases = [
        'don\'t feel good', 'dont feel good', 'not feeling good', 'not feeling well',
        'don\'t feel well', 'dont feel well', 'not feel good', 'not feel well',
        'feel bad', 'feel awful', 'feel terrible', 'feeling bad', 'feeling awful',
        'bad day', 'terrible day', 'awful day', 'not good', 'not great', 'not well',
        'having trouble', 'having problems', 'having issues', 'can\'t sleep',
        'unable to sleep', 'sleep problem', 'sleep issue', 'waking up', 'night sweat',
        'weight gain', 'weight loss', 'no energy', 'not happy'
    ]

    # Strong positive phrases (check AFTER negatives to avoid false positives)
    strong_positive_phrases = [
        'feel better', 'feeling better', 'feel great', 'feeling great',
        'feel wonderful', 'feeling wonderful', 'feel amazing', 'feeling amazing',
        'so happy', 'very happy', 'really happy', 'feeling good'
        # NOTE: removed 'feel good' because it conflicts with "don't feel good"
    ]

    # Check for strong negative phrases FIRST (to catch negations like "don't feel good")
    for phrase in strong_negative_phrases:
        if phrase in text_lower:
            return "NEGATIVE"

    # Check for strong positive phrases AFTER negatives
    for phrase in strong_positive_phrases:
        if phrase in text_lower:
            return "POSITIVE"

    # Check for negations before positive words (e.g., "not happy", "don't feel good")
    for negation in negations:
        for positive_word in positive_words:
            if f"{negation} {positive_word}" in text_lower or f"{negation} feel {positive_word}" in text_lower:
                return "NEGATIVE"

    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    # Default to NEUTRAL for very short messages or greetings
    if len(text_lower.strip()) < 5 or text_lower.strip() in ['hi', 'hello', 'hey', 'yes', 'no', 'ok', 'okay']:
        return "NEUTRAL"

    if positive_count > negative_count:
        return "POSITIVE"
    elif negative_count > positive_count:
        return "NEGATIVE"
    else:
        return "NEUTRAL"


@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    """WebSocket endpoint for OpenAI Realtime API"""
    import sys
    await websocket.accept()
    print("Client WebSocket accepted", flush=True)
    sys.stdout.flush()

    openai_ws = None

    try:
        # Connect to OpenAI Realtime API
        openai_api_key = os.getenv("OPENAI_API_KEY")
        print(f"API Key present: {bool(openai_api_key)}", flush=True)
        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"

        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "OpenAI-Beta": "realtime=v1"
        }

        print("Connecting to OpenAI Realtime API...", flush=True)
        sys.stdout.flush()

        # Create SSL context with certifi's CA bundle
        import ssl
        import certifi
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        openai_ws = await websockets.connect(url, extra_headers=headers, ssl=ssl_context)
        print("Connected to OpenAI Realtime API!", flush=True)
        sys.stdout.flush()

        # Configure the session with British voice and system prompt
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "voice": "echo",  # Clear, neutral voice that speaks at a good pace
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,  # Lower threshold = more sensitive to quieter speech
                    "prefix_padding_ms": 500,  # More padding to capture start of speech
                    "silence_duration_ms": 800  # Respond a bit faster
                },
                "instructions": SYSTEM_PROMPT.replace("You MUST always return a JSON object with two fields:\n1. 'reply': Your supportive text response to the user.\n2. 'userSentiment': One of 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'.", "")
            }
        }

        await openai_ws.send(json.dumps(session_config))
        print("Session configured")

        # Create tasks to handle bidirectional communication
        async def forward_to_openai():
            """Forward messages from client to OpenAI"""
            try:
                while True:
                    # Receive from client
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    # Forward to OpenAI
                    await openai_ws.send(json.dumps(message))

            except WebSocketDisconnect:
                print("Client disconnected")
            except Exception as e:
                print(f"Error forwarding to OpenAI: {e}")

        async def forward_to_client():
            """Forward messages from OpenAI to client"""
            try:
                while True:
                    # Receive from OpenAI
                    message = await openai_ws.recv()

                    # Parse and analyze for sentiment
                    try:
                        msg_data = json.loads(message)
                        msg_type = msg_data.get("type")

                        # Log ALL event types for debugging
                        print(f"Event received: {msg_type}", flush=True)

                        # Log ERROR events with full details
                        if msg_type == "error":
                            print(f"ERROR from OpenAI Realtime API: {json.dumps(msg_data, indent=2)}", flush=True)

                        # Log conversation items for debugging with full data
                        if msg_type == "conversation.item.created":
                            print(f"Conversation item created: {json.dumps(msg_data, indent=2)[:1000]}", flush=True)

                        # Check for transcript completion event (user's transcribed speech)
                        if msg_type == "conversation.item.input_audio_transcription.completed":
                            print(f"Transcription completed event: {json.dumps(msg_data, indent=2)}", flush=True)
                            transcript = msg_data.get("transcript")
                            if transcript and isinstance(transcript, str):
                                transcript = transcript.strip()
                                if len(transcript) > 3:
                                    # Quick sentiment analysis
                                    sentiment = analyze_sentiment(transcript)
                                    print(f"User sentiment detected: {sentiment} for '{transcript}'", flush=True)

                                    # Send sentiment update to client
                                    sentiment_msg = {
                                        "type": "sentiment.update",
                                        "sentiment": sentiment
                                    }
                                    await websocket.send_text(json.dumps(sentiment_msg))

                        # Alternative: Check response.audio_transcript.done for AI's response transcript
                        if msg_type == "response.audio_transcript.done":
                            print(f"AI transcript done: {json.dumps(msg_data, indent=2)[:500]}", flush=True)

                    except Exception as e:
                        print(f"Error parsing sentiment: {e}", flush=True)

                    # Forward original message to client
                    await websocket.send_text(message)

            except websockets.exceptions.ConnectionClosed:
                print("OpenAI connection closed")
            except Exception as e:
                print(f"Error forwarding to client: {e}")

        # Run both tasks concurrently
        await asyncio.gather(
            forward_to_openai(),
            forward_to_client()
        )

    except Exception as e:
        import traceback
        print(f"WebSocket error: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        try:
            await websocket.close()
        except:
            pass
    finally:
        if openai_ws:
            try:
                await openai_ws.close()
            except:
                pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2179)
