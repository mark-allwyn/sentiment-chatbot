# Scyla - AI Companion for Menopause Support

A sentiment-aware AI companion web application designed to support women navigating menopause. Built with Python FastAPI backend, React frontend, and OpenAI for intelligent conversations with real-time sentiment analysis.

## Architecture

- **Backend**: Python FastAPI server with OpenAI integration
- **Frontend**: React + TypeScript + Vite
- **AI**: OpenAI GPT-4o-mini for conversations and sentiment analysis
- **Features**: Real-time sentiment detection, color-changing avatar, conversational AI

## Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key

## Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Edit backend/.env and add your OpenAI API key:
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
python main.py
# Backend will run on http://localhost:8000
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
│   ├── main.py              # FastAPI application with OpenAI integration
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables (OpenAI API key)
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React component
│   │   ├── index.tsx        # React entry point
│   │   ├── types.ts         # TypeScript interfaces
│   │   ├── components/      # React components (Avatar, TypingIndicator)
│   │   └── services/        # API service layer
│   ├── index.html           # HTML template with Tailwind
│   ├── package.json         # Node dependencies
│   ├── vite.config.ts       # Vite configuration
│   └── tsconfig.json        # TypeScript configuration
└── backup-original/         # Original Gemini-based implementation
```

## Key Features

- **Sentiment Analysis**: Real-time emotion detection (Positive, Negative, Neutral)
- **Adaptive Avatar**: Color-changing visual indicator based on user sentiment
- **Conversational Memory**: Backend maintains conversation history per session
- **Empathetic Responses**: AI trained to provide supportive, non-judgmental guidance
- **Clean Architecture**: Separated backend/frontend for scalability

## API Endpoints

- `GET /` - Health check
- `POST /api/chat` - Send message and receive AI response with sentiment

## Environment Variables

### Backend (.env)
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Development

- Backend runs on port 8000
- Frontend runs on port 2177
- CORS is configured to allow frontend-backend communication

## Building for Production

```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
# Use a production ASGI server like gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```
