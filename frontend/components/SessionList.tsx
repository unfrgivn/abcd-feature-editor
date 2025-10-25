import React, { useState } from 'react';
import { Session } from '../types';
import { TrashIcon } from './icons/TrashIcon';
import { EditIcon } from './icons/EditIcon';

interface SessionListProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSessionSelect: (session: Session) => void;
  onSessionDelete: (sessionId: string) => void;
  onSessionRename?: (sessionId: string, newName: string) => void;
  onNewSession: () => void;
  onClearAllSessions?: () => void;
}

const SessionList: React.FC<SessionListProps> = ({
  sessions,
  currentSessionId,
  onSessionSelect,
  onSessionDelete,
  onSessionRename,
  onNewSession,
  onClearAllSessions,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const filteredSessions = sessions.filter(session => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      session.feature_id?.toLowerCase().includes(query) ||
      session.session_id.toLowerCase().includes(query)
    );
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  };

  return (
    <div className="bg-white border-r border-gray-200 flex flex-col" style={{ width: isExpanded ? '280px' : '60px' }}>
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        {isExpanded && <h2 className="font-semibold text-gray-900">Sessions</h2>}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title={isExpanded ? 'Collapse' : 'Expand'}
        >
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {isExpanded ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            )}
          </svg>
        </button>
      </div>

      {isExpanded && (
        <>
          <button
            onClick={onNewSession}
            className="m-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            + New Session
          </button>

          <div className="mx-3 mb-3 space-y-2">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search sessions..."
                className="w-full px-3 py-2 pr-8 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <svg 
                className="absolute right-2 top-2.5 w-4 h-4 text-gray-400" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            
            {sessions.length > 0 && onClearAllSessions && (
              <button
                onClick={() => setShowClearConfirm(true)}
                className="w-full px-3 py-2 text-sm text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
              >
                Clear All Sessions
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto">
            {filteredSessions.length === 0 ? (
              <div className="p-4 text-center text-gray-500 text-sm">
                {searchQuery ? 'No matching sessions' : 'No sessions yet'}
              </div>
            ) : (
              <div className="space-y-1 p-2">
                {filteredSessions.map((session) => (
                  <div
                    key={session.session_id}
                    className={`p-3 rounded-lg cursor-pointer transition-colors group ${
                      currentSessionId === session.session_id
                        ? 'bg-blue-50 border border-blue-200'
                        : 'hover:bg-gray-50 border border-transparent'
                    }`}
                    onClick={() => onSessionSelect(session)}
                  >
                     <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        {editingSessionId === session.session_id ? (
                          <input
                            type="text"
                            value={editingName}
                            onChange={(e) => setEditingName(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                if (editingName.trim() && onSessionRename) {
                                  onSessionRename(session.session_id, editingName.trim());
                                }
                                setEditingSessionId(null);
                              } else if (e.key === 'Escape') {
                                setEditingSessionId(null);
                              }
                            }}
                            onBlur={() => {
                              if (editingName.trim() && onSessionRename) {
                                onSessionRename(session.session_id, editingName.trim());
                              }
                              setEditingSessionId(null);
                            }}
                            className="w-full text-sm font-medium px-2 py-1 border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-300"
                            autoFocus
                            onClick={(e) => e.stopPropagation()}
                          />
                        ) : (
                          <>
                            <div className="text-sm font-medium text-gray-900 truncate">
                              {session.feature_id || 'Untitled Session'}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              {formatDate(session.updated_at)}
                            </div>
                          </>
                        )}
                      </div>
                      <div className="flex items-center gap-1 ml-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingSessionId(session.session_id);
                            setEditingName(session.feature_id || 'Untitled Session');
                          }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-blue-50 rounded"
                          title="Rename session"
                        >
                          <EditIcon className="w-4 h-4 text-blue-500" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSessionDelete(session.session_id);
                          }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-50 rounded"
                          title="Delete session"
                        >
                          <TrashIcon className="w-4 h-4 text-red-500" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {!isExpanded && sessions.length > 0 && (
        <div className="flex-1 overflow-y-auto">
          <div className="space-y-2 p-2">
            {sessions.map((session) => (
              <button
                key={session.session_id}
                onClick={() => onSessionSelect(session)}
                className={`w-full h-10 rounded-lg transition-colors ${
                  currentSessionId === session.session_id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                }`}
                title={session.feature_id || 'Untitled Session'}
              >
                <div className="text-xs font-medium">
                  {session.feature_id?.substring(0, 2).toUpperCase() || 'UN'}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {showClearConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Clear All Sessions?</h3>
            <p className="text-gray-600 mb-4">
              This will permanently delete all {sessions.length} session{sessions.length !== 1 ? 's' : ''}. This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="flex-1 px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  onClearAllSessions?.();
                  setShowClearConfirm(false);
                }}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionList;
