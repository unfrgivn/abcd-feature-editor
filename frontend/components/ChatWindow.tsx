import React, { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { Message as MessageType, Role, Feature } from '../types';
import * as geminiService from '../services/geminiService';
import axios from 'axios';
import Message from './Message';
import ChatInput from './ChatInput';
import { XIcon } from './icons/XIcon';

interface ChatWindowProps {
  featureToEdit: Feature;
  onClose?: () => void;
}

const INITIAL_MESSAGE = 'Please make initial recommendations for improving the video based on the feature description provided.';

const ChatWindow: React.FC<ChatWindowProps> = ({ featureToEdit, onClose }) => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isTopPaneCollapsed, setIsTopPaneCollapsed] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isInitialized = useRef<boolean>(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeChat = useCallback(() => {
    try {
      geminiService.startChatSession();
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
    if(!isInitialized.current){
      isInitialized.current = true;
      handleSendMessage(INITIAL_MESSAGE);
    }
  }, [initializeChat]);


  const handleSendMessage = async (inputText: string) => {
    if (!inputText.trim() || isLoading) return;

    const newUserMessage: MessageType = { role: Role.USER, text: inputText };
    setMessages(prev => [...prev, newUserMessage, { role: Role.MODEL, text: '' }]);
    setIsLoading(true);

    try {
      const { data } = await axios.post(`http://127.0.0.1:8000/api/call_ai_editor_agent`, {
        query: inputText,
        feature_id: featureToEdit?.id,
      });
      
      console.log('DEBUG: Backend response type:', typeof data);
      console.log('DEBUG: Backend response:', data);
      
      let botMessage: MessageType;
      
      if (typeof data === 'object' && data.text) {
        botMessage = { 
          role: Role.MODEL, 
          text: data.text,
          media: data.media
        };
      } else if (typeof data === 'string') {
        try {
          const parsedData = JSON.parse(data);
          if (parsedData.text && parsedData.media) {
            botMessage = { 
              role: Role.MODEL, 
              text: parsedData.text,
              media: parsedData.media
            };
          } else {
            botMessage = { role: Role.MODEL, text: data };
          }
        } catch (e) {
          botMessage = { role: Role.MODEL, text: data };
        }
      } else {
        botMessage = { role: Role.MODEL, text: String(data) };
      }
      
      setMessages((prev) => [...prev.slice(0, -1), botMessage]);
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
    } else if (url.includes('storage.googleapis.com') || url.includes('creative-audit.prd.cdn.polaris.prd.ext.wpromote.com') || url.startsWith('gs://')) {
      let videoUrl = url;
      if (url.startsWith('gs://')) {
        const pathWithoutProtocol = url.substring(5);
        const bucketAndPath = pathWithoutProtocol.split('/');
        const bucketName = bucketAndPath[0];
        const pathOnly = bucketAndPath.slice(1).join('/');
        if (bucketName !== 'creative-audit-scratch-pad') {
          videoUrl = `https://creative-audit.prd.cdn.polaris.prd.ext.wpromote.com/${pathOnly}`;
        } else {
          videoUrl = `https://storage.googleapis.com/${pathWithoutProtocol}`;
        }
      } else if (url.includes('storage.googleapis.com')) {
        const match = url.match(/storage\.googleapis\.com\/([^\/]+)\/(.+)/);
        if (match && match[1] && match[2]) {
          const bucketName = match[1];
          const pathOnly = match[2];
          if (bucketName !== 'creative-audit-scratch-pad') {
            videoUrl = `https://creative-audit.prd.cdn.polaris.prd.ext.wpromote.com/${pathOnly}`;
          }
        }
      }
      return (
        <video className="w-full aspect-video rounded-lg bg-black" controls>
          <source src={videoUrl} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      );
    }
    return (
      <div className="w-full aspect-video rounded-lg bg-gray-100 flex items-center justify-center">
        <p className="text-gray-500">Video format not supported for preview.</p>
      </div>
    );
  };

  const filteredMessages = useMemo(
    () => messages.filter(msg => msg.text !== INITIAL_MESSAGE), 
    [messages]
  );

  const mockScores = () => {
    const hash = featureToEdit?.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) || 0;
    return {
      youtube: 52 + ((hash * 3) % 43),
    };
  };

  const scores = mockScores();

  const getScoreBadgeClass = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-[#9fcc3b]';
    if (score >= 40) return 'bg-orange-400';
    return 'bg-red-500';
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {featureToEdit && onClose && (
        <div className="px-6 py-4 bg-white border-b border-gray-200 flex justify-between items-center flex-shrink-0">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <button onClick={onClose} className="text-blue-600 hover:text-blue-800 font-medium">Overview</button>
            <span>/</span>
            <span className="text-gray-900 font-medium truncate max-w-md">{featureToEdit.name}</span>
          </div>
          <div className="flex items-center space-x-3">
            <button className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
              <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>
            <button className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
              Compare Creatives
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
        </div>
      )}
      
      {featureToEdit && (
        <div className="border-b border-gray-200 flex-shrink-0 bg-white">
          {!isTopPaneCollapsed && (
            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
                <div>
                  <div className="mb-3">
                    <div className="text-xs text-gray-500 uppercase mb-1">FILE NAME</div>
                    <h3 className="text-lg font-semibold text-gray-900">{featureToEdit.name}</h3>
                  </div>
                  <div className="mb-4">
                    <div className="text-xs text-gray-500 uppercase mb-1">UPLOADED</div>
                    <p className="text-sm text-gray-900">{featureToEdit.detected || 'Sep 26, 2025'}</p>
                  </div>
                  {renderVideoPlayer(featureToEdit.videoUrl)}
                </div>
                <div className="space-y-4">
                  <div className="flex items-center justify-center pb-6 border-b border-gray-200">
                    <div className="flex items-center space-x-2">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                      </svg>
                      <span className={`px-3 py-1 rounded-md text-sm font-semibold text-white ${getScoreBadgeClass(scores.youtube)}`}>
                        {scores.youtube}%
                      </span>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-semibold text-[#1a2b52] uppercase mb-2">Opportunity Summary</h4>
                    <p className="text-sm text-gray-700 leading-relaxed">{featureToEdit.llmExplanation}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
          <button
            onClick={() => setIsTopPaneCollapsed(!isTopPaneCollapsed)}
            className="w-full px-6 py-2 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-center border-t border-gray-200"
          >
            <svg
              className={`w-5 h-5 text-gray-400 transition-transform ${isTopPaneCollapsed ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          </button>
        </div>
      )}
      
      <div className="flex-grow p-6 space-y-6 overflow-y-auto bg-gray-50">
        {filteredMessages.map((msg, index) => (
          <Message key={index} message={msg} />
        ))}
        {isLoading && filteredMessages[filteredMessages.length - 1]?.text === '' && (
          <div className="flex justify-start">
             <div className="flex items-center space-x-2">
                 <div className="bg-white border border-gray-200 p-3 rounded-lg flex items-center space-x-2 shadow-sm">
                     <span className="h-2 w-2 bg-blue-500 rounded-full animate-pulse [animation-delay:-0.3s]"></span>
                     <span className="h-2 w-2 bg-blue-500 rounded-full animate-pulse [animation-delay:-0.15s]"></span>
                     <span className="h-2 w-2 bg-blue-500 rounded-full animate-pulse"></span>
                 </div>
             </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-6 bg-white border-t border-gray-200 flex-shrink-0">
        {error ? (
          <div className="text-center text-red-600 p-4 bg-red-50 rounded-lg border border-red-200">
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