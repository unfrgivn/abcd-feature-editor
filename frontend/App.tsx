import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ChatWindow from './components/ChatWindow';
import FeaturesTable from './components/FeaturesTable';
import SessionList from './components/SessionList';
import { Feature, Session } from './types';
import * as sessionService from './services/sessionService';


function App() {
  const [view, setView] = useState<'table' | 'chat'>('table');
  const [features, setFeatures] = useState<Feature[]>([]);
  const [editingFeature, setEditingFeature] = useState<Feature | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const userId = 'demo-user';

  useEffect(() => {
    const fetchFeatures = async () => {
      try {
        setLoading(true);
        const response = await axios.get('http://127.0.0.1:8000/api/config.json');
        setFeatures(response.data);
      } catch (error) {
        console.error('Error fetching features:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFeatures();
  }, []);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const sessionsList = await sessionService.listSessions(userId);
        setSessions(sessionsList);
      } catch (error) {
        console.error('Error fetching sessions:', error);
      }
    };

    fetchSessions();
  }, [userId]);

  const handleStartEdit = async (feature: Feature) => {
    try {
      await axios.post('http://127.0.0.1:8000/api/cleanup');
      console.log('Session cleaned up successfully');
      
      const sessionId = `session-${Date.now()}`;
      const result = await sessionService.createSession(
        userId,
        sessionId,
        feature.videoId,
        feature.videoUrl,
        feature.id
      );
      
      const newSession = await sessionService.getSession(userId, sessionId);
      setCurrentSession(newSession);
      setSessions(prev => [newSession, ...prev]);
      
    } catch (error) {
      console.error('Error creating session:', error);
    }
    
    setEditingFeature(feature);
    setView('chat');
  };

  const handleSessionSelect = async (session: Session) => {
    try {
      const feature = features.find(f => f.id === session.feature_id);
      if (feature) {
        setCurrentSession(session);
        setEditingFeature(feature);
        setView('chat');
      }
    } catch (error) {
      console.error('Error selecting session:', error);
    }
  };

  const handleSessionDelete = async (sessionId: string) => {
    try {
      if (currentSession?.session_id === sessionId) {
        await axios.post('http://127.0.0.1:8000/api/cleanup');
        console.log('Active session cleaned up before deletion');
      }
      
      await sessionService.deleteSession(userId, sessionId);
      setSessions(prev => prev.filter(s => s.session_id !== sessionId));
      
      if (currentSession?.session_id === sessionId) {
        setCurrentSession(null);
        setEditingFeature(null);
        setView('table');
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const handleSessionRename = async (sessionId: string, newName: string) => {
    try {
      await sessionService.renameSession(userId, sessionId, newName);
      setSessions(prev =>
        prev.map(s => (s.session_id === sessionId ? { ...s, feature_id: newName } : s))
      );
      if (currentSession?.session_id === sessionId) {
        setCurrentSession(prev => prev ? { ...prev, feature_id: newName } : null);
      }
    } catch (error) {
      console.error('Error renaming session:', error);
    }
  };

  const handleNewSession = () => {
    setCurrentSession(null);
    setEditingFeature(null);
    setView('table');
  };

  const handleCloseChat = () => {
    setCurrentSession(null);
    setEditingFeature(null);
    setView('table');
  };

  const handleDeleteFeature = (featureId: string) => {
    setFeatures(prevFeatures => prevFeatures.filter(f => f.id !== featureId));
  };

  const handleToggleFixed = (featureId: string) => {
    setFeatures(prevFeatures => 
      prevFeatures.map(f => f.id === featureId ? { ...f, isFixed: !f.isFixed } : f)
    );
  };

  return (
    <div className="flex h-screen bg-white text-gray-900">
      <SessionList
        sessions={sessions}
        currentSessionId={currentSession?.session_id || null}
        onSessionSelect={handleSessionSelect}
        onSessionDelete={handleSessionDelete}
        onSessionRename={handleSessionRename}
        onNewSession={handleNewSession}
      />
      <aside className="w-16 bg-[#1a2b52] flex flex-col items-center py-4 space-y-6">
        <div className="w-10 h-10 bg-[#4a9eff] rounded-lg flex items-center justify-center text-white font-bold text-xl">
          IQ
        </div>
        <div className="flex-1 flex flex-col space-y-4 text-white/60">
          <button className="p-2 hover:text-white transition-colors" title="Dashboard">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
          </button>
          <button className="p-2 hover:text-white transition-colors" title="Analytics">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </button>
          <button className="p-2 bg-white/10 text-white rounded transition-colors" title="Creative Audit">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>
          <button className="p-2 hover:text-white transition-colors" title="Teams">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </button>
        </div>
        <button className="p-2 text-white/60 hover:text-white transition-colors" title="Settings">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </aside>
      
      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-semibold text-gray-900">Creative Audit</h1>
            <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="flex items-center space-x-3">
            <button className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
              Compare Creatives
            </button>
            <button className="px-4 py-2 bg-[#1a2b52] text-white rounded-lg text-sm font-medium hover:bg-[#152241] transition-colors">
              Upload New Creatives
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
        </header>
        
        <main className="flex-1 overflow-auto bg-gray-50">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-lg text-gray-600">Loading creatives...</p>
              </div>
            </div>
          ) : view === 'table' ? (
            <div className="p-6">
              <div className="mb-4">
                <h2 className="text-2xl font-semibold text-gray-900">My Creatives</h2>
              </div>
              <FeaturesTable 
                features={features}
                onEdit={handleStartEdit}
                onDelete={handleDeleteFeature}
                onToggleFixed={handleToggleFixed}
              />
            </div>
          ) : (
            <ChatWindow 
              featureToEdit={editingFeature} 
              onClose={handleCloseChat} 
              currentSession={currentSession}
              userId={userId}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;