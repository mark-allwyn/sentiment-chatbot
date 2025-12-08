import axios from 'axios';
import { ChatResponse, VoiceChatResponse } from '../types';

const API_BASE_URL = 'http://localhost:2179';

export const sendMessage = async (message: string): Promise<ChatResponse> => {
  try {
    const response = await axios.post<ChatResponse>(`${API_BASE_URL}/api/chat`, {
      message,
      session_id: 'default'
    });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const sendVoiceMessage = async (audioBlob: Blob): Promise<VoiceChatResponse> => {
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('session_id', 'default');

    const response = await axios.post<VoiceChatResponse>(
      `${API_BASE_URL}/api/voice-chat`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error('Voice API Error:', error);
    throw error;
  }
};

export const setVoicePreference = async (voice: 'nova' | 'shimmer'): Promise<void> => {
  try {
    await axios.post(`${API_BASE_URL}/api/voice-config`, {
      voice,
      session_id: 'default'
    });
  } catch (error) {
    console.error('Voice config error:', error);
    throw error;
  }
};

export const getVoicePreference = async (): Promise<string> => {
  try {
    const response = await axios.get<{ voice: string }>(
      `${API_BASE_URL}/api/voice-config/default`
    );
    return response.data.voice;
  } catch (error) {
    console.error('Voice config error:', error);
    return 'nova'; // Default fallback
  }
};
