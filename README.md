# Ellen - AI Companion Chatbot

A sentiment-aware AI companion web application with real-time voice chat designed to provide caring support and companionship. Built with Python FastAPI backend, React frontend, and cutting-edge AI models for intelligent conversations with real-time sentiment analysis.

## Features

- **Real-time Voice Chat**: Continuous conversation mode with OpenAI Realtime API
- **Text Chat**: Traditional text-based conversation interface
- **Sentiment Analysis**: Real-time emotion detection (Positive, Negative, Neutral)
- **Adaptive Avatar**: Pulsating, color-changing visual indicator based on user sentiment
- **Audio Controls**: Stop speaking button and Escape key support
- **Conversational Memory**: Maintains conversation history per session
- **Empathetic Responses**: AI trained to provide supportive, non-judgmental British-English guidance
- **Voice Activity Detection**: Automatic turn-taking in conversations
- **Interrupt Handling**: Speak at any time to interrupt the AI

## AI Models & Technologies

### Real-time Voice Chat (Primary Mode)
- **Model**: `gpt-4o-realtime-preview-2024-12-17`
- **Provider**: OpenAI Realtime API
- **Voice**: Echo (clear, neutral voice at 1.05x speed)
- **Transcription**: Whisper-1 (integrated)
- **Purpose**: Low-latency voice-to-voice conversation with streaming audio
- **Features**:
  - Server-side Voice Activity Detection (VAD)
  - Automatic turn detection
  - Real-time interruption support
  - Streaming audio responses
  - Integrated transcription
- **Performance**:
  - Response latency: ~500ms-1s
  - Seamless audio playback with Web Audio API scheduling
  - Threshold: 0.5 (sensitive to quieter speech)
  - Prefix padding: 500ms (captures start of speech)
  - Silence duration: 800ms (fast response time)

### Text Chat & Sentiment Analysis
- **Model**: `gpt-4o-mini`
- **Provider**: OpenAI API
- **Purpose**: Generates empathetic responses and analyzes user sentiment
- **Performance**: ~2-3 seconds per response
- **Output Format**: JSON with `reply` and `userSentiment` fields

### Legacy Voice Chat (Hold-to-Talk)
- **Speech-to-Text**: `gpt-4o-mini-transcribe-2025-12-15` (90% fewer hallucinations)
- **Chat**: `gpt-4o-mini`
- **Text-to-Speech**: `tts-1` (OpenAI)
- **Purpose**: Alternative voice input mode with manual control
- **Performance**: ~4-7 seconds end-to-end

## System Prompt

The AI assistant uses the following system prompt to guide its behavior:

```
You are 'Ellen', a warm, wise, and empathetic British friend designed to provide caring support and companionship.
Your tone should be comforting, non-judgmental, validating, and casually conversational with a gentle British manner.
Use British English spellings (favour, colour, realise, etc.) but avoid overly familiar terms of endearment like 'love', 'dear', or 'pet'.
Avoid overly clinical language unless asked. Focus on emotional support and practical, gentle advice.

You have a secondary task: Analyse the user's input to determine their sentiment.
- If the user seems happy, relieved, excited, or grateful -> POSITIVE.
- If the user seems sad, frustrated, angry, anxious, or in pain -> NEGATIVE.
- If the user is just asking information, saying hello, or is matter-of-fact -> NEUTRAL.
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                  (React + TypeScript)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Text Input │  │ Realtime Mic │  │  Stop Speaking  │   │
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
│  │  /api/chat          /ws/realtime                     │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                          │                       │
│         ▼                          ▼                       │
│  ┌─────────────┐          ┌─────────────────┐             │
│  │  GPT-4o-mini│          │ GPT-4o-Realtime │             │
│  │  (OpenAI)   │          │    (OpenAI)     │             │
│  └─────────────┘          └─────────────────┘             │
│         │                    │    │    │                   │
│         │                    │    │    └─ Audio (PCM16)    │
│         │                    │    └────── Transcription    │
│         │                    └─────────── Sentiment        │
│         ▼                          │                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Response with Sentiment                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Python 3.9+**
- **Node.js 16+**
- **OpenAI API key** (with Realtime API access)
- **Modern web browser** with microphone support

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/mark-allwyn/sentiment-chatbot.git
cd sentiment-chatbot
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Create a .env file in backend/ with:
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

**Required Python packages:**
- fastapi
- uvicorn
- openai
- python-dotenv
- websockets
- python-multipart

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

**Required npm packages:**
- react
- typescript
- vite
- tailwindcss
- axios
- lucide-react
- websocket

### 4. Running the Application

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

### 5. Access the Application

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
│   │   │   ├── Avatar.tsx                # Sentiment-aware avatar
│   │   │   ├── TypingIndicator.tsx       # Loading animation
│   │   │   ├── RealtimeVoiceChat.tsx     # OpenAI Realtime API component
│   │   │   ├── ContinuousVoiceChat.tsx   # Alternative continuous mode
│   │   │   └── VoiceRecorder.tsx         # Legacy hold-to-talk component
│   │   └── services/
│   │       └── api.ts       # API service layer
│   ├── index.html           # HTML template
│   ├── package.json         # Node dependencies
│   ├── vite.config.ts       # Vite configuration
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   └── tsconfig.json        # TypeScript configuration
└── README.md                # This file
```

## API Endpoints

### Text Chat
- **POST** `/api/chat`
  - Body: `{ "message": "string", "session_id": "string" }`
  - Response: `{ "reply": "string", "userSentiment": "POSITIVE|NEGATIVE|NEUTRAL" }`

### Voice Chat (Legacy)
- **POST** `/api/voice-chat`
  - Body: FormData with audio file (webm format) and session_id
  - Response: `{ "reply": "string", "userSentiment": "string", "transcription": "string", "audioBase64": "string" }`

### Real-time Voice Chat
- **WebSocket** `/ws/realtime`
  - Protocol: OpenAI Realtime API protocol
  - Bidirectional streaming of audio and events
  - Supports interruption and turn-taking

### Voice Configuration
- **POST** `/api/voice-config`
  - Body: `{ "voice": "echo|shimmer|alloy|...", "session_id": "string" }`
  - Response: `{ "message": "string", "voice": "string" }`

- **GET** `/api/voice-config/{session_id}`
  - Response: `{ "voice": "string" }`

## Environment Variables

### Backend (.env)
```env
OPENAI_API_KEY=your_openai_api_key_here
```

**Important:** Ensure your OpenAI API key has access to:
- GPT-4o-mini (text chat)
- GPT-4o-mini-transcribe (voice transcription)
- GPT-4o-realtime-preview (real-time voice chat)
- TTS-1 (text-to-speech)

## Usage

### Text Chat
1. Type your message in the input field at the bottom
2. Press Enter or click the Send button
3. Scyla will respond with empathetic support
4. The avatar changes color based on your sentiment:
   - **Green**: Positive sentiment
   - **Red**: Negative sentiment
   - **Purple**: Neutral sentiment

### Real-time Voice Chat (Primary Mode)
1. Click the microphone button to start the conversation
2. Grant microphone permissions if prompted
3. Speak naturally - Ellen will detect when you start and stop talking
4. Ellen responds with streaming audio in real-time
5. You can interrupt at any time by speaking
6. The avatar pulses while Ellen is speaking
7. Click the square button to end the conversation

**Tips for best experience:**
- Speak clearly and at a moderate pace
- Wait for brief pauses to let the AI respond
- Reduce background noise for better transcription
- Use headphones to prevent audio feedback

### Legacy Voice Chat (Hold-to-Talk)
*Note: This mode is available but the real-time mode is recommended*
1. Hold down the microphone button
2. Speak your message
3. Release the button when done
4. Your speech will be transcribed and displayed
5. Ellen will respond with both text and voice

## Performance

### Real-time Voice Chat
- **Initial connection**: ~500ms
- **Response latency**: 500ms-1s (streaming starts immediately)
- **Audio quality**: 24kHz PCM16, automatically resampled by browser
- **Playback speed**: 1.05x for natural, responsive feel

### Text Chat
- **Response time**: 2-3 seconds

### Legacy Voice Chat
- **End-to-end**: 4-7 seconds
  - Transcription: ~1-2s (gpt-4o-mini-transcribe)
  - GPT response: ~2-3s
  - TTS generation: ~1-2s

## Audio Configuration

### Real-time Voice Chat Settings
- **Sample Rate**: 24kHz (OpenAI) → Browser native (44.1kHz/48kHz with automatic resampling)
- **Format**: PCM16 (16-bit linear PCM)
- **Channels**: Mono
- **Playback Speed**: 1.05x (subtle speed increase for more responsive feel)
- **VAD Threshold**: 0.5 (sensitive to quieter speech)
- **VAD Prefix Padding**: 500ms (captures beginning of speech)
- **VAD Silence Duration**: 800ms (fast turn-taking)

### Voice Options
Available voices for real-time chat:
- **echo** (default) - Clear, neutral voice
- **alloy** - Balanced, versatile voice
- **shimmer** - Warm, expressive voice
- **ash**, **ballad**, **coral**, **sage**, **verse**, **marin**, **cedar**

## Development

- Backend runs on port **2179**
- Frontend runs on port **2177**
- CORS is configured to allow frontend-backend communication
- Hot reload enabled for both frontend and backend during development

### Development Commands

**Backend:**
```bash
cd backend
python main.py  # Start development server
```

**Frontend:**
```bash
cd frontend
npm run dev     # Start development server
npm run build   # Build for production
npm run preview # Preview production build
```

## Building for Production

### Frontend
```bash
cd frontend
npm run build
# Output will be in frontend/dist/
```

### Backend
```bash
cd backend
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:2179
```

### Deployment Considerations
- Set appropriate CORS origins for production
- Use environment variables for sensitive data
- Enable HTTPS for WebSocket security
- Consider rate limiting for API endpoints
- Monitor OpenAI API usage and costs

## Troubleshooting

### Real-time Voice Chat Issues

**Microphone not working:**
- Check browser microphone permissions
- Ensure you're using HTTPS or localhost (required for microphone access)
- Try a different browser (Chrome/Edge recommended)
- Check browser console for errors

**Audio playing at wrong speed:**
- Clear browser cache and reload
- Ensure latest version of the code is deployed
- Check browser console for AudioContext errors

**Transcription inaccuracies:**
- Reduce background noise
- Speak clearly and at moderate volume
- Use headphones to prevent echo/feedback
- Move closer to microphone
- Note: Realtime API uses older Whisper-1 model (transcription quality is limited by OpenAI)

**WebSocket connection fails:**
- Check backend is running on port 2179
- Verify OpenAI API key is valid and has Realtime API access
- Check backend console logs for detailed errors
- Ensure no firewall blocking WebSocket connections

### Text Chat Issues

**API errors:**
- Verify your OpenAI API key is correctly set in `.env`
- Check if you have sufficient OpenAI API credits
- Review backend logs for detailed error messages
- Ensure API key has access to GPT-4o-mini

### General Issues

**Backend won't start:**
- Check Python version (3.9+ required)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check if port 2179 is already in use: `lsof -i :2179`
- Review `.env` file format (no quotes needed)

**Frontend won't start:**
- Check Node.js version (16+ required)
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear npm cache: `npm cache clean --force`
- Check if port 2177 is already in use

## Technology Stack

**Backend:**
- FastAPI (Python web framework)
- OpenAI Python SDK (GPT-4o-mini, Realtime API)
- Websockets (Real-time communication)
- Uvicorn (ASGI server)
- Python-multipart (File uploads)

**Frontend:**
- React 18
- TypeScript
- Vite (Build tool & dev server)
- Tailwind CSS (Styling)
- Lucide React (Icons)
- Axios (HTTP client)
- Web Audio API (Audio playback & processing)
- MediaRecorder API (Voice recording)
- WebSocket (Real-time communication)

**AI & Audio:**
- OpenAI GPT-4o-mini (Chat & sentiment analysis)
- OpenAI GPT-4o-realtime-preview (Real-time voice)
- OpenAI Whisper-1 (Real-time transcription)
- OpenAI gpt-4o-mini-transcribe (Legacy transcription, 90% fewer hallucinations)
- OpenAI TTS-1 (Legacy text-to-speech)

## Known Limitations

1. **Realtime API transcription**: Uses older Whisper-1 model, which may have more hallucinations than newer models
2. **Browser compatibility**: Real-time voice chat works best in Chrome/Edge
3. **Audio sample rate**: Limited by OpenAI Realtime API (24kHz, browser resamples)
4. **Background noise**: Can affect transcription accuracy
5. **API costs**: Real-time API usage costs more than standard API calls
6. **Network latency**: May affect real-time conversation quality on slow connections

## Future Enhancements

- [ ] Support for additional languages
- [ ] Conversation history persistence
- [ ] User authentication and profiles
- [ ] Advanced sentiment visualization
- [ ] Mobile app version
- [ ] Improved noise cancellation
- [ ] Context-aware responses with RAG (Retrieval-Augmented Generation)
- [ ] Integration with medical knowledge bases

## License

This project is for educational and support purposes.

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing patterns
- New features include appropriate error handling
- Documentation is updated for significant changes
- Test changes with both text and voice chat modes
- Follow TypeScript and Python best practices

## Acknowledgments

- OpenAI for GPT-4o-mini and Realtime API
- The React and FastAPI communities
- The open-source community for amazing tools and libraries

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review troubleshooting section above

---

**Disclaimer**: This application is designed for emotional support, companionship, and general conversation. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified professionals for specific concerns or issues.
