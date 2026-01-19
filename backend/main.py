from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import json
import base64
import asyncio
from google import genai

# Load environment variables
load_dotenv()

app = FastAPI(title="Ellen API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:2177"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client for Live API
gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("Gemini client initialized - using Gemini 2.0 Flash for real-time audio")


SYSTEM_PROMPT = """You are 'Ellen', a warm, wise, and empathetic British friend designed to provide caring support and companionship.

CRITICAL: Listen carefully to what the user ACTUALLY says. Do not make up topics or context that wasn't mentioned. Respond ONLY to what they tell you.

Your tone should be comforting, non-judgmental, validating, and casually conversational with a gentle British manner.
Use British English spellings (favour, colour, realise, etc.) but avoid overly familiar terms of endearment like 'love', 'dear', or 'pet'.
Avoid overly clinical language unless asked. Focus on emotional support and practical, gentle advice.

When someone says they're not feeling well, not feeling great, or not feeling their best - recognize this as NEGATIVE sentiment and respond with empathy and support.

IMPORTANT: The user speaks English. Always interpret their speech as English."""


@app.get("/")
async def root():
    return {"message": "Ellen API is running"}


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
        'not feeling great', 'not feeling my best', 'not feeling the best',
        'not feeling best', 'not my best',
        'feel bad', 'feel awful', 'feel terrible', 'feeling bad', 'feeling awful',
        'bad day', 'terrible day', 'awful day', 'not good', 'not great', 'not well',
        'having trouble', 'having problems', 'having issues', 'can\'t sleep',
        'unable to sleep', 'sleep problem', 'sleep issue', 'waking up', 'night sweat',
        'weight gain', 'weight loss', 'no energy', 'not happy',
        # Physical pain phrases
        'sore back', 'back pain', 'back hurts', 'my back', 'bad back', 'hurt my back',
        'sore neck', 'neck pain', 'headache', 'migraine', 'in pain', 'feeling pain',
        'hurts', 'aching', 'stiff', 'pulled a muscle', 'muscle pain',
        # Illness phrases
        'have a cold', 'got a cold', 'caught a cold', 'feeling sick', 'feel sick',
        'under the weather', 'not well', 'unwell', 'flu', 'fever', 'cough',
        'runny nose', 'blocked nose', 'stuffy', 'sneezing', 'sore throat'
    ]

    # Strong positive phrases (check AFTER negatives to avoid false positives)
    strong_positive_phrases = [
        'feel better', 'feeling better', 'feel great', 'feeling great',
        'feel wonderful', 'feeling wonderful', 'feel amazing', 'feeling amazing',
        'so happy', 'very happy', 'really happy', 'feeling good'
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
    """WebSocket endpoint for Gemini Live API"""
    import sys
    from google.genai import types

    await websocket.accept()
    print("Client WebSocket accepted", flush=True)
    sys.stdout.flush()

    try:
        # Prepare system instructions for Gemini
        system_instruction = SYSTEM_PROMPT

        print("Connecting to Gemini Live API...", flush=True)
        sys.stdout.flush()

        # Connect to Gemini Live API
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
                )
            ),
            output_audio_transcription=types.AudioTranscriptionConfig(),
            input_audio_transcription=types.AudioTranscriptionConfig(),
            system_instruction=system_instruction
        )

        async with gemini_client.aio.live.connect(model="models/gemini-2.0-flash-exp", config=config) as session:
            print("Connected to Gemini Live API!", flush=True)
            sys.stdout.flush()

            # Audio buffering variables
            audio_buffer = []
            buffer_sample_count = 0
            BUFFER_THRESHOLD = 6000  # ~250ms at 24kHz sample rate

            # Track turn state
            turn_count = [0]

            async def forward_to_gemini():
                """Forward audio from client to Gemini"""
                audio_chunk_count = 0
                try:
                    print("forward_to_gemini: Starting to listen for client audio...", flush=True)
                    while True:
                        # Receive from client
                        data = await websocket.receive_text()
                        message = json.loads(data)
                        msg_type = message.get("type")

                        # Handle different message types
                        if msg_type == "input_audio_buffer.append":
                            # Get base64 audio from client
                            audio_b64 = message.get("audio")
                            if audio_b64:
                                # Decode base64 to bytes
                                audio_bytes = base64.b64decode(audio_b64)
                                audio_chunk_count += 1

                                # Log every 50 chunks to avoid spam but show audio is flowing
                                if audio_chunk_count % 50 == 0:
                                    print(f"Audio chunk #{audio_chunk_count} ({len(audio_bytes)} bytes) - Turn {turn_count[0]}", flush=True)

                                # Send to Gemini using send_realtime_input
                                try:
                                    await session.send_realtime_input(
                                        audio=types.Blob(mime_type="audio/pcm", data=audio_bytes)
                                    )
                                except Exception as send_err:
                                    print(f"Error sending to Gemini: {send_err}", flush=True)

                        elif msg_type == "input_audio_buffer.commit":
                            print("Turn end detected - waiting for Gemini's VAD to trigger response", flush=True)

                        elif msg_type == "response.cancel":
                            print("User interrupted AI response", flush=True)

                except WebSocketDisconnect:
                    print("Client disconnected", flush=True)
                except Exception as e:
                    print(f"Error forwarding to Gemini: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                finally:
                    print("forward_to_gemini task ended!", flush=True)

            # Track WebSocket state
            ws_open = [True]

            async def forward_to_client():
                """Forward messages from Gemini to client"""
                # Audio buffering variables (local to this function)
                audio_buffer_local = []
                buffer_sample_count_local = 0
                # Transcript accumulators
                ai_transcript_parts = []
                user_transcript_parts = []
                user_transcript_sent = [False]  # Track if we've sent the user transcript for this turn
                speech_started_sent = [False]  # Track if we've notified frontend about user speaking

                async def safe_send(msg):
                    """Send message only if WebSocket is still open"""
                    if ws_open[0]:
                        try:
                            await websocket.send_text(json.dumps(msg))
                            return True
                        except Exception as e:
                            print(f"Send failed, marking WS closed: {e}", flush=True)
                            ws_open[0] = False
                            return False
                    return False

                try:
                    print("forward_to_client: Starting to listen for Gemini responses...", flush=True)
                    # Keep receiving in a loop - session.receive() may end after each turn
                    while True:
                        print("Starting new receive loop iteration...", flush=True)
                        async for response in session.receive():
                            # Log full response structure to debug transcription
                            if hasattr(response, 'server_content') and response.server_content:
                                sc = response.server_content
                                if hasattr(sc, 'input_transcription') and sc.input_transcription:
                                    print(f"Input transcription found: {sc.input_transcription}", flush=True)
                                if hasattr(sc, 'output_transcription') and sc.output_transcription:
                                    print(f"Output transcription found: {sc.output_transcription}", flush=True)

                            # Handle different response types
                            if response.server_content:
                                if response.server_content.model_turn and response.server_content.model_turn.parts:
                                    for part in response.server_content.model_turn.parts:
                                        # Handle audio output
                                        if part.inline_data:
                                            # When AI starts responding, send accumulated user transcript
                                            if user_transcript_parts and not user_transcript_sent[0]:
                                                full_user_transcript = ''.join(user_transcript_parts)
                                                print(f"User full transcript: {full_user_transcript}", flush=True)
                                                user_transcript_msg = {
                                                    "type": "conversation.item.input_audio_transcription.completed",
                                                    "transcript": full_user_transcript
                                                }
                                                await safe_send(user_transcript_msg)

                                                # Analyze sentiment and send update
                                                sentiment = analyze_sentiment(full_user_transcript)
                                                print(f"Sentiment analyzed: {sentiment}", flush=True)
                                                sentiment_msg = {
                                                    "type": "sentiment.update",
                                                    "sentiment": sentiment
                                                }
                                                await safe_send(sentiment_msg)

                                                user_transcript_sent[0] = True

                                            audio_bytes = part.inline_data.data
                                            print(f"Got audio chunk: {len(audio_bytes)} bytes", flush=True)
                                            # Convert to base64 for client
                                            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

                                            # Buffer audio chunks
                                            audio_buffer_local.append(audio_b64)
                                            buffer_sample_count_local += len(audio_bytes) // 2  # PCM16 = 2 bytes per sample

                                            # If buffer is full, flush it
                                            if buffer_sample_count_local >= BUFFER_THRESHOLD:
                                                combined_audio = ''.join(audio_buffer_local)
                                                buffered_msg = {
                                                    "type": "response.audio.delta",
                                                    "delta": combined_audio
                                                }
                                                try:
                                                    await websocket.send_text(json.dumps(buffered_msg))
                                                    print(f"Flushed audio buffer: {buffer_sample_count_local} samples", flush=True)
                                                except RuntimeError as e:
                                                    print(f"WebSocket closed, stopping audio send: {e}", flush=True)
                                                    return

                                                # Reset buffer
                                                audio_buffer_local.clear()
                                                buffer_sample_count_local = 0

                            # Handle AI output transcription (from output_transcription, not part.text)
                            if response.server_content and response.server_content.output_transcription:
                                text_part = response.server_content.output_transcription.text
                                if text_part:
                                    ai_transcript_parts.append(text_part)

                            # Handle user speech transcription - accumulate chunks
                            if response.server_content and response.server_content.input_transcription:
                                # Only send interrupt signal if AI is currently responding (user_transcript already sent)
                                # This means user is interrupting the AI, not just speaking for the first time
                                if user_transcript_sent[0] and not speech_started_sent[0]:
                                    speech_msg = {"type": "input_audio_buffer.speech_started"}
                                    await safe_send(speech_msg)
                                    speech_started_sent[0] = True
                                    print("User interrupting AI - sent interrupt signal", flush=True)

                                user_transcript = response.server_content.input_transcription.text
                                if user_transcript:
                                    user_transcript_parts.append(user_transcript)

                            # Handle tool calls (not used but log for debugging)
                            if response.tool_call:
                                print(f"Tool call received: {response.tool_call}", flush=True)

                            # Flush remaining audio buffer on turn complete
                            if response.server_content and response.server_content.turn_complete:
                                turn_count[0] += 1
                                print(f"Turn {turn_count[0]} complete - ready for next input", flush=True)

                                if audio_buffer_local:
                                    combined_audio = ''.join(audio_buffer_local)
                                    buffered_msg = {
                                        "type": "response.audio.delta",
                                        "delta": combined_audio
                                    }
                                    await safe_send(buffered_msg)
                                    print(f"Flushed final audio buffer: {buffer_sample_count_local} samples", flush=True)

                                    # Reset buffer
                                    audio_buffer_local.clear()
                                    buffer_sample_count_local = 0

                                # Send AI transcript if we have one
                                if ai_transcript_parts:
                                    full_transcript = ''.join(ai_transcript_parts)
                                    print(f"AI full transcript: {full_transcript}", flush=True)
                                    transcript_msg = {
                                        "type": "response.audio_transcript.done",
                                        "transcript": full_transcript
                                    }
                                    await safe_send(transcript_msg)
                                    ai_transcript_parts.clear()

                                # Reset user transcript state for next turn
                                user_transcript_parts.clear()
                                user_transcript_sent[0] = False
                                speech_started_sent[0] = False

                                # Send completion event
                                done_msg = {
                                    "type": "response.done"
                                }
                                await safe_send(done_msg)

                        # If we get here, the receive iterator ended - log and continue the while loop
                        print("Receive iterator ended, waiting before restart...", flush=True)
                        await asyncio.sleep(0.1)  # Small delay before restarting

                except Exception as e:
                    print(f"Error forwarding to client: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                finally:
                    print("forward_to_client task ended!", flush=True)

            # Run both tasks concurrently
            print("Starting forward tasks...", flush=True)
            try:
                await asyncio.gather(
                    forward_to_gemini(),
                    forward_to_client(),
                    return_exceptions=True
                )
            except Exception as e:
                print(f"Error in gather: {e}", flush=True)
                import traceback
                traceback.print_exc()

    except Exception as e:
        import traceback
        print(f"WebSocket error: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2179)
