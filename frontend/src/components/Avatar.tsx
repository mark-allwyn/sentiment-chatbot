import React from 'react';
import { SentimentState } from '../types';

interface AvatarProps {
  sentiment: SentimentState;
  isAudioPlaying?: boolean;
}

const Avatar: React.FC<AvatarProps> = ({ sentiment, isAudioPlaying = false }) => {
  const getColor = () => {
    switch (sentiment) {
      case SentimentState.POSITIVE:
        return '#4ade80';
      case SentimentState.NEGATIVE:
        return '#f87171';
      case SentimentState.NEUTRAL:
      default:
        return '#fb923c';
    }
  };

  const getLabel = () => {
    switch (sentiment) {
      case SentimentState.POSITIVE:
        return 'Positive';
      case SentimentState.NEGATIVE:
        return 'Negative';
      case SentimentState.NEUTRAL:
      default:
        return 'Neutral';
    }
  };

  const color = getColor();

  return (
    <div className={`relative w-48 h-48 mx-auto transition-all duration-500 ease-in-out transform hover:scale-105 ${
      isAudioPlaying ? 'animate-pulse' : ''
    }`}>
      <svg viewBox="0 0 200 200" className="w-full h-full drop-shadow-lg">
        <circle
          cx="100"
          cy="100"
          r="90"
          fill={color}
          className="transition-all duration-1000 ease-in-out"
        />
        <circle
          cx="100"
          cy="100"
          r="80"
          fill="white"
          opacity="0.1"
        />
      </svg>

      <div className={`absolute bottom-2 right-2 px-3 py-1 rounded-full text-xs font-bold text-white shadow-md transition-colors duration-500 ${
        sentiment === SentimentState.POSITIVE ? 'bg-green-600' :
        sentiment === SentimentState.NEGATIVE ? 'bg-red-500' : 'bg-orange-500'
      }`}>
        {getLabel()}
      </div>
    </div>
  );
};

export default Avatar;
