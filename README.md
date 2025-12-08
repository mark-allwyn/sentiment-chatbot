# Scyla - AI Companion for Menopause Support

A sentiment-aware AI companion web application with voice chat designed to support women navigating menopause. Built with Python FastAPI backend, React frontend, and AI models for intelligent conversations with real-time sentiment analysis.

## Features

- **Voice Chat**: Hold-to-talk microphone with local speech recognition and text-to-speech
- **Text Chat**: Traditional text-based conversation interface
- **Sentiment Analysis**: Real-time emotion detection (Positive, Negative, Neutral)
- **Adaptive Avatar**: Pulsating, color-changing visual indicator based on user sentiment
- **Audio Controls**: Stop speaking button and Escape key support
- **Conversational Memory**: Maintains conversation history per session
- **Empathetic Responses**: AI trained to provide supportive, non-judgmental guidance

## AI Models & Technologies

### Speech-to-Text (Voice Input)
- **Model**: Faster-Whisper "tiny" model
- **Provider**: Local inference (CPU with int8 quantization)
- **Purpose**: Transcribes user voice input to text
- **Performance**: ~1-2 seconds per transcription
- **Requirements**: FFmpeg for audio format conversion

### Chat & Sentiment Analysis
- **Model**: GPT-4o-mini
- **Provider**: OpenAI API
- **Purpose**: Generates empathetic responses and analyzes user sentiment
- **Performance**: ~2-3 seconds per response
- **Output Format**: JSON with `reply` and `userSentiment` fields

### Text-to-Speech (Voice Output)
- **Model**: Edge-TTS (en-US-AvaNeural)
- **Provider**: Microsoft Edge TTS (local, free)
- **Purpose**: Converts AI responses to natural-sounding speech
- **Performance**: ~1-2 seconds per generation
- **Voice**: Female, professional tone

## System Prompt

The AI assistant uses the following system prompt to guide its behavior:

```
You are 'Scyla', a warm, wise, and empathetic female friend designed to support women going through menopause.
Your tone should be comforting, non-judgmental, validating, and casually conversational.
Avoid overly clinical language unless asked. Focus on emotional support and practical, gentle advice.

You have a secondary task: Analyze the user's input to determine their sentiment.
- If the user seems happy, relieved, excited, or grateful -> POSITIVE.
- If the user seems sad, frustrated, angry, anxious, or in pain -> NEGATIVE.
- If the user is just asking information, saying hello, or is matter-of-fact -> NEUTRAL.

You MUST always return a JSON object with two fields:
1. 'reply': Your supportive text response to the user.
2. 'userSentiment': One of 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'.
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                  (React + TypeScript)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Text Input │  │ Voice Record │  │  Stop Speaking  │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│         │                 │                    │            │
│         └─────────────────┴────────────────────┘            │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────┼──────────────────────────────────┐
│                          ▼                                  │
│                   FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /api/chat              /api/voice-chat              │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                          │                       │
│         ▼                          ▼                       │
│  ┌─────────────┐          ┌─────────────────┐             │
│  │  GPT-4o-mini│          │ Faster-Whisper  │             │
│  │  (OpenAI)   │          │    (Local)      │             │
│  └─────────────┘          └─────────────────┘             │
│         │                          │                       │
│         │                          ▼                       │
│         │                  ┌─────────────────┐             │
│         │                  │   GPT-4o-mini   │             │
│         │                  │    (OpenAI)     │             │
│         │                  └─────────────────┘             │
│         │                          │                       │
│         │                          ▼                       │
│         │                  ┌─────────────────┐             │
│         │                  │   Edge-TTS      │             │
│         │                  │    (Local)      │             │
│         │                  └─────────────────┘             │
│         ▼                          │                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Response with Sentiment + Audio           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Python 3.9+**
- **Node.js 16+**
- **OpenAI API key**
- **FFmpeg** (for audio processing)
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `apt-get install ffmpeg`
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/)

## Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Create a .env file in backend/ with:
# OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 3. Running the Application

You need to run both backend and frontend servers:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # If using virtual environment
python main.py
# Backend will run on http://localhost:2179
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Frontend will run on http://localhost:2177
```

### 4. Access the Application

Open your browser and navigate to: `http://localhost:2177`

## Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables (OpenAI API key)
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React component
│   │   ├── index.tsx        # React entry point
│   │   ├── types.ts         # TypeScript interfaces
│   │   ├── components/
│   │   │   ├── Avatar.tsx           # Sentiment-aware avatar
│   │   │   ├── TypingIndicator.tsx  # Loading animation
│   │   │   └── VoiceRecorder.tsx    # Voice input component
│   │   └── services/
│   │       └── api.ts       # API service layer
│   ├── index.html           # HTML template
│   ├── package.json         # Node dependencies
│   ├── vite.config.ts       # Vite configuration
│   └── tsconfig.json        # TypeScript configuration
└── backup-original/         # Original Gemini-based implementation
```

## API Endpoints

### Text Chat
- **POST** `/api/chat`
  - Body: `{ "message": "string", "session_id": "string" }`
  - Response: `{ "reply": "string", "userSentiment": "POSITIVE|NEGATIVE|NEUTRAL" }`

### Voice Chat
- **POST** `/api/voice-chat`
  - Body: FormData with audio file (webm format) and session_id
  - Response: `{ "reply": "string", "userSentiment": "string", "transcription": "string", "audioBase64": "string" }`

### Voice Configuration
- **POST** `/api/voice-config`
  - Body: `{ "voice": "nova|shimmer", "session_id": "string" }`
  - Response: `{ "message": "string", "voice": "string" }`

- **GET** `/api/voice-config/{session_id}`
  - Response: `{ "voice": "string" }`

## Environment Variables

### Backend (.env)
```env
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Text Chat
1. Type your message in the input field at the bottom
2. Press Enter or click the Send button
3. Scyla will respond with empathetic support
4. The avatar changes color based on your sentiment

### Voice Chat
1. Hold down the microphone button
2. Speak your message
3. Release the button when done
4. Your speech will be transcribed and displayed
5. Scyla will respond with both text and voice
6. The avatar pulsates while speaking
7. Click "Stop Speaking" or press Escape to interrupt

## Performance

Typical response times (end-to-end):
- **Text chat**: 2-3 seconds
- **Voice chat**: 4-7 seconds
  - Transcription: ~1-2s
  - GPT response: ~2-3s
  - TTS generation: ~1-2s

## Development

- Backend runs on port 2179
- Frontend runs on port 2177
- CORS is configured to allow frontend-backend communication
- Hot reload enabled for both frontend and backend during development

## Building for Production

```bash
# Frontend
cd frontend
npm run build
# Output will be in frontend/dist/

# Backend
cd backend
# Use a production ASGI server like gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## Troubleshooting

### Voice chat not working
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check microphone permissions in your browser
- Verify the backend logs for specific errors

### Slow transcription
- The first voice request may be slower as models load
- Subsequent requests should be much faster
- Check if FFmpeg is properly installed

### API errors
- Verify your OpenAI API key is correctly set in `.env`
- Check if you have sufficient OpenAI API credits
- Review backend logs for detailed error messages

## Technology Stack

**Backend:**
- FastAPI (Python web framework)
- OpenAI Python SDK (GPT-4o-mini API)
- Faster-Whisper (Local speech recognition)
- Edge-TTS (Local text-to-speech)
- FFmpeg (Audio processing)
- Uvicorn (ASGI server)

**Frontend:**
- React 18
- TypeScript
- Vite (Build tool)
- Tailwind CSS
- Lucide React (Icons)
- Axios (HTTP client)
- MediaRecorder API (Voice recording)

## License

This project is for educational and support purposes.

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing patterns
- New features include appropriate error handling
- Documentation is updated for significant changes

## Acknowledgments

- OpenAI for GPT-4o-mini API
- Microsoft for Edge-TTS
- Faster-Whisper for local speech recognition
- The open-source community for amazing tools and libraries
