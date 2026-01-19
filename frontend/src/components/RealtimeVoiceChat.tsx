import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';

interface RealtimeVoiceChatProps {
  onTranscript?: (text: string, role: 'user' | 'assistant') => void;
  disabled?: boolean;
  onAISpeakingChange?: (isSpeaking: boolean) => void;
  onSentimentChange?: (sentiment: string) => void;
}

export const RealtimeVoiceChat: React.FC<RealtimeVoiceChatProps> = ({
  onTranscript,
  disabled,
  onAISpeakingChange,
  onSentimentChange
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isAISpeaking, setIsAISpeaking] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<Int16Array[]>([]);
  const isPlayingRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Convert Float32Array to Int16Array (PCM16)
  const floatTo16BitPCM = (float32Array: Float32Array): Int16Array => {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return int16Array;
  };

  // Convert Int16Array to base64
  const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  };

  // Play audio from base64 PCM16
  const playAudio = async (base64Audio: string) => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext();
      }

      // Decode base64 to Int16Array
      const binaryString = atob(base64Audio);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      const int16Array = new Int16Array(bytes.buffer);

      // Add to queue
      audioQueueRef.current.push(int16Array);

      // Start playing if not already playing
      if (!isPlayingRef.current) {
        playNextInQueue();
      }
    } catch (error) {
      console.error('Error playing audio:', error);
    }
  };

  const playNextInQueue = async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setIsAISpeaking(false);
      return;
    }

    isPlayingRef.current = true;
    setIsAISpeaking(true);

    const int16Array = audioQueueRef.current.shift()!;

    if (!audioContextRef.current) return;

    // Convert Int16 to Float32 for Web Audio API
    const float32Array = new Float32Array(int16Array.length);
    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / (int16Array[i] < 0 ? 0x8000 : 0x7FFF);
    }

    // Create audio buffer
    const audioBuffer = audioContextRef.current.createBuffer(
      1,
      float32Array.length,
      24000
    );
    audioBuffer.getChannelData(0).set(float32Array);

    // Play
    const source = audioContextRef.current.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContextRef.current.destination);

    source.onended = () => {
      playNextInQueue();
    };

    source.start();
  };

  const connectWebSocket = async () => {
    try {
      console.log('Connecting to WebSocket...');
      const ws = new WebSocket('ws://localhost:2179/ws/realtime');
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected!');
        setIsConnected(true);
        // Start recording once WebSocket is connected
        startRecording();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('Received:', message.type);

          switch (message.type) {
            case 'session.created':
            case 'session.updated':
              console.log('Session ready');
              break;

            case 'input_audio_buffer.speech_started':
              console.log('User started speaking - cancelling any AI response');
              // Clear audio queue when user starts speaking (interruption)
              audioQueueRef.current = [];
              isPlayingRef.current = false;
              setIsAISpeaking(false);

              // Send cancel event to stop AI generation
              if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({
                  type: 'response.cancel'
                }));
              }
              break;

            case 'input_audio_buffer.speech_stopped':
              console.log('User stopped speaking');
              break;

            case 'conversation.item.created':
              if (message.item?.content) {
                const transcript = message.item.content.find((c: any) => c.transcript)?.transcript;
                if (transcript && onTranscript) {
                  onTranscript(transcript, message.item.role);
                }
              }
              break;

            case 'conversation.item.input_audio_transcription.completed':
              console.log('User transcript completed:', message.transcript);
              if (message.transcript && onTranscript) {
                onTranscript(message.transcript, 'user');
              }
              break;

            case 'response.audio.delta':
            case 'response.output_audio.delta':
              if (message.delta) {
                playAudio(message.delta);
              }
              break;

            case 'response.audio_transcript.done':
            case 'response.output_audio_transcript.done':
              console.log('AI transcript completed:', message.text || message.transcript);
              const aiText = message.text || message.transcript;
              if (aiText && onTranscript) {
                onTranscript(aiText, 'assistant');
              }
              break;

            case 'response.audio.done':
            case 'response.output_audio.done':
              console.log('AI finished speaking');
              break;

            case 'response.done':
              console.log('Response complete - ready for next voice input');
              break;

            case 'sentiment.update':
              console.log('Sentiment update received:', message.sentiment);
              if (message.sentiment && onSentimentChange) {
                console.log('Calling onSentimentChange with:', message.sentiment);
                onSentimentChange(message.sentiment);
              } else {
                console.log('onSentimentChange not called - sentiment:', message.sentiment, 'callback:', !!onSentimentChange);
              }
              break;

            case 'error':
              console.error('OpenAI error:', message.error);
              break;
          }
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setIsRecording(false);
      };

    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,  // Gemini requires 16kHz input
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      streamRef.current = stream;
      console.log('Got media stream');

      // Create AudioContext for processing
      const audioContext = new AudioContext({ sampleRate: 16000 });  // Gemini requires 16kHz input
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(2048, 1, 1);

      source.connect(processor);
      processor.connect(audioContext.destination);

      processor.onaudioprocess = (e) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          // Log if WebSocket is not ready (but only occasionally to avoid spam)
          if (Math.random() < 0.01) {
            console.log('⚠️ WebSocket not ready, state:', wsRef.current?.readyState);
          }
          return;
        }

        const float32Array = e.inputBuffer.getChannelData(0);

        // Calculate volume level for VAD
        let sum = 0;
        for (let i = 0; i < float32Array.length; i++) {
          sum += float32Array[i] * float32Array[i];
        }
        const rms = Math.sqrt(sum / float32Array.length);
        const volume = Math.max(0, Math.min(1, rms * 10)); // Normalize to 0-1

        // Voice Activity Detection threshold
        const SPEECH_THRESHOLD = 0.01; // Adjust based on your environment
        const SILENCE_DURATION = 1000; // 1 second of silence to consider turn complete

        const isSpeaking = volume > SPEECH_THRESHOLD;

        // Always send the actual audio (not zeros) - let Gemini's VAD handle speech detection
        const int16Array = floatTo16BitPCM(float32Array);
        const base64Audio = arrayBufferToBase64(int16Array.buffer as ArrayBuffer);

        const message = {
          type: 'input_audio_buffer.append',
          audio: base64Audio
        };

        wsRef.current.send(JSON.stringify(message));

        // Track speaking state for UI feedback only
        if (isSpeaking && !isSpeakingRef.current) {
          console.log('Speech detected (volume:', volume.toFixed(3), ')');
          isSpeakingRef.current = true;
        } else if (!isSpeaking && isSpeakingRef.current) {
          console.log('Silence detected');
          isSpeakingRef.current = false;
        }
      };

      setIsRecording(true);
      console.log('Recording started');

    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    // Clear silence timeout
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }

    isSpeakingRef.current = false;
    setIsRecording(false);
    console.log('Recording stopped');
  };

  const toggleConnection = async () => {
    console.log('Toggle connection clicked, isConnected:', isConnected);
    if (isConnected) {
      // Disconnect
      console.log('Disconnecting...');
      stopRecording();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      // Clear audio queue
      audioQueueRef.current = [];
      setIsConnected(false);
    } else {
      // Connect - recording will be started from ws.onopen callback
      console.log('Connecting to WebSocket...');
      await connectWebSocket();
    }
  };

  // Notify parent when AI speaking state changes
  useEffect(() => {
    if (onAISpeakingChange) {
      onAISpeakingChange(isAISpeaking);
    }
  }, [isAISpeaking, onAISpeakingChange]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  console.log('RealtimeVoiceChat rendering, disabled:', disabled, 'isConnected:', isConnected);

  return (
    <div className="relative flex items-center justify-center">
      <button
        onClick={toggleConnection}
        disabled={disabled}
        className={`p-4 rounded-full transition-all duration-200 shadow-lg ${
          isConnected
            ? isRecording
              ? 'bg-red-500 hover:bg-red-600 ring-4 ring-red-300 animate-pulse'
              : 'bg-green-500 hover:bg-green-600 ring-4 ring-green-300'
            : 'bg-purple-500 hover:bg-purple-600 hover:scale-105'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-label={isConnected ? 'Disconnect' : 'Connect'}
        title={isConnected ? 'Click to end conversation' : 'Click to start real-time conversation'}
      >
        {disabled ? (
          <Loader2 className="w-6 h-6 text-white animate-spin" />
        ) : isConnected ? (
          <Square className="w-6 h-6 text-white fill-white" />
        ) : (
          <Mic className="w-6 h-6 text-white" />
        )}
      </button>

      {isConnected && (
        <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
          <div className="flex items-center gap-2 text-xs font-medium">
            <div
              className={`w-2 h-2 rounded-full ${
                isAISpeaking
                  ? 'bg-green-500 animate-pulse'
                  : isRecording
                  ? 'bg-red-500 animate-ping'
                  : 'bg-gray-400'
              }`}
            />
            <span className={isRecording || isAISpeaking ? 'animate-pulse' : ''}>
              {isAISpeaking ? 'Ellen speaking...' : isRecording ? 'Listening...' : 'Connected'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
