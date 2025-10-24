import React, { useState, useEffect } from 'react';
import { SessionVersion } from '../types';
import * as sessionService from '../services/sessionService';

interface VersionHistoryProps {
  sessionPk: number;
  onRollback?: (versionId: number, videoUrl: string | null) => void;
}

const VersionHistory: React.FC<VersionHistoryProps> = ({ sessionPk, onRollback }) => {
  const [versions, setVersions] = useState<SessionVersion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    const fetchVersions = async () => {
      try {
        setIsLoading(true);
        const versionList = await sessionService.getVersions(sessionPk);
        setVersions(versionList);
        setError(null);
      } catch (err) {
        console.error('Error fetching versions:', err);
        setError('Failed to load version history');
      } finally {
        setIsLoading(false);
      }
    };

    if (sessionPk) {
      fetchVersions();
    }
  }, [sessionPk]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleString();
  };

  const handleRollback = (version: SessionVersion) => {
    if (onRollback) {
      onRollback(version.id, version.video_url);
    }
  };

  if (versions.length === 0 && !isLoading) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm font-medium text-gray-900">Version History</span>
          {versions.length > 0 && (
            <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
              {versions.length}
            </span>
          )}
        </div>
        <svg 
          className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="border-t border-gray-200">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              Loading versions...
            </div>
          ) : error ? (
            <div className="p-4 text-center text-red-500 text-sm">
              {error}
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className="p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-sm font-medium text-gray-900">
                          Version {version.version_number}
                        </span>
                        {version.version_number === versions[versions.length - 1]?.version_number && (
                          <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">
                            Latest
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatDate(version.created_at)}
                      </div>
                      {version.video_url && (
                        <div className="mt-2">
                          <a
                            href={version.video_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:text-blue-800 underline"
                          >
                            View video
                          </a>
                        </div>
                      )}
                    </div>
                    {onRollback && version.version_number !== versions[versions.length - 1]?.version_number && (
                      <button
                        onClick={() => handleRollback(version)}
                        className="ml-4 px-3 py-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
                      >
                        Rollback
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VersionHistory;
