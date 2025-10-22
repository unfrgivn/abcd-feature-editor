import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ChatWindow from './components/ChatWindow';
import FeaturesTable from './components/FeaturesTable';
import { Feature } from './types';


function App() {
  const [view, setView] = useState<'table' | 'chat'>('table');
  const [features, setFeatures] = useState<Feature[]>([]);
  const [editingFeature, setEditingFeature] = useState<Feature | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchFeatures = async () => {
      try {
        setLoading(true);
        const response = await axios.get('http://127.0.0.1:8000/api/config.json');
        setFeatures(response.data);
      } catch (error) {
        console.error('Error fetching features:', error);
        // Fallback to initial features if API fails
      } finally {
        setLoading(false);
      }
    };

    fetchFeatures();
  }, []);

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
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400 mx-auto mb-4"></div>
              <p className="text-lg text-gray-300">Loading features...</p>
            </div>
          </div>
        ) : view === 'table' ? (
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