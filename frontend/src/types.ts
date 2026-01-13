export enum SentimentState {
  NEUTRAL = 'NEUTRAL',
  POSITIVE = 'POSITIVE',
  NEGATIVE = 'NEGATIVE',
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'model';
  text: string;
}

export interface ChatResponse {
  reply: string;
  userSentiment: string;
}

export interface VoiceChatResponse {
  reply: string;
  userSentiment: string;
  transcription: string;
  audioBase64: string;
}
