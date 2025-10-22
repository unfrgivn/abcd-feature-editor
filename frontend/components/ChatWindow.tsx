import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Message as MessageType, Role, Feature } from '../types';
import * as geminiService from '../services/geminiService';
import axios from 'axios';
import Message from './Message';
import ChatInput from './ChatInput';
import { XIcon } from './icons/XIcon';

interface ChatWindowProps {
  featureToEdit?: Feature | null;
  onClose?: () => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ featureToEdit = null, onClose }) => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeChat = useCallback(() => {
    try {
      if (featureToEdit) {
        geminiService.startChatSession(
          'You are an assistant that helps edit software features. The user will describe changes, and you should help them refine the feature name and description.'
        );
        setMessages([
          {
            role: Role.MODEL,
            text: `How would you like to update this feature?`,
          },
        ]);
      } else {
        geminiService.startChatSession();
        setMessages([
          {
            role: Role.MODEL,
            text: "Hello! I'm your Gemini AI assistant. How can I help you today?",
          },
        ]);
      }
      setError(null);
    } catch (e) {
      if (e instanceof Error) {
        setError(e.message);
        console.error(e);
      } else {
        setError("An unknown error occurred during initialization.");
        console.error(e);
      }
    }
  }, [featureToEdit]);

  useEffect(() => {
    initializeChat();
  }, [initializeChat]);


  const handleSendMessage = async (inputText: string) => {
    if (!inputText.trim() || isLoading) return;

    const newUserMessage: MessageType = { role: Role.USER, text: inputText };
    setMessages(prev => [...prev, newUserMessage, { role: Role.MODEL, text: '' }]);
    setIsLoading(true);

    try {
      const { data } = await axios.post(`http://127.0.0.1:8000/api/call_ai_editor_agent`, {
        query: inputText,
      });
      const botMessage: MessageType = { role: Role.MODEL, text: data };
      setMessages((prev) => [...prev, botMessage]);
      /*await geminiService.sendMessageStream(inputText, (chunk) => {
        setMessages(prevMessages => {
          const lastMessage = prevMessages[prevMessages.length - 1];
          if (lastMessage.role === Role.MODEL) {
            const updatedMessages = [...prevMessages];
            updatedMessages[prevMessages.length - 1] = {
              ...lastMessage,
              text: lastMessage.text + chunk,
            };
            return updatedMessages;
          }
          return prevMessages;
        });
      });*/
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'An unknown error occurred.';
      setMessages(prev => [...prev.slice(0, -1), { role: Role.MODEL, text: `Error: ${errorMessage}` }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const renderVideoPlayer = (url: string) => {
    if (url.includes('youtube.com/watch?v=')) {
      const videoId = url.split('v=')[1]?.split('&')[0];
      if (!videoId) return null;
      const embedUrl = `https://www.youtube.com/embed/${videoId}`;
      return (
        <iframe
          className="w-full aspect-video rounded-lg"
          src={embedUrl}
          title="YouTube video player"
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        ></iframe>
      );
    } else if (url.includes('storage.googleapis.com')) {
      return (
        <video className="w-full aspect-video rounded-lg bg-black" controls>
          <source src={url} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      );
    }
    return (
      <div className="w-full aspect-video rounded-lg bg-slate-900 flex items-center justify-center">
        <p className="text-slate-400">Video format not supported for preview.</p>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto flex flex-col h-full">
      {featureToEdit && onClose && (
        <div className="p-4 bg-slate-800/80 backdrop-blur-sm border-b border-slate-700 flex justify-between items-center flex-shrink-0">
          <h2 className="font-semibold text-lg truncate">
            Editing Feature: <span className="text-blue-400 font-bold">{featureToEdit.name}</span>
          </h2>
          <button 
            onClick={onClose} 
            className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold py-2 px-4 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900"
          >
            <XIcon />
            <span>Back to Features</span>
          </button>
        </div>
      )}
      
      {featureToEdit && (
        <div className="p-4 sm:p-6 border-b border-slate-700 flex-shrink-0">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <div>
              {renderVideoPlayer(featureToEdit.videoUrl)}
            </div>
            <div className="space-y-3">
              <h3 className="text-xl font-bold text-white">{featureToEdit.name}</h3>
              <p className="text-sm font-mono text-slate-400 bg-slate-800/50 rounded px-2 py-1 inline-block">{featureToEdit.videoId}</p>
              <p className="text-slate-300">{featureToEdit.llmExplanation}</p>
              <a href={featureToEdit.videoUrl} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 text-sm truncate block break-all">
                {featureToEdit.videoUrl}
              </a>
            </div>
          </div>
        </div>
      )}
      
      <div className="flex-grow p-4 sm:p-6 space-y-6 overflow-y-auto">
        {messages.map((msg, index) => (
          <Message key={index} message={msg} />
        ))}
        {isLoading && messages[messages.length - 1]?.text === '' && (
          <div className="flex justify-start">
             <div className="flex items-center space-x-2">
                 <div className="bg-slate-700 p-3 rounded-lg flex items-center space-x-2">
                     <span className="h-2 w-2 bg-blue-400 rounded-full animate-pulse [animation-delay:-0.3s]"></span>
                     <span className="h-2 w-2 bg-blue-400 rounded-full animate-pulse [animation-delay:-0.15s]"></span>
                     <span className="h-2 w-2 bg-blue-400 rounded-full animate-pulse"></span>
                 </div>
             </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 sm:p-6 bg-transparent border-t border-slate-700 flex-shrink-0">
        {error ? (
          <div className="text-center text-red-400 p-4 bg-red-900/50 rounded-lg">
            <strong>Initialization Error:</strong> {error}. Please check your API key and refresh.
          </div>
        ) : (
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        )}
      </div>
    </div>
  );
};

export default ChatWindow;