import React, { useState, useRef, useEffect } from 'react';
import { Send, Square } from 'lucide-react';
import Avatar from './components/Avatar';
import { TypingIndicator } from './components/TypingIndicator';
import { RealtimeVoiceChat } from './components/RealtimeVoiceChat';
import { sendMessage } from './services/api';
import { ChatMessage, SentimentState } from './types';

const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'model',
      text: "Hi there. I'm Ellen. I'm here to listen, support, and chat about whatever you're going through. How are you feeling today?"
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sentiment, setSentiment] = useState<SentimentState>(SentimentState.NEUTRAL);
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const [currentAudioUrl, setCurrentAudioUrl] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Stop audio playback
  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current.src = '';
    }

    // Clean up Object URL
    if (currentAudioUrl) {
      URL.revokeObjectURL(currentAudioUrl);
      setCurrentAudioUrl(null);
    }

    setIsAudioPlaying(false);
  };

  // Keyboard support for stopping audio
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isAudioPlaying) {
        stopAudio();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isAudioPlaying]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAudio();
    };
  }, []);

  // Function to play audio from base64
  const playAudio = (audioBase64: string) => {
    try {
      // Stop any currently playing audio first
      stopAudio();

      const audioBlob = base64ToBlob(audioBase64, 'audio/mp3');
      const audioUrl = URL.createObjectURL(audioBlob);
      setCurrentAudioUrl(audioUrl);

      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = audioUrl;
      } else {
        audioRef.current = new Audio(audioUrl);
      }

      audioRef.current.play()
        .then(() => {
          setIsAudioPlaying(true);
        })
        .catch(error => {
          console.error('Error playing audio:', error);
          stopAudio(); // Clean up on error
        });

      // Handle audio end
      audioRef.current.onended = () => {
        URL.revokeObjectURL(audioUrl);
        setCurrentAudioUrl(null);
        setIsAudioPlaying(false);
      };

      // Handle audio errors
      audioRef.current.onerror = () => {
        console.error('Audio playback error');
        stopAudio();
      };
    } catch (error) {
      console.error('Error creating audio:', error);
      stopAudio();
    }
  };

  // Helper function to convert base64 to blob
  const base64ToBlob = (base64: string, contentType: string): Blob => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: contentType });
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userText = inputValue.trim();
    setInputValue('');

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      text: userText
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await sendMessage(userText);

      const detectedSentiment = response.userSentiment as SentimentState;
      setSentiment(detectedSentiment);

      const modelMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        text: response.reply
      };
      setMessages(prev => [...prev, modelMessage]);

    } catch (error) {
      console.error("Failed to send message", error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        text: "I'm having a little trouble connecting right now, but I'm still here for you. Can you say that again?"
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTranscript = (text: string, role: 'user' | 'assistant') => {
    const message: ChatMessage = {
      id: Date.now().toString(),
      role: role === 'user' ? 'user' : 'model',
      text: text
    };
    setMessages(prev => [...prev, message]);
  };

  const handleAISpeakingChange = (isSpeaking: boolean) => {
    setIsAudioPlaying(isSpeaking);
  };

  const handleSentimentChange = (sentimentStr: string) => {
    console.log('handleSentimentChange called with:', sentimentStr);
    const sentimentMap: { [key: string]: SentimentState } = {
      'POSITIVE': SentimentState.POSITIVE,
      'NEGATIVE': SentimentState.NEGATIVE,
      'NEUTRAL': SentimentState.NEUTRAL
    };
    const newSentiment = sentimentMap[sentimentStr] || SentimentState.NEUTRAL;
    console.log('Setting sentiment to:', newSentiment);
    console.log('Current sentiment before update:', sentiment);
    setSentiment(newSentiment);
  };

  const printTranscript = () => {
    console.log('=== CONVERSATION TRANSCRIPT ===');
    messages.forEach((msg, index) => {
      const role = msg.role === 'user' ? 'USER' : 'ELLEN';
      console.log(`[${index + 1}] ${role}: ${msg.text}`);
    });
    console.log('=== END TRANSCRIPT ===');
    alert('Transcript printed to browser console (F12)');
  };


  return (
    <div className="min-h-screen bg-warm-50 text-gray-800 font-sans flex flex-col md:flex-row max-w-7xl mx-auto shadow-2xl overflow-hidden rounded-xl my-0 md:my-8 border border-lavender-200">

      <div className="w-full md:w-1/3 bg-white p-8 flex flex-col items-center justify-center border-b md:border-b-0 md:border-r border-lavender-100 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-64 h-64 bg-lavender-50 rounded-full mix-blend-multiply filter blur-3xl opacity-70 -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>
        <div className="absolute bottom-0 right-0 w-64 h-64 bg-sage-100 rounded-full mix-blend-multiply filter blur-3xl opacity-70 translate-x-1/2 translate-y-1/2 animate-pulse delay-1000"></div>

        <div className="z-10 text-center space-y-6">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-lavender-600 flex items-center justify-center gap-2">
              Ellen
            </h1>
          </div>

          <Avatar sentiment={sentiment} isAudioPlaying={isAudioPlaying} />

          {/* Audio Stop Button */}
          {isAudioPlaying && (
            <button
              onClick={stopAudio}
              className="mx-auto flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-full shadow-lg transition-all duration-200 transform hover:scale-105 active:scale-95 animate-pulse"
              aria-label="Stop audio playback"
            >
              <Square className="w-4 h-4" fill="currentColor" />
              <span className="text-sm font-medium">Stop Speaking</span>
            </button>
          )}

          <div className="mt-8 px-6 py-4 bg-warm-50 rounded-xl border border-lavender-100 text-center">
            <p className="text-sm text-gray-600 italic">
              {sentiment === SentimentState.POSITIVE && "I'm so glad to see you in good spirits!"}
              {sentiment === SentimentState.NEGATIVE && "I'm here for you. Take your time."}
              {sentiment === SentimentState.NEUTRAL && "I'm listening. Tell me more."}
            </p>
          </div>

          {messages.length > 1 && (
            <button
              onClick={printTranscript}
              className="mt-4 px-4 py-2 bg-lavender-500 hover:bg-lavender-600 text-white rounded-lg shadow-md transition-all duration-200 transform hover:scale-105 active:scale-95 text-sm font-medium"
            >
              Print Transcript
            </button>
          )}
        </div>
      </div>

      <div className="w-full md:w-2/3 flex flex-col h-[80vh] md:h-[85vh] bg-warm-50 relative">

        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scrollbar-hide">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] md:max-w-[75%] p-4 rounded-2xl shadow-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-lavender-500 text-white rounded-br-none'
                    : 'bg-white text-gray-700 border border-lavender-100 rounded-bl-none'
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex w-full justify-start">
              <TypingIndicator />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 md:p-6 bg-white border-t border-lavender-100 sticky bottom-0 z-20">
          <form
            onSubmit={handleSendMessage}
            className="flex items-center gap-3 bg-warm-50 p-2 pr-2 rounded-full border border-lavender-200 focus-within:ring-2 focus-within:ring-lavender-300 focus-within:border-transparent transition-all shadow-sm"
          >
            <RealtimeVoiceChat
              onTranscript={handleTranscript}
              onAISpeakingChange={handleAISpeakingChange}
              onSentimentChange={handleSentimentChange}
              disabled={isLoading}
            />
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type a message or start real-time conversation..."
              disabled={isLoading}
              className="flex-1 bg-transparent px-4 py-3 outline-none text-gray-700 placeholder-gray-400"
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="p-3 bg-lavender-500 text-white rounded-full hover:bg-lavender-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md transform hover:scale-105 active:scale-95"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          <div className="text-center mt-2">
             <p className="text-xs text-gray-400">AI can make mistakes. Please consult a doctor for medical advice.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
