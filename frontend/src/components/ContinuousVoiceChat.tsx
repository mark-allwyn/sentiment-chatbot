import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';

interface ContinuousVoiceChatProps {
  onMessage: (audioBlob: Blob) => Promise<void>;
  disabled?: boolean;
  isAIResponding?: boolean;
  silenceTimeout?: number; // Short silence to end turn (default: 3s)
  longSilenceTimeout?: number; // Long silence to end conversation (default: 30s)
}

export const ContinuousVoiceChat: React.FC<ContinuousVoiceChatProps> = ({
  onMessage,
  disabled,
  isAIResponding = false,
  silenceTimeout = 3000,
  longSilenceTimeout = 30000
}) => {
  const [isConversationActive, setIsConversationActive] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isWaitingForAI, setIsWaitingForAI] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const longSilenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const isConversationActiveRef = useRef<boolean>(false);

  // Detect silence in audio
  const detectSilence = () => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);

    // Calculate average volume
    const average = dataArray.reduce((a, b) => a + b) / bufferLength;

    console.log('Audio level:', average);

    // If volume is very low (silence)
    if (average < 5) {
      if (!silenceTimerRef.current) {
        console.log('Silence detected, starting timer...');
        silenceTimerRef.current = setTimeout(() => {
          console.log('Turn ended - silence timeout reached');
          endTurn();
        }, silenceTimeout);
      }
    } else {
      // Voice detected, clear short silence timer
      if (silenceTimerRef.current) {
        console.log('Voice detected, clearing silence timer');
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }

      // Also reset long silence timer
      if (longSilenceTimerRef.current) {
        clearTimeout(longSilenceTimerRef.current);
        longSilenceTimerRef.current = null;
      }
    }

    // Continue monitoring while recording
    animationFrameRef.current = requestAnimationFrame(detectSilence);
  };

  // Start long silence timer when waiting for user
  const startLongSilenceTimer = useCallback(() => {
    if (longSilenceTimerRef.current) {
      clearTimeout(longSilenceTimerRef.current);
    }

    longSilenceTimerRef.current = setTimeout(() => {
      console.log('Conversation ended - long silence');
      stopConversation();
    }, longSilenceTimeout);
  }, [longSilenceTimeout]);

  const startRecording = async () => {
    console.log('Starting recording...');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      console.log('Got media stream');

      // Set up audio analysis for silence detection
      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 2048;
      source.connect(analyserRef.current);

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        console.log('MediaRecorder stopped');
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        console.log('Audio blob size:', audioBlob.size, 'Conversation active:', isConversationActiveRef.current);
        audioChunksRef.current = [];

        // Only send if we have meaningful audio AND conversation is still active
        if (audioBlob.size > 1000 && isConversationActiveRef.current) {
          console.log('Sending audio to API...');
          setIsWaitingForAI(true);
          try {
            await onMessage(audioBlob);
            console.log('Audio sent successfully');
          } catch (error) {
            console.error('Error sending message:', error);
            // On error, stop the conversation
            stopConversation();
          } finally {
            setIsWaitingForAI(false);
          }
        } else {
          console.log('Not sending audio - too small or conversation inactive');
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      console.log('MediaRecorder started, isRecording set to true');

      // Start silence detection
      console.log('Starting silence detection...');
      detectSilence();

      // Start long silence timer
      console.log('Starting long silence timer...');
      startLongSilenceTimer();
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please check permissions.');
      stopConversation();
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }

    // Clear timers
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  };

  const endTurn = () => {
    stopRecording();
    // Will auto-resume after AI responds via useEffect
  };

  const stopConversation = () => {
    stopRecording();

    // Stop all tracks to release microphone
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    // Clean up audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Clear all timers
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    if (longSilenceTimerRef.current) {
      clearTimeout(longSilenceTimerRef.current);
      longSilenceTimerRef.current = null;
    }

    setIsConversationActive(false);
    isConversationActiveRef.current = false;
    setIsWaitingForAI(false);
  };

  const toggleConversation = () => {
    if (isConversationActive) {
      stopConversation();
    } else {
      setIsConversationActive(true);
      isConversationActiveRef.current = true;
      startRecording();
    }
  };

  // Auto-resume recording after AI finishes responding
  useEffect(() => {
    console.log('Auto-resume check:', {
      isConversationActive,
      isAIResponding,
      isRecording,
      isWaitingForAI
    });

    if (isConversationActive && !isAIResponding && !isRecording && !isWaitingForAI) {
      // Small delay to ensure audio playback has started
      const timer = setTimeout(() => {
        console.log('AI finished, resuming recording...');
        startRecording();
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [isAIResponding, isConversationActive, isRecording, isWaitingForAI]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopConversation();
    };
  }, []);

  const getStatusText = () => {
    if (isWaitingForAI || isAIResponding) {
      return 'Listening to Ellen...';
    }
    if (isRecording) {
      return 'Speak now...';
    }
    return 'Start conversation';
  };

  return (
    <div className="relative flex items-center justify-center">
      <button
        onClick={toggleConversation}
        disabled={disabled}
        className={`p-4 rounded-full transition-all duration-200 shadow-lg ${
          isConversationActive
            ? isRecording
              ? 'bg-red-500 hover:bg-red-600 ring-4 ring-red-300 animate-pulse'
              : 'bg-orange-500 hover:bg-orange-600 ring-4 ring-orange-300'
            : 'bg-purple-500 hover:bg-purple-600 hover:scale-105'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-label={isConversationActive ? 'Stop conversation' : 'Start conversation'}
        title={isConversationActive ? 'Click to stop conversation' : 'Click to start continuous conversation'}
      >
        {disabled ? (
          <Loader2 className="w-6 h-6 text-white animate-spin" />
        ) : isConversationActive ? (
          <Square className="w-6 h-6 text-white fill-white" />
        ) : (
          <Mic className="w-6 h-6 text-white" />
        )}
      </button>

      {isConversationActive && (
        <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
          <div className="flex items-center gap-2 text-xs font-medium">
            <div
              className={`w-2 h-2 rounded-full ${
                isRecording ? 'bg-red-500 animate-ping' : 'bg-orange-500 animate-pulse'
              }`}
            />
            <span className={isRecording ? 'text-red-500 animate-pulse' : 'text-orange-500'}>
              {getStatusText()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
