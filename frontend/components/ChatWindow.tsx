import React, { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { Message as MessageType, Role, Feature, Recommendation, RecommendationStatus, Session, EditQueue as EditQueueType } from '../types';
import * as geminiService from '../services/geminiService';
import * as sessionService from '../services/sessionService';
import axios from 'axios';
import Message from './Message';
import ChatInput from './ChatInput';
import RecommendationWorkflow from './RecommendationWorkflow';
import ResponsiveVideoPlayer from './ResponsiveVideoPlayer';
import VersionHistory from './VersionHistory';
import { EditQueue } from './EditQueue';
import { XIcon } from './icons/XIcon';

interface ChatWindowProps {
  featureToEdit: Feature;
  onClose?: () => void;
  currentSession?: Session | null;
  userId?: string;
}

const INITIAL_MESSAGE = 'Please make initial recommendations for improving the video based on the feature description provided.';

const ChatWindow: React.FC<ChatWindowProps> = ({ featureToEdit, onClose, currentSession, userId = 'demo-user' }) => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isTopPaneCollapsed, setIsTopPaneCollapsed] = useState<boolean>(false);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [isProcessingRecommendation, setIsProcessingRecommendation] = useState<boolean>(false);
  const [currentVideoIndex, setCurrentVideoIndex] = useState<number>(0);
  const [videoHistory, setVideoHistory] = useState<string[]>([]);
  const [applyingRecommendationId, setApplyingRecommendationId] = useState<string | null>(null);
  const [editQueue, setEditQueue] = useState<EditQueueType | null>(null);
  const [isEditSidebarOpen, setIsEditSidebarOpen] = useState<boolean>(false);
  const [editQueuePulse, setEditQueuePulse] = useState<boolean>(false);
  const [isEditOperationLoading, setIsEditOperationLoading] = useState<boolean>(false);
  const applyingRecommendationIdRef = useRef<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isInitialized = useRef<boolean>(false);

  useEffect(() => {
    if (currentSession?.state) {
      const savedMessages = currentSession.state.messages as MessageType[] || [];
      const savedRecommendations = currentSession.state.recommendations as Recommendation[] || [];
      setMessages(savedMessages);
      setRecommendations(savedRecommendations);
      isInitialized.current = !!savedMessages.length;
      
      if (featureToEdit?.videoUrl) {
        const acceptedVideos = savedRecommendations
          .filter(r => r.status === RecommendationStatus.ACCEPTED && r.videoUrl)
          .map(r => r.videoUrl!);
        const history = [featureToEdit.videoUrl, ...acceptedVideos];
        setVideoHistory(history);
        setCurrentVideoIndex(history.length - 1);
      }
      
      fetchEditQueue();
    } else {
      setMessages([]);
      setRecommendations([]);
      isInitialized.current = false;
      if (featureToEdit?.videoUrl) {
        setVideoHistory([featureToEdit.videoUrl]);
        setCurrentVideoIndex(0);
      }
    }
  }, [currentSession?.session_id, featureToEdit?.videoUrl]);

  const fetchEditQueue = async () => {
    if (!currentSession) return;
    
    try {
      const response = await axios.get(`http://127.0.0.1:8000/api/sessions/edit-queue`, {
        params: {
          user_id: userId,
          session_id: currentSession.session_id,
        }
      });
      
      if (response.data) {
        const prevEditCount = editQueue?.edits?.length || 0;
        const newEditCount = response.data?.edits?.length || 0;
        
        console.log('DEBUG ChatWindow: Fetched edit queue:', response.data);
        console.log('DEBUG ChatWindow: Edit count:', newEditCount);
        console.log('DEBUG ChatWindow: Edits:', response.data.edits?.map((e: any) => ({
          id: e.id,
          type: e.type,
          status: e.status
        })));
        
        setEditQueue(response.data);
        
        if (newEditCount > prevEditCount) {
          setEditQueuePulse(true);
          setTimeout(() => setEditQueuePulse(false), 2000);
        }
      }
    } catch (error) {
      console.error('Error fetching edit queue:', error);
    }
  };

  useEffect(() => {
    if (currentSession && messages.length > 0) {
      const saveSession = async () => {
        try {
          await sessionService.updateSessionState(userId, currentSession.session_id, {
            messages,
            recommendations,
          });
          setSaveError(null);
        } catch (error) {
          console.error('Error saving session state:', error);
          setSaveError('Failed to save session. Changes may be lost.');
        }
      };
      saveSession();
    }
  }, [messages, recommendations, currentSession, userId]);

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
    if (!currentSession?.session_id) return;
    
    initializeChat();
    if(!isInitialized.current && messages.length === 0){
      isInitialized.current = true;
      handleSendMessage(INITIAL_MESSAGE);
    }
  }, [currentSession?.session_id]);


  const handleSendMessage = async (inputText: string) => {
    if (!inputText.trim() || isLoading) return;

    const newUserMessage: MessageType = { role: Role.USER, text: inputText };
    setMessages(prev => [...prev, newUserMessage, { role: Role.MODEL, text: '' }]);
    setIsLoading(true);

    try {
      console.log('DEBUG: applyingRecommendationId at start:', applyingRecommendationIdRef.current);
      
      const { data } = await axios.post(`http://127.0.0.1:8000/api/call_ai_editor_agent`, {
        query: inputText,
        feature_id: featureToEdit?.id,
        user_id: userId,
        session_id: currentSession?.session_id,
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
        
        const hasVideoUrl = data.media?.video_url;
        const hasAudioUrls = data.media?.audio_urls;
        const isQuestion = data.text.trim().endsWith('?');
        
        console.log('DEBUG: hasVideoUrl:', hasVideoUrl);
        console.log('DEBUG: hasAudioUrls:', hasAudioUrls);
        console.log('DEBUG: isQuestion:', isQuestion);
        
        if (hasAudioUrls || isQuestion) {
          console.log('DEBUG: Question or audio preview - creating PENDING recommendation');
          const filteredMessagesCount = messages.filter(msg => msg.text !== INITIAL_MESSAGE).length;
          const messageIndex = filteredMessagesCount;
          const newRec: Recommendation = {
            id: `rec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            title: hasAudioUrls ? 'Audio Recommendation' : 'Text Recommendation',
            description: data.text.substring(0, 100) + (data.text.length > 100 ? '...' : ''),
            status: RecommendationStatus.PENDING,
            videoUrl: data.media?.video_url,
            audioUrls: data.media?.audio_urls,
            messageIndex: messageIndex,
          };
          setRecommendations(prevRecs => {
            const isDuplicate = prevRecs.some(rec => {
              const sameVideo = rec.videoUrl === newRec.videoUrl && rec.videoUrl !== undefined;
              const sameAudio = JSON.stringify(rec.audioUrls) === JSON.stringify(newRec.audioUrls) && rec.audioUrls !== undefined;
              const sameDesc = rec.description === newRec.description;
              return sameDesc && (sameVideo || sameAudio);
            });
            return isDuplicate ? prevRecs : [...prevRecs, newRec];
          });
        } else if (hasVideoUrl) {
          console.log('DEBUG: Non-question message with video_url - adding to history and marking ACCEPTED');
          setVideoHistory(prev => [...prev, data.media.video_url]);
          setCurrentVideoIndex(prev => prev + 1);
          
          const filteredMessagesCount = messages.filter(msg => msg.text !== INITIAL_MESSAGE).length;
          const messageIndex = filteredMessagesCount;
          const newRec: Recommendation = {
            id: `rec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            title: 'Video Edit Applied',
            description: data.text.substring(0, 100) + (data.text.length > 100 ? '...' : ''),
            status: RecommendationStatus.ACCEPTED,
            videoUrl: data.media.video_url,
            messageIndex: messageIndex,
          };
          setRecommendations(prevRecs => [...prevRecs, newRec]);
          setRecommendations(prevRecs => {
            const isDuplicate = prevRecs.some(rec => {
              const sameVideo = rec.videoUrl === newRec.videoUrl && rec.videoUrl !== undefined;
              const sameAudio = JSON.stringify(rec.audioUrls) === JSON.stringify(newRec.audioUrls) && rec.audioUrls !== undefined;
              const sameDesc = rec.description === newRec.description;
              return sameDesc && (sameVideo || sameAudio);
            });
            return isDuplicate ? prevRecs : [...prevRecs, newRec];
          });
        }
      } else if (typeof data === 'string') {
        try {
          const parsedData = JSON.parse(data);
          if (parsedData.text && parsedData.media) {
            botMessage = { 
              role: Role.MODEL, 
              text: parsedData.text,
              media: parsedData.media
            };
            
            const hasVideoUrl = parsedData.media?.video_url;
            const hasAudioUrls = parsedData.media?.audio_urls;
            const isQuestion = parsedData.text.trim().endsWith('?');
            
            if (hasVideoUrl) {
              setVideoHistory(prev => {
                const newHistory = [...prev, parsedData.media.video_url];
                setCurrentVideoIndex(newHistory.length - 1);
                return newHistory;
              });
              
              const filteredMessagesCount = messages.filter(msg => msg.text !== INITIAL_MESSAGE).length;
              const messageIndex = filteredMessagesCount;
              const newRec: Recommendation = {
                id: `rec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                title: 'Video Edit Applied',
                description: parsedData.text.substring(0, 100) + (parsedData.text.length > 100 ? '...' : ''),
                status: RecommendationStatus.ACCEPTED,
                videoUrl: parsedData.media.video_url,
                messageIndex: messageIndex,
              };
              setRecommendations(prev => [...prev, newRec]);
              
              if (currentSession) {
                try {
                  await sessionService.createVersion(currentSession.pk, parsedData.media.video_url);
                } catch (error) {
                  console.error('Error creating version snapshot:', error);
                }
              }
            } else if (hasAudioUrls || isQuestion) {
              const filteredMessagesCount = messages.filter(msg => msg.text !== INITIAL_MESSAGE).length;
              const messageIndex = filteredMessagesCount;
              const newRec: Recommendation = {
                id: `rec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                title: hasAudioUrls ? 'Audio Recommendation' : 'Text Recommendation',
                description: parsedData.text.substring(0, 100) + (parsedData.text.length > 100 ? '...' : ''),
                status: RecommendationStatus.PENDING,
                videoUrl: parsedData.media?.video_url,
                audioUrls: parsedData.media?.audio_urls,
                messageIndex: messageIndex,
              };
              setRecommendations(prev => {
                const isDuplicate = prev.some(rec => 
                  rec.videoUrl === newRec.videoUrl && 
                  rec.description === newRec.description &&
                  rec.status === RecommendationStatus.PENDING
                );
                return isDuplicate ? prev : [...prev, newRec];
              });
            }
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
      
      fetchEditQueue();
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'An unknown error occurred.';
      setMessages(prev => [...prev.slice(0, -1), { role: Role.MODEL, text: `Error: ${errorMessage}` }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleAcceptRecommendation = async (recommendationId: string) => {
    setIsProcessingRecommendation(true);
    
    const recommendation = recommendations.find(r => r.id === recommendationId);
    console.log('DEBUG: handleAcceptRecommendation called for:', recommendationId);
    console.log('DEBUG: Recommendation:', recommendation);
    
    const messageIndex = recommendation?.messageIndex ?? -1;
    const relatedMessage = messageIndex >= 0 ? filteredMessages[messageIndex] : null;
    const isQuestion = relatedMessage?.text?.trim().endsWith('?') ?? false;
    
    console.log('DEBUG: messageIndex:', messageIndex);
    console.log('DEBUG: relatedMessage:', relatedMessage);
    console.log('DEBUG: isQuestion:', isQuestion);
    
    setRecommendations(prev => 
      prev.map(rec => 
        rec.id === recommendationId 
          ? { ...rec, status: RecommendationStatus.PROCESSING }
          : rec
      )
    );
    
    if (isQuestion) {
      console.log('DEBUG: Question detected, calling backend to apply change');
      setApplyingRecommendationId(recommendationId);
      applyingRecommendationIdRef.current = recommendationId;
      
      try {
        const { data } = await axios.post(`http://127.0.0.1:8000/api/call_ai_editor_agent`, {
          query: "Yes, please apply that change.",
          feature_id: featureToEdit?.id,
          user_id: userId,
          session_id: currentSession?.session_id,
        });
        
        console.log('DEBUG: Backend response after accepting:', data);
        
        if (data.media?.video_url) {
          setRecommendations(prev => 
            prev.map(rec => 
              rec.id === recommendationId 
                ? { ...rec, videoUrl: data.media.video_url, status: RecommendationStatus.ACCEPTED }
                : rec
            )
          );
          
          if (currentSession) {
            try {
              await sessionService.createVersion(currentSession.pk, data.media.video_url);
              setVideoHistory(prev => [...prev, data.media.video_url]);
              setCurrentVideoIndex(prev => prev + 1);
            } catch (error) {
              console.error('Error creating version snapshot:', error);
            }
          }
          
          const followUpMessage: MessageType = { 
            role: Role.MODEL, 
            text: "Great! I've applied the changes. Is there anything else you'd like me to adjust?"
          };
          setMessages(prev => [...prev, followUpMessage]);
          
          fetchEditQueue();
        } else {
          console.warn('DEBUG: No video_url in response, marking as ACCEPTED anyway');
          setRecommendations(prev => 
            prev.map(rec => 
              rec.id === recommendationId 
                ? { ...rec, status: RecommendationStatus.ACCEPTED }
                : rec
            )
          );
          
          const followUpMessage: MessageType = { 
            role: Role.MODEL, 
            text: data.text || "I've processed your request. Is there anything else you'd like me to adjust?"
          };
          setMessages(prev => [...prev, followUpMessage]);
        }
        
        setApplyingRecommendationId(null);
        applyingRecommendationIdRef.current = null;
      } catch (error) {
        console.error('Error applying recommendation:', error);
        setRecommendations(prev => 
          prev.map(rec => 
            rec.id === recommendationId 
              ? { ...rec, status: RecommendationStatus.PENDING }
              : rec
          )
        );
      } finally {
        setIsProcessingRecommendation(false);
      }
      
      return;
    }
    
    if (currentSession && recommendation?.videoUrl) {
      try {
        await sessionService.createVersion(currentSession.pk, recommendation.videoUrl);
        console.log('Version snapshot created for recommendation:', recommendationId);
        
        setVideoHistory(prev => [...prev, recommendation.videoUrl!]);
        setCurrentVideoIndex(prev => prev + 1);
        
        setRecommendations(prev => 
          prev.map(rec => 
            rec.id === recommendationId 
              ? { ...rec, status: RecommendationStatus.ACCEPTED }
              : rec
          )
        );
      } catch (error) {
        console.error('Error creating version snapshot:', error);
      }
    }
    
    setIsProcessingRecommendation(false);
  };

  const handleRejectRecommendation = (recommendationId: string) => {
    setRecommendations(prev => 
      prev.map(rec => 
        rec.id === recommendationId 
          ? { ...rec, status: RecommendationStatus.REJECTED }
          : rec
      )
    );
  };

  const handleUndoRecommendation = (recommendationId: string) => {
    const recommendation = recommendations.find(r => r.id === recommendationId);
    
    if (recommendation?.status === RecommendationStatus.ACCEPTED) {
      const acceptedRecs = recommendations.filter(r => r.status === RecommendationStatus.ACCEPTED);
      const isLatest = acceptedRecs[acceptedRecs.length - 1]?.id === recommendationId;
      
      if (!isLatest) {
        console.log('Cannot undo: not the most recent change');
        return;
      }
      
      if (recommendation.videoUrl && videoHistory.length > 1) {
        const indexToRemove = videoHistory.findIndex(url => url === recommendation.videoUrl);
        if (indexToRemove > 0) {
          setVideoHistory(prev => prev.filter((_, i) => i !== indexToRemove));
          setCurrentVideoIndex(prev => Math.max(0, prev - 1));
        }
      }
    }
    
    setRecommendations(prev => 
      prev.map(rec => 
        rec.id === recommendationId 
          ? { ...rec, status: RecommendationStatus.PENDING }
          : rec
      )
    );
  };

  const handleRemoveEdit = async (editId: string) => {
    if (!currentSession) return;
    
    setIsEditOperationLoading(true);
    
    const botMessage: MessageType = { 
      role: Role.MODEL, 
      text: 'Removing that edit and regenerating the video...'
    };
    setMessages(prev => [...prev, botMessage]);
    
    try {
      const response = await axios.post(`http://127.0.0.1:8000/api/call_ai_editor_agent`, {
        query: `Remove edit with ID ${editId}`,
        feature_id: featureToEdit?.id,
        user_id: userId,
        session_id: currentSession?.session_id,
      });
      
      console.log('Edit removed:', response.data);
      
      await fetchEditQueue();
      
      const isError = response.data.text?.toLowerCase().includes('error') || 
                      response.data.text?.toLowerCase().includes('not found');
      
      if (isError) {
        const errorMessage: MessageType = { 
          role: Role.MODEL, 
          text: response.data.text || 'Sorry, I encountered an error while removing that edit. Please try again.',
        };
        setMessages(prev => [...prev.slice(0, -1), errorMessage]);
      } else if (response.data.media?.video_url) {
        setVideoHistory(prev => {
          const newHistory = [...prev, response.data.media.video_url];
          setCurrentVideoIndex(newHistory.length - 1);
          return newHistory;
        });
        
        const successMessage: MessageType = { 
          role: Role.MODEL, 
          text: 'The edit has been removed and the video has been updated.',
          media: { video_url: response.data.media.video_url },
          isEditQueueSuccess: true
        };
        setMessages(prev => [...prev.slice(0, -1), successMessage]);
      } else {
        const successMessage: MessageType = { 
          role: Role.MODEL, 
          text: 'The edit has been removed from the queue.',
        };
        setMessages(prev => [...prev.slice(0, -1), successMessage]);
      }
    } catch (error) {
      console.error('Error removing edit:', error);
      const errorMessage: MessageType = { 
        role: Role.MODEL, 
        text: 'Sorry, I encountered an error while removing that edit. Please try again.',
      };
      setMessages(prev => [...prev.slice(0, -1), errorMessage]);
    } finally {
      setIsEditOperationLoading(false);
    }
  };

  const handleReactivateEdit = async (editId: string) => {
    if (!currentSession) return;
    
    setIsEditOperationLoading(true);
    
    const botMessage: MessageType = { 
      role: Role.MODEL, 
      text: 'Reactivating that edit and regenerating the video...'
    };
    setMessages(prev => [...prev, botMessage]);
    
    try {
      const response = await axios.post(`http://127.0.0.1:8000/api/call_ai_editor_agent`, {
        query: `Reactivate edit with ID ${editId}`,
        feature_id: featureToEdit?.id,
        user_id: userId,
        session_id: currentSession?.session_id,
      });
      
      console.log('Edit reactivated:', response.data);
      
      await fetchEditQueue();
      
      const isError = response.data.text?.toLowerCase().includes('error') || 
                      response.data.text?.toLowerCase().includes('not found');
      
      if (isError) {
        const errorMessage: MessageType = { 
          role: Role.MODEL, 
          text: response.data.text || 'Sorry, I encountered an error while reactivating that edit. Please try again.',
        };
        setMessages(prev => [...prev.slice(0, -1), errorMessage]);
      } else if (response.data.media?.video_url) {
        setVideoHistory(prev => {
          const newHistory = [...prev, response.data.media.video_url];
          setCurrentVideoIndex(newHistory.length - 1);
          return newHistory;
        });
        
        const successMessage: MessageType = { 
          role: Role.MODEL, 
          text: 'The edit has been reactivated and the video has been updated.',
          media: { video_url: response.data.media.video_url },
          isEditQueueSuccess: true
        };
        setMessages(prev => [...prev.slice(0, -1), successMessage]);
      } else {
        const successMessage: MessageType = { 
          role: Role.MODEL, 
          text: 'The edit has been reactivated.',
        };
        setMessages(prev => [...prev.slice(0, -1), successMessage]);
      }
    } catch (error) {
      console.error('Error reactivating edit:', error);
      const errorMessage: MessageType = { 
        role: Role.MODEL, 
        text: 'Sorry, I encountered an error while reactivating that edit. Please try again.',
      };
      setMessages(prev => [...prev.slice(0, -1), errorMessage]);
    } finally {
      setIsEditOperationLoading(false);
    }
  };

  const handleDeactivateEdit = async (editId: string) => {
    if (!currentSession) return;
    
    setIsEditOperationLoading(true);
    
    const botMessage: MessageType = { 
      role: Role.MODEL, 
      text: 'Deactivating that edit and regenerating the video...'
    };
    setMessages(prev => [...prev, botMessage]);
    
    try {
      const response = await axios.post(`http://127.0.0.1:8000/api/call_ai_editor_agent`, {
        query: `Deactivate edit with ID ${editId}`,
        feature_id: featureToEdit?.id,
        user_id: userId,
        session_id: currentSession?.session_id,
      });
      
      console.log('Edit deactivated:', response.data);
      
      await fetchEditQueue();
      
      const isError = response.data.text?.toLowerCase().includes('error') || 
                      response.data.text?.toLowerCase().includes('not found');
      
      if (isError) {
        const errorMessage: MessageType = { 
          role: Role.MODEL, 
          text: response.data.text || 'Sorry, I encountered an error while deactivating that edit. Please try again.',
        };
        setMessages(prev => [...prev.slice(0, -1), errorMessage]);
      } else if (response.data.media?.video_url) {
        setVideoHistory(prev => {
          const newHistory = [...prev, response.data.media.video_url];
          setCurrentVideoIndex(newHistory.length - 1);
          return newHistory;
        });
        
        const successMessage: MessageType = { 
          role: Role.MODEL, 
          text: 'The edit has been deactivated and the video has been updated.',
          media: { video_url: response.data.media.video_url },
          isEditQueueSuccess: true
        };
        setMessages(prev => [...prev.slice(0, -1), successMessage]);
      } else {
        const successMessage: MessageType = { 
          role: Role.MODEL, 
          text: 'The edit has been deactivated.',
        };
        setMessages(prev => [...prev.slice(0, -1), successMessage]);
      }
    } catch (error) {
      console.error('Error deactivating edit:', error);
      const errorMessage: MessageType = { 
        role: Role.MODEL, 
        text: 'Sorry, I encountered an error while deactivating that edit. Please try again.',
      };
      setMessages(prev => [...prev.slice(0, -1), errorMessage]);
    } finally {
      setIsEditOperationLoading(false);
    }
  };

  const handleExportVideo = async () => {
    if (!currentSession) {
      console.error('No active session for export');
      return;
    }

    const acceptedRec = recommendations.find(
      rec => rec.status === RecommendationStatus.ACCEPTED && rec.videoUrl
    );

    if (!acceptedRec?.videoUrl) {
      console.error('No accepted recommendation with video to export');
      return;
    }

    try {
      setIsExporting(true);
      const response = await axios.post(
        'http://127.0.0.1:8000/api/export',
        null,
        {
          params: {
            video_path: acceptedRec.videoUrl,
            user_id: userId,
            feature_id: featureToEdit.id,
            video_id: featureToEdit.videoId,
          },
        }
      );
      
      console.log('Video exported:', response.data);
      alert(`Video exported successfully! URL: ${response.data.public_url}`);
    } catch (error) {
      console.error('Error exporting video:', error);
      alert('Failed to export video. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };
  

  const filteredMessages = useMemo(() => {
    return messages
      .filter(msg => msg.text !== INITIAL_MESSAGE);
  }, [messages]);

  const mockScores = () => {
    const hash = featureToEdit?.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) || 0;
    return {
      meta: 55 + (hash % 33),
      tiktok: 50 + ((hash * 2) % 45),
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

  const handlePreviousVideo = () => {
    if (currentVideoIndex > 0) {
      setCurrentVideoIndex(prev => prev - 1);
    }
  };

  const handleNextVideo = () => {
    if (currentVideoIndex < videoHistory.length - 1) {
      setCurrentVideoIndex(prev => prev + 1);
    }
  };

  const getCurrentVideoUrl = () => {
    return videoHistory[currentVideoIndex] || featureToEdit.videoUrl;
  };

  const getVideoLabel = () => {
    if (currentVideoIndex === 0) return 'Original';
    if (isProcessingRecommendation && currentVideoIndex === videoHistory.length - 1) return 'Processing...';
    if (currentVideoIndex === videoHistory.length - 1) return 'Current';
    return `Version ${currentVideoIndex}`;
  };

  const activeEditCount = useMemo(() => {
    return editQueue?.edits?.filter(edit => edit.status === 'applied').length || 0;
  }, [editQueue]);

  const getCombinedTimeline = useMemo(() => {
    console.log('DEBUG getCombinedTimeline: messages.length=', messages.length);
    console.log('DEBUG getCombinedTimeline: filteredMessages.length=', filteredMessages.length);
    console.log('DEBUG getCombinedTimeline: recommendations.length=', recommendations.length);
    
    const timeline: Array<{ type: 'message' | 'recommendation'; data: MessageType | Recommendation; order: number; isLatestAcceptedUndoable?: boolean }> = [];
    
    const messagesWithoutInitial = messages.filter(msg => msg.text !== INITIAL_MESSAGE);
    console.log('DEBUG getCombinedTimeline: messagesWithoutInitial.length=', messagesWithoutInitial.length);
    
    messagesWithoutInitial.forEach((msg, index) => {
      const filteredMsg = filteredMessages[index];
      console.log(`DEBUG getCombinedTimeline: index=${index}, filteredMsg=`, filteredMsg);
      if (filteredMsg) {
        timeline.push({ type: 'message', data: filteredMsg, order: index * 2 });
      }
      
      const msgRecommendation = recommendations.find(rec => rec.messageIndex === index);
      
      if (msgRecommendation) {
        timeline.push({ type: 'recommendation', data: msgRecommendation, order: index * 2 + 1 });
      }
    });
    
    console.log('DEBUG getCombinedTimeline: timeline.length=', timeline.length);
    
    const sortedTimeline = timeline.sort((a, b) => a.order - b.order);
    
    const lastItem = sortedTimeline[sortedTimeline.length - 1];
    if (lastItem && lastItem.type === 'recommendation') {
      const rec = lastItem.data as Recommendation;
      if (rec.status === RecommendationStatus.ACCEPTED) {
        const acceptedRecs = recommendations.filter(r => r.status === RecommendationStatus.ACCEPTED);
        const isLatestAccepted = acceptedRecs[acceptedRecs.length - 1]?.id === rec.id;
        lastItem.isLatestAcceptedUndoable = isLatestAccepted;
      }
    }
    
    return sortedTimeline;
  }, [messages, filteredMessages, recommendations]);

  return (
    <div className="flex h-full bg-white">
      {featureToEdit && (
        <div className="w-80 border-r border-gray-200 flex flex-col flex-shrink-0 bg-white">
          <div className="px-4 py-3 border-b border-gray-200">
            <div className="text-xs text-gray-500 uppercase mb-1">Preview</div>
            <h3 className="text-sm font-semibold text-gray-900 truncate">{featureToEdit.name}</h3>
          </div>
          
          <div className="p-4 overflow-y-auto flex-1">
            <div className="mb-4">
              <div className="relative">
                {(isProcessingRecommendation && currentVideoIndex === videoHistory.length - 1) || isEditOperationLoading ? (
                  <div className="absolute inset-0 bg-black bg-opacity-50 rounded-lg flex items-center justify-center z-10">
                    <div className="text-white text-sm font-medium flex items-center space-x-2">
                      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>{isEditOperationLoading ? 'Updating video...' : 'Processing...'}</span>
                    </div>
                  </div>
                ) : null}
                <ResponsiveVideoPlayer url={getCurrentVideoUrl()} key={getCurrentVideoUrl()} />
              </div>
              
              {videoHistory.length > 1 && (
                <div className="mt-3 flex items-center justify-between bg-gray-100 rounded-lg p-2">
                  <button
                    onClick={handlePreviousVideo}
                    disabled={currentVideoIndex === 0}
                    className="p-1 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    title="Previous version"
                  >
                    <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-medium text-gray-700">{getVideoLabel()}</span>
                    <span className="text-xs text-gray-500">({currentVideoIndex + 1}/{videoHistory.length})</span>
                  </div>
                  
                  <button
                    onClick={handleNextVideo}
                    disabled={currentVideoIndex === videoHistory.length - 1}
                    className="p-1 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    title="Next version"
                  >
                    <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              )}
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between space-x-4 pb-4 border-b border-gray-200">
                <div className="flex flex-col items-center flex-1">
                  <svg className="w-4 h-4 mb-1" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M22.675 0h-21.35c-.732 0-1.325.593-1.325 1.325v21.351c0 .731.593 1.324 1.325 1.324h11.495v-9.294h-3.128v-3.622h3.128v-2.671c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.795.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.313h3.587l-.467 3.622h-3.12v9.293h6.116c.73 0 1.323-.593 1.323-1.325v-21.35c0-.732-.593-1.325-1.325-1.325z"/>
                  </svg>
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold text-white ${getScoreBadgeClass(scores.meta)}`}>
                    {scores.meta}%
                  </span>
                </div>
                <div className="flex flex-col items-center flex-1">
                  <svg className="w-4 h-4 mb-1" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12.53.02C13.84 0 15.14.01 16.44 0c.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
                  </svg>
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold text-white ${getScoreBadgeClass(scores.tiktok)}`}>
                    {scores.tiktok}%
                  </span>
                </div>
                <div className="flex flex-col items-center flex-1">
                  <svg className="w-4 h-4 mb-1" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                  </svg>
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold text-white ${getScoreBadgeClass(scores.youtube)}`}>
                    {scores.youtube}%
                  </span>
                </div>
              </div>
              
              <div>
                <h4 className="text-xs font-semibold text-[#1a2b52] uppercase mb-2">Opportunity Summary</h4>
                <p className="text-xs text-gray-700 leading-relaxed">{featureToEdit.llmExplanation}</p>
              </div>
              
              <div>
                <div className="text-xs text-gray-500 uppercase mb-1">UPLOADED</div>
                <p className="text-xs text-gray-900">{featureToEdit.detected || 'Sep 26, 2025'}</p>
              </div>
            </div>
            
            {currentSession && (
              <div className="mt-4">
                <VersionHistory 
                  sessionPk={currentSession.pk}
                  onRollback={(versionId, videoUrl) => {
                    console.log('Rollback to version:', versionId, videoUrl);
                  }}
                />
              </div>
            )}
          </div>
        </div>
      )}
      
      <div className="flex-1 flex flex-col min-w-0 bg-white">
        {featureToEdit && onClose && (
          <div className="px-6 py-4 bg-white border-b border-gray-200 flex justify-between items-center flex-shrink-0">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <button onClick={onClose} className="text-blue-600 hover:text-blue-800 font-medium">Overview</button>
              <span>/</span>
              <span className="text-gray-900 font-medium truncate max-w-md">{featureToEdit.name}</span>
            </div>
            <div className="flex items-center space-x-3">
              <button 
                onClick={handleExportVideo}
                disabled={isExporting || !recommendations.some(r => r.status === RecommendationStatus.ACCEPTED && r.videoUrl)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                {isExporting ? 'Exporting...' : 'Export'}
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
              <button 
                onClick={() => setIsEditSidebarOpen(!isEditSidebarOpen)}
                className={`relative p-2 rounded-lg transition-colors ${isEditSidebarOpen ? 'bg-blue-50 text-blue-600' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'}`}
                title="Edit History"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                {activeEditCount > 0 && (
                  <span className={`absolute -top-1 -right-1 bg-green-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center ${editQueuePulse ? 'animate-pulse' : ''}`}>
                    {activeEditCount}
                  </span>
                )}
              </button>
            </div>
          </div>
        )}
        
        <div className="flex-grow p-6 space-y-6 overflow-y-auto bg-gray-50">
          {saveError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-sm text-red-700">{saveError}</span>
              </div>
              <button 
                onClick={() => setSaveError(null)}
                className="text-red-500 hover:text-red-700"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
          
          {getCombinedTimeline.map((item, index) => {
            console.log('DEBUG render: item.type=', item.type, 'index=', index);
            if (item.type === 'message') {
              const msgData = item.data as MessageType;
              console.log('DEBUG render: msgData=', msgData);
              const messageIndexInList = filteredMessages.findIndex(m => m === msgData);
              const linkedRec = recommendations.find(rec => rec.messageIndex === messageIndexInList);
              
              return (
                <Message 
                  key={`msg-${index}`} 
                  message={msgData}
                  recommendation={linkedRec}
                  onAcceptRecommendation={handleAcceptRecommendation}
                  onRejectRecommendation={handleRejectRecommendation}
                />
              );
            }
            return null;
          })}
          {isLoading && filteredMessages[filteredMessages.length - 1]?.text === '' && (
            <div className="flex justify-start">
               <div className="flex items-center space-x-2">
                   <div className="bg-white border border-gray-200 p-3 rounded-lg flex items-center space-x-2 shadow-sm">
                       <span className="text-sm text-blue-500">Maximizing Google Ad Revenue</span>
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

      {isEditSidebarOpen && (
        <div className="w-96 border-l border-gray-200 flex flex-col flex-shrink-0 bg-white">
          <div className="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
            <div>
              <div className="text-xs text-gray-500 uppercase mb-1">Edit History</div>
              <h3 className="text-sm font-semibold text-gray-900">
                {activeEditCount} Active {activeEditCount === 1 ? 'Edit' : 'Edits'}
              </h3>
            </div>
            <button 
              onClick={() => setIsEditSidebarOpen(false)}
              className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
            >
              <XIcon className="w-5 h-5" />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4">
            <EditQueue 
              editQueue={editQueue} 
              onRemoveEdit={handleRemoveEdit}
              onReactivateEdit={handleReactivateEdit}
              onDeactivateEdit={handleDeactivateEdit}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatWindow;