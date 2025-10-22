import React, { useState, useRef, useEffect } from 'react';
import { SendIcon } from './icons/SendIcon';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading }) => {
  const [inputText, setInputText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputText]);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputText.trim()) {
      onSendMessage(inputText);
      setInputText('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e as unknown as React.FormEvent);
    }
  };


  return (
    <form onSubmit={handleSubmit} className="flex items-start space-x-3">
      <textarea
        ref={textareaRef}
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message here..."
        className="flex-1 bg-slate-800 border border-slate-600 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none max-h-48"
        rows={1}
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={isLoading || !inputText.trim()}
        className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg p-3 h-12 w-12 flex items-center justify-center disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed hover:from-blue-600 hover:to-blue-700 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-[#131316]"
      >
        <SendIcon />
      </button>
    </form>
  );
};

export default ChatInput;