import React from 'react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex space-x-2 p-4 bg-white rounded-tr-2xl rounded-br-2xl rounded-bl-2xl w-fit shadow-sm border border-lavender-100 items-center h-12">
      <div className="w-2 h-2 bg-lavender-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
      <div className="w-2 h-2 bg-lavender-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
      <div className="w-2 h-2 bg-lavender-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
    </div>
  );
};
