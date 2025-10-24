import React from 'react';
import { CheckIcon } from './icons/CheckIcon';
import { XIcon } from './icons/XIcon';
import { Recommendation, RecommendationStatus } from '../types';
import ResponsiveVideoPlayer from './ResponsiveVideoPlayer';

interface RecommendationWorkflowProps {
  recommendations: Recommendation[];
  onAccept: (recommendationId: string) => void;
  onReject: (recommendationId: string) => void;
  onUndo: (recommendationId: string) => void;
  isLatestAccepted?: boolean;
}

const RecommendationWorkflow: React.FC<RecommendationWorkflowProps> = ({
  recommendations,
  onAccept,
  onReject,
  onUndo,
  isLatestAccepted = true,
}) => {
  const fixLegacyTitle = (rec: Recommendation): Recommendation => {
    if (rec.status === RecommendationStatus.PENDING) {
      if (rec.title === 'Video Edit Applied') {
        return { ...rec, title: 'Video Edit Recommendation' };
      }
      if (rec.title === 'Audio Generated') {
        return { ...rec, title: 'Audio Recommendation' };
      }
    }
    if (rec.status === RecommendationStatus.ACCEPTED) {
      if (rec.title === 'Video Edit Recommendation' || rec.title === 'Video Edit Applied') {
        return { ...rec, title: 'Video Edit Applied' };
      }
      if (rec.title === 'Audio Recommendation' || rec.title === 'Audio Generated') {
        return { ...rec, title: 'Audio Applied' };
      }
    }
    return rec;
  };

  const fixedRecommendations = recommendations.map(fixLegacyTitle);
  const pendingRecommendations = fixedRecommendations.filter(r => r.status === RecommendationStatus.PENDING);
  const acceptedRecommendations = fixedRecommendations.filter(r => r.status === RecommendationStatus.ACCEPTED);
  const rejectedRecommendations = fixedRecommendations.filter(r => r.status === RecommendationStatus.REJECTED);

  return (
    <div className="space-y-4">
      {acceptedRecommendations.length > 0 && (
        <div className="space-y-3 mb-4">
          <h3 className="text-xs font-semibold text-green-700 uppercase">Applied Changes</h3>
          {acceptedRecommendations.map((rec) => (
            <div
              key={rec.id}
              className="bg-green-50 border border-green-300 rounded-xl p-4 space-y-2"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <div className="mt-0.5">
                    <CheckIcon />
                  </div>
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-gray-900">{rec.title}</h4>
                    <p className="text-sm text-gray-700 mt-1">{rec.description}</p>
                    
                    {rec.metadata && (
                      <div className="mt-2 text-xs text-gray-600 space-y-1">
                        {rec.metadata.text && (
                          <div>
                            <span className="font-medium">Text:</span> {rec.metadata.text}
                          </div>
                        )}
                        {rec.metadata.audio_text && (
                          <div>
                            <span className="font-medium">Audio:</span> {rec.metadata.audio_text}
                          </div>
                        )}
                        {rec.metadata.position && (
                          <div>
                            <span className="font-medium">Position:</span> {rec.metadata.position}
                          </div>
                        )}
                        {rec.metadata.color && (
                          <div className="flex items-center gap-2">
                            <span className="font-medium">Color:</span>
                            <span>{rec.metadata.color}</span>
                            <div
                              className="w-4 h-4 rounded border border-gray-300"
                              style={{ backgroundColor: rec.metadata.color }}
                            />
                          </div>
                        )}
                      </div>
                     )}
                  </div>
                </div>
                
                <button
                  onClick={() => onUndo(rec.id)}
                  disabled={!isLatestAccepted}
                  className="ml-4 px-3 py-1 text-xs font-medium text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title={isLatestAccepted ? "Undo" : "Can only undo the most recent change"}
                >
                  Undo
                </button>
              </div>
              
              {rec.audioUrls && rec.audioUrls.length > 0 && (
                <div className="mt-3 space-y-2">
                  <p className="text-xs font-medium text-gray-600 uppercase">Audio Preview</p>
                  {rec.audioUrls.map((audioUrl, index) => (
                    <div key={index}>
                      <p className="text-xs text-gray-500 mb-1">Audio {index + 1}</p>
                      <audio controls className="w-full">
                        <source src={audioUrl} type="audio/mpeg" />
                        Your browser does not support the audio element.
                      </audio>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {pendingRecommendations.length > 0 && (
        <div className="space-y-3">
          {pendingRecommendations.map((rec) => (
            <div
              key={rec.id}
              className="bg-blue-50 border border-blue-200 rounded-xl p-4 space-y-3"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-gray-900">{rec.title}</h4>
                  <p className="text-sm text-gray-700 mt-1">{rec.description}</p>
                  
                  {rec.metadata && (
                    <div className="mt-2 text-xs text-gray-600 space-y-1">
                      {rec.metadata.text && (
                        <div>
                          <span className="font-medium">Text:</span> {rec.metadata.text}
                        </div>
                      )}
                      {rec.metadata.audio_text && (
                        <div>
                          <span className="font-medium">Audio:</span> {rec.metadata.audio_text}
                        </div>
                      )}
                      {rec.metadata.position && (
                        <div>
                          <span className="font-medium">Position:</span> {rec.metadata.position}
                        </div>
                      )}
                      {rec.metadata.color && (
                        <div className="flex items-center gap-2">
                          <span className="font-medium">Color:</span>
                          <span>{rec.metadata.color}</span>
                          <div
                            className="w-4 h-4 rounded border border-gray-300"
                            style={{ backgroundColor: rec.metadata.color }}
                          />
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => onAccept(rec.id)}
                    className="p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
                    title="Accept recommendation"
                  >
                    <CheckIcon />
                  </button>
                  <button
                    onClick={() => onReject(rec.id)}
                    className="p-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
                    title="Reject recommendation"
                  >
                    <XIcon />
                  </button>
                </div>
              </div>
              
              {rec.audioUrls && rec.audioUrls.length > 0 && (
                <div className="mt-3 space-y-2">
                  <p className="text-xs font-medium text-gray-600 uppercase">Audio Preview</p>
                  {rec.audioUrls.map((audioUrl, index) => (
                    <div key={index}>
                      <p className="text-xs text-gray-500 mb-1">Audio {index + 1}</p>
                      <audio controls className="w-full">
                        <source src={audioUrl} type="audio/mpeg" />
                        Your browser does not support the audio element.
                      </audio>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {recommendations.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">No recommendations yet. Start a conversation to get AI suggestions!</p>
        </div>
      )}
    </div>
  );
};

export default RecommendationWorkflow;
