# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Scyla** is a sentiment-aware AI companion web application designed to support women navigating menopause. Built with React, TypeScript, and Vite, it features real-time sentiment analysis using Google's Gemini AI API and a color-changing avatar that reflects detected user emotions.

**AI Studio App**: https://ai.studio/apps/drive/1b85LSjISFb-Dl9TJyieMAg586cTb_RMw

## Development Commands

```bash
# Install dependencies
npm install

# Run development server (localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm preview
```

## Environment Setup

Create a `.env.local` file in the root directory with:
```
GEMINI_API_KEY=your_api_key_here
```

The Vite config (vite.config.ts:14-15) maps this to `process.env.API_KEY` for the Gemini service.

## Architecture

### Core Flow
1. **User Input** → App.tsx handles message state and UI rendering
2. **API Call** → services/geminiService.ts sends message to Gemini API with system instruction
3. **Structured Response** → Gemini returns JSON with `{reply: string, userSentiment: string}`
4. **State Update** → Sentiment updates Avatar component, reply added to chat history

### Key Components

**App.tsx** (main component)
- Manages chat messages state and sentiment state
- Two-panel layout: Avatar panel (left) and chat interface (right)
- Calls `sendMessageToGemini()` on message submit
- Updates sentiment based on API response (App.tsx:52-53)

**services/geminiService.ts** (Gemini AI integration)
- Maintains singleton chat instance with system instruction defining Scyla's persona
- Enforces structured JSON output via `responseSchema` (geminiService.ts:34-48)
- System instruction defines sentiment classification rules (geminiService.ts:10-23)
- Fallback handling for API errors (geminiService.ts:72-75)

**components/Avatar.tsx** (visual sentiment indicator)
- SVG-based circular avatar that changes color based on sentiment
- Color mapping: POSITIVE=green, NEGATIVE=red, NEUTRAL=orange
- Includes status badge and smooth transitions

**types.ts** (shared interfaces)
- `SentimentState` enum: NEUTRAL | POSITIVE | NEGATIVE
- `ChatMessage` interface: id, role ('user' | 'model'), text
- `GeminiResponse` interface: reply, userSentiment

### Styling
- Uses Tailwind CSS via CDN (index.html:7)
- Custom color palette: sage (green tones), lavender (purple tones), warm (cream tones)
- Quicksand font from Google Fonts
- Tailwind config defined inline in index.html:24-53

### Import Maps
Dependencies loaded via AI Studio CDN import maps (index.html:55-65), not traditional node_modules for production deployment.

## Important Implementation Details

**Gemini API Configuration**
- Model: `gemini-2.5-flash`
- Response format: `application/json` with strict schema enforcement
- Chat instance is reused across messages to maintain conversation context

**Sentiment Detection**
The API analyzes user sentiment on every message based on emotional tone, not just keywords. The system instruction provides clear guidelines for classification.

**Environment Variable Access**
Vite's `loadEnv()` reads `.env.local` and defines values at build time via `defineConfig` (vite.config.ts:13-16).

**TypeScript Configuration**
- Uses React JSX transform (`jsx: "react-jsx"`)
- Path alias `@/*` maps to project root
- ES2022 target with experimental decorators enabled
