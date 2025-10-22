import React, { useState } from 'react';
import ChatWindow from './components/ChatWindow';
import FeaturesTable from './components/FeaturesTable';
import { Feature } from './types';

const initialFeatures: Feature[] = [
  {
    id: 'a_supers',
    name: 'Supers',
    category: 'Attract',
    description: 'Any supers (text overlays) have been incorporated at any time in the video.',
    detected: false,
    llmExplanation: 'Feature not detected...',
    isFixed: false,
    videoId: 'VID-AUTH-101',
    videoUrl: 'https://www.youtube.com/watch?v=g_t-iI73k_c'
  },
  {
    id: 'a_supers_with_audio',
    name: 'Supers with Audio',
    category: 'Attract',
    description: 'The speech heard in the audio of the video matches OR is contextually supportive of the overlaid text shown on screen.',
    detected: false,
    llmExplanation: 'Feature not detected...',
    isFixed: false,
    videoId: 'VID-CHAT-201',
    videoUrl: 'gcs://bucket/videos/realtime-chat-demo.mp4'
  }
];


function App() {
  const [view, setView] = useState<'table' | 'chat'>('table');
  const [features, setFeatures] = useState<Feature[]>(initialFeatures);
  const [editingFeature, setEditingFeature] = useState<Feature | null>(null);

  const handleStartEdit = (feature: Feature) => {
    setEditingFeature(feature);
    setView('chat');
  };

  const handleCloseChat = () => {
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
    <div className="text-white min-h-screen font-sans">
      <header className="bg-slate-900/60 backdrop-blur-sm border-b border-slate-700 shadow-lg sticky top-0 z-10">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold text-center bg-gradient-to-r from-purple-400 to-blue-500 text-transparent bg-clip-text">
            AI Editor Agent - Feature Manager
          </h1>
        </div>
      </header>
      <main className="h-[calc(100vh-65px)]">
        {view === 'table' ? (
          <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <FeaturesTable 
              features={features}
              onEdit={handleStartEdit}
              onDelete={handleDeleteFeature}
              onToggleFixed={handleToggleFixed}
            />
          </div>
        ) : (
          <ChatWindow featureToEdit={editingFeature} onClose={handleCloseChat} />
        )}
      </main>
    </div>
  );
}

export default App;