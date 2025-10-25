import React from 'react';
import { Edit, EditQueue as EditQueueType } from '../types';

interface EditQueueProps {
  editQueue: EditQueueType | null;
  onRemoveEdit?: (editId: string) => void;
}

export const EditQueue: React.FC<EditQueueProps> = ({ editQueue, onRemoveEdit }) => {
  if (!editQueue || editQueue.edits.length === 0) {
    return null;
  }

  const formatTime = (ms: number): string => {
    const seconds = ms / 1000;
    return `${seconds.toFixed(1)}s`;
  };

  const getEditDescription = (edit: Edit): string => {
    switch (edit.type) {
      case 'voiceover':
        return `Voiceover: "${edit.params.text}" at ${formatTime(edit.params.start_ms)}`;
      case 'text_overlay':
        return `Text: "${edit.params.text}" from ${formatTime(edit.params.start_ms)} to ${formatTime(edit.params.end_ms)}`;
      case 'trim':
        return `Trim: ${formatTime(edit.params.start_ms)} to ${formatTime(edit.params.end_ms)}`;
      case 'filter':
        return `Filter: ${edit.params.filter_type}`;
      default:
        return `Edit: ${edit.type}`;
    }
  };

  const appliedEdits = editQueue.edits.filter(e => e.status === 'applied');

  return (
    <div className="edit-queue-container" style={{
      backgroundColor: '#1e1e1e',
      border: '1px solid #333',
      borderRadius: '8px',
      padding: '16px',
      marginBottom: '16px'
    }}>
      <h3 style={{ 
        margin: '0 0 12px 0', 
        fontSize: '14px', 
        fontWeight: '600',
        color: '#fff'
      }}>
        Edit Queue ({appliedEdits.length} {appliedEdits.length === 1 ? 'edit' : 'edits'})
      </h3>
      
      <div className="edit-list" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {appliedEdits.map((edit, index) => (
          <div
            key={edit.id}
            className="edit-item"
            style={{
              backgroundColor: '#2a2a2a',
              border: '1px solid #444',
              borderRadius: '6px',
              padding: '12px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <div style={{ flex: 1 }}>
              <div style={{ 
                fontSize: '12px', 
                color: '#888',
                marginBottom: '4px'
              }}>
                #{index + 1} · {edit.type}
              </div>
              <div style={{ 
                fontSize: '13px', 
                color: '#e0e0e0'
              }}>
                {getEditDescription(edit)}
              </div>
            </div>
            
            {onRemoveEdit && (
              <button
                onClick={() => onRemoveEdit(edit.id)}
                style={{
                  backgroundColor: 'transparent',
                  border: '1px solid #666',
                  borderRadius: '4px',
                  padding: '6px 12px',
                  color: '#e0e0e0',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#ff4444';
                  e.currentTarget.style.borderColor = '#ff4444';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.borderColor = '#666';
                }}
              >
                Remove
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
