import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import Avatar from './components/Avatar';
import { TypingIndicator } from './components/TypingIndicator';
import { sendMessageToGemini } from './services/geminiService';
import { ChatMessage, SentimentState } from './types';

const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'model',
      text: "Hi there. I'm Scyla. I'm here to listen, support, and chat about whatever you're going through. How are you feeling today?"
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sentiment, setSentiment] = useState<SentimentState>(SentimentState.NEUTRAL);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userText = inputValue.trim();
    setInputValue('');
    
    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      text: userText
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // API Call
      const response = await sendMessageToGemini(userText);
      
      // Update Sentiment based on API analysis
      // We explicitly cast the string to the Enum, assuming API adheres to Schema
      const detectedSentiment = response.userSentiment as SentimentState;
      setSentiment(detectedSentiment);

      // Add Model Response
      const modelMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        text: response.reply
      };
      setMessages(prev => [...prev, modelMessage]);

    } catch (error) {
      console.error("Failed to send message", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-warm-50 text-gray-800 font-sans flex flex-col md:flex-row max-w-7xl mx-auto shadow-2xl overflow-hidden rounded-xl my-0 md:my-8 border border-lavender-200">
      
      {/* Left Panel: Avatar & Context */}
      <div className="w-full md:w-1/3 bg-white p-8 flex flex-col items-center justify-center border-b md:border-b-0 md:border-r border-lavender-100 relative overflow-hidden">
        {/* Decorative Background Elements */}
        <div className="absolute top-0 left-0 w-64 h-64 bg-lavender-50 rounded-full mix-blend-multiply filter blur-3xl opacity-70 -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>
        <div className="absolute bottom-0 right-0 w-64 h-64 bg-sage-100 rounded-full mix-blend-multiply filter blur-3xl opacity-70 translate-x-1/2 translate-y-1/2 animate-pulse delay-1000"></div>
        
        <div className="z-10 text-center space-y-6">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-lavender-600 flex items-center justify-center gap-2">
              Scyla
            </h1>
          </div>

          <Avatar sentiment={sentiment} />

          <div className="mt-8 px-6 py-4 bg-warm-50 rounded-xl border border-lavender-100 text-center">
            <p className="text-sm text-gray-600 italic">
              {sentiment === SentimentState.POSITIVE && "I'm so glad to see you in good spirits!"}
              {sentiment === SentimentState.NEGATIVE && "I'm here for you. Take your time."}
              {sentiment === SentimentState.NEUTRAL && "I'm listening. Tell me more."}
            </p>
          </div>
        </div>
      </div>

      {/* Right Panel: Chat Interface */}
      <div className="w-full md:w-2/3 flex flex-col h-[80vh] md:h-[85vh] bg-warm-50 relative">
        
        {/* Messages Area */}
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

        {/* Input Area */}
        <div className="p-4 md:p-6 bg-white border-t border-lavender-100 sticky bottom-0 z-20">
          <form 
            onSubmit={handleSendMessage}
            className="flex items-center gap-3 bg-warm-50 p-2 pr-2 rounded-full border border-lavender-200 focus-within:ring-2 focus-within:ring-lavender-300 focus-within:border-transparent transition-all shadow-sm"
          >
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type a message..."
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