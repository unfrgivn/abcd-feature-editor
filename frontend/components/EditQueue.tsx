import React from 'react';
import { Edit, EditQueue as EditQueueType } from '../types';

interface EditQueueProps {
  editQueue: EditQueueType | null;
  onRemoveEdit?: (editId: string) => void;
  onReactivateEdit?: (editId: string) => void;
  onDeactivateEdit?: (editId: string) => void;
}

export const EditQueue: React.FC<EditQueueProps> = ({ 
  editQueue, 
  onRemoveEdit, 
  onReactivateEdit,
  onDeactivateEdit 
}) => {
  console.log('DEBUG EditQueue: Received editQueue:', editQueue);
  console.log('DEBUG EditQueue: Edit count:', editQueue?.edits?.length);
  console.log('DEBUG EditQueue: Edits:', editQueue?.edits?.map(e => ({
    id: e.id,
    type: e.type,
    status: e.status
  })));
  
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

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'applied':
        return '#4ade80';
      case 'overwritten':
        return '#666';
      case 'reverted':
        return '#888';
      case 'superseded':
        return '#777';
      case 'pending':
        return '#fbbf24';
      default:
        return '#999';
    }
  };

  const getStatusLabel = (status: string): string => {
    switch (status) {
      case 'applied':
        return 'Active';
      case 'overwritten':
        return 'Replaced';
      case 'reverted':
        return 'Deactivated';
      case 'superseded':
        return 'Modified';
      case 'pending':
        return 'Pending';
      default:
        return status;
    }
  };

  const activeCount = editQueue.edits.filter(e => e.status === 'applied').length;

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
        Edit Queue ({activeCount} active)
      </h3>
      
      <div className="edit-list" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {editQueue.edits.map((edit, index) => (
          <div
            key={edit.id}
            className="edit-item"
            style={{
              backgroundColor: edit.status === 'applied' ? '#2a2a2a' : '#252525',
              border: edit.status === 'applied' ? '1px solid #4ade80' : '1px solid #333',
              borderRadius: '6px',
              padding: '12px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              opacity: edit.status === 'applied' ? 1 : 0.6
            }}
          >
            <div style={{ flex: 1 }}>
              <div style={{ 
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '4px'
              }}>
                <span style={{ 
                  fontSize: '12px', 
                  color: '#888'
                }}>
                  #{index + 1} · {edit.type}
                </span>
                <span style={{
                  fontSize: '10px',
                  color: getStatusColor(edit.status),
                  backgroundColor: `${getStatusColor(edit.status)}22`,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontWeight: '600'
                }}>
                  {getStatusLabel(edit.status)}
                </span>
              </div>
              <div style={{ 
                fontSize: '13px', 
                color: '#e0e0e0'
              }}>
                {getEditDescription(edit)}
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: '8px' }}>
              {edit.status === 'applied' && (
                <>
                  {onDeactivateEdit && (
                    <button
                      onClick={() => onDeactivateEdit(edit.id)}
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
                        e.currentTarget.style.backgroundColor = '#444';
                        e.currentTarget.style.borderColor = '#888';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                        e.currentTarget.style.borderColor = '#666';
                      }}
                    >
                      Deactivate
                    </button>
                  )}
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
                </>
              )}
              
              {(edit.status === 'reverted' || edit.status === 'overwritten') && (
                <>
                  {onReactivateEdit && (
                    <button
                      onClick={() => onReactivateEdit(edit.id)}
                      style={{
                        backgroundColor: 'transparent',
                        border: '1px solid #4ade80',
                        borderRadius: '4px',
                        padding: '6px 12px',
                        color: '#4ade80',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.backgroundColor = '#4ade8033';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      Reactivate
                    </button>
                  )}
                  {onRemoveEdit && (
                    <button
                      onClick={() => onRemoveEdit(edit.id)}
                      style={{
                        backgroundColor: 'transparent',
                        border: '1px solid #666',
                        borderRadius: '4px',
                        padding: '6px 12px',
                        color: '#888',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.backgroundColor = '#ff4444';
                        e.currentTarget.style.borderColor = '#ff4444';
                        e.currentTarget.style.color = '#fff';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                        e.currentTarget.style.borderColor = '#666';
                        e.currentTarget.style.color = '#888';
                      }}
                    >
                      Delete
                    </button>
                  )}
                </>
              )}
              
              {edit.status === 'superseded' && onRemoveEdit && (
                <button
                  onClick={() => onRemoveEdit(edit.id)}
                  style={{
                    backgroundColor: 'transparent',
                    border: '1px solid #666',
                    borderRadius: '4px',
                    padding: '6px 12px',
                    color: '#888',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = '#ff4444';
                    e.currentTarget.style.borderColor = '#ff4444';
                    e.currentTarget.style.color = '#fff';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.borderColor = '#666';
                    e.currentTarget.style.color = '#888';
                  }}
                >
                  Delete
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
