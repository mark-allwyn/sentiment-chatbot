import { GoogleGenAI, Type, Chat } from "@google/genai";
import { GeminiResponse, SentimentState } from "../types";

const apiKey = process.env.API_KEY || '';

// Initialize client
const ai = new GoogleGenAI({ apiKey });

// System instruction to define persona and output format
const SYSTEM_INSTRUCTION = `
You are 'Scyla', a warm, wise, and empathetic female friend designed to support women going through menopause.
Your tone should be comforting, non-judgmental, validatng, and casually conversational. 
Avoid overly clinical language unless asked. Focus on emotional support and practical, gentle advice.

You have a secondary task: Analyze the user's input to determine their sentiment.
- If the user seems happy, relieved, excited, or grateful -> POSITIVE.
- If the user seems sad, frustrated, angry, anxious, or in pain -> NEGATIVE.
- If the user is just asking information, saying hello, or is matter-of-fact -> NEUTRAL.

You MUST always return a JSON object with two fields:
1. 'reply': Your supportive text response to the user.
2. 'userSentiment': One of 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'.
`;

let chatInstance: Chat | null = null;

export const getChatInstance = () => {
  if (!chatInstance) {
    chatInstance = ai.chats.create({
      model: 'gemini-2.5-flash',
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        responseMimeType: 'application/json',
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            reply: {
              type: Type.STRING,
              description: "The supportive response text from Scyla."
            },
            userSentiment: {
              type: Type.STRING,
              enum: [SentimentState.POSITIVE, SentimentState.NEUTRAL, SentimentState.NEGATIVE],
              description: "The detect sentiment of the user's latest message."
            }
          },
          required: ["reply", "userSentiment"]
        }
      }
    });
  }
  return chatInstance;
};

export const sendMessageToGemini = async (message: string): Promise<GeminiResponse> => {
  const chat = getChatInstance();
  
  try {
    const result = await chat.sendMessage({ message });
    const responseText = result.text;
    
    if (!responseText) {
      throw new Error("Empty response from Gemini");
    }

    // Parse the JSON response
    const data = JSON.parse(responseText) as GeminiResponse;
    return data;
  } catch (error) {
    console.error("Gemini API Error:", error);
    // Fallback in case of parsing error or API failure to keep app running
    return {
      reply: "I'm having a little trouble connecting right now, but I'm still here for you. Can you say that again?",
      userSentiment: "NEUTRAL"
    };
  }
};