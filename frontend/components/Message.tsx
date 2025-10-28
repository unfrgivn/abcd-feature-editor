import React from 'react';
import { Message as MessageType, Role, Recommendation, RecommendationStatus } from '../types';
import { BotIcon } from './icons/BotIcon';
import { UserIcon } from './icons/UserIcon';
import { CheckIcon } from './icons/CheckIcon';
import { XIcon } from './icons/XIcon';
import ResponsiveVideoPlayer from './ResponsiveVideoPlayer';

interface MessageProps {
  message: MessageType;
  recommendation?: Recommendation;
  onAcceptRecommendation?: (id: string) => void;
  onRejectRecommendation?: (id: string) => void;
}

const Message: React.FC<MessageProps> = ({ message, recommendation, onAcceptRecommendation, onRejectRecommendation }) => {
  const isUser = message.role === Role.USER;
  const isAccepted = !isUser && recommendation?.status === RecommendationStatus.ACCEPTED;
  const activeRecommendation = isAccepted ? undefined : recommendation;
  const isPending = !isUser && activeRecommendation?.status === RecommendationStatus.PENDING;
  const isProcessing = !isUser && activeRecommendation?.status === RecommendationStatus.PROCESSING;
  const isRejected = !isUser && activeRecommendation?.status === RecommendationStatus.REJECTED;
  const isEditQueueSuccess = !isUser && message.isEditQueueSuccess;

  const containerClasses = isUser ? 'flex justify-end' : 'flex justify-start';
  
  let bubbleClasses = isUser
    ? 'bg-[#1a2b52] text-white rounded-2xl'
    : 'bg-white border border-gray-200 text-gray-900 rounded-2xl shadow-sm';
  
  let wrapperClasses = '';
  
  if (isPending) {
    bubbleClasses = 'bg-blue-50 border border-blue-200 text-gray-900 rounded-2xl shadow-sm';
  } else if (isProcessing) {
    bubbleClasses = 'bg-white text-gray-900 rounded-2xl shadow-sm relative';
    wrapperClasses = 'relative p-[2px] rounded-2xl bg-gradient-to-r from-blue-500 via-cyan-400 to-pink-400 bg-[length:200%_200%] animate-gradient-border';
  } else if (isRejected) {
    bubbleClasses = 'bg-red-50 border border-red-200 text-gray-900 rounded-2xl shadow-sm';
  } else if (isAccepted || isEditQueueSuccess) {
    bubbleClasses = 'bg-green-50 border border-green-200 text-gray-900 rounded-2xl shadow-sm';
  }
  
  const icon = isUser ? <UserIcon /> : <BotIcon />;
  const contentOrder = isUser ? 'flex-row-reverse' : 'flex-row';

  const formatText = (text: string) => {
    let formattedText = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code class="bg-gray-100 text-sm rounded px-1 py-0.5 text-gray-800">$1</code>');
    
    const codeBlockRegex = /```(\w*?)\n([\s\S]*?)```/g;
    formattedText = formattedText.replace(codeBlockRegex, (match, lang, code) => {
        return `<pre class="bg-gray-100 p-3 rounded-lg my-2 overflow-x-auto"><code class="language-${lang || ''}">${code.trim()}</code></pre>`;
    });

    return { __html: formattedText };
  };

  if (!message.text.trim() && !isUser && !message.media) {
    return null;
  }

  return (
    <div className={`${containerClasses} group`}>
      <div className={`flex items-start ${isUser ? 'space-x-3' : 'space-x-3'} max-w-3xl ${contentOrder}`}>
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 ${isUser ? 'bg-blue-600 ml-3' : 'bg-gray-200'}`}>
          {icon}
        </div>
        <div className="flex flex-col space-y-3 flex-1">
          {message.text.trim() && (
            <div className={wrapperClasses}>
              <div className={`px-4 py-3 ${bubbleClasses}`}>
                {isAccepted && (
                  <div className="flex items-center space-x-2 mb-2">
                    <CheckIcon />
                    <span className="text-xs font-semibold text-green-700 uppercase">Accepted</span>
                  </div>
                )}
                {isEditQueueSuccess && (
                  <div className="flex items-center space-x-2 mb-2">
                    <CheckIcon />
                    <span className="text-xs font-semibold text-green-700 uppercase">Done</span>
                  </div>
                )}
                {isProcessing && (
                  <div className="flex items-center space-x-2 mb-2">
                    <svg className="animate-spin h-4 w-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span className="text-xs font-semibold text-blue-700 uppercase">Processing...</span>
                  </div>
                )}
                {isRejected && (
                  <div className="flex items-center space-x-2 mb-2">
                    <XIcon />
                    <span className="text-xs font-semibold text-red-700 uppercase">Rejected</span>
                  </div>
                )}
                <p className="text-sm leading-relaxed whitespace-pre-wrap" dangerouslySetInnerHTML={formatText(message.text)}></p>
                {recommendation?.audioUrls && recommendation.audioUrls.length > 0 && (isPending || isProcessing) && (
                  <div className={`mt-3 space-y-2 pt-3 border-t ${isProcessing ? 'border-blue-300' : 'border-blue-300'}`}>
                    <p className="text-xs font-medium text-gray-600 uppercase">Audio Preview</p>
                    {recommendation.audioUrls.map((audioUrl, index) => (
                      <div key={index}>
                        <p className="text-xs text-gray-500 mb-1">Option {index + 1}</p>
                        <audio controls className="w-full h-10">
                          <source src={audioUrl} type="audio/mpeg" />
                          Your browser does not support the audio element.
                        </audio>
                      </div>
                    ))}
                  </div>
                )}
                {isPending && onAcceptRecommendation && onRejectRecommendation && recommendation && (
                  <div className="flex items-center space-x-2 mt-3 pt-3 border-t border-blue-300">
                    <button
                      onClick={() => onAcceptRecommendation(recommendation.id)}
                      className="px-3 py-1.5 bg-green-500 hover:bg-green-600 text-white text-xs font-medium rounded-lg transition-colors flex items-center space-x-1"
                      title="Accept recommendation"
                    >
                      <CheckIcon />
                      <span>Accept</span>
                    </button>
                    <button
                      onClick={() => onRejectRecommendation(recommendation.id)}
                      className="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs font-medium rounded-lg transition-colors flex items-center space-x-1"
                      title="Reject recommendation"
                    >
                      <XIcon />
                      <span>Reject</span>
                    </button>
                  </div>
                )}
                {isProcessing && (
                  <div className="mt-3 pt-3 border-t border-blue-300">
                    <div className="flex items-center space-x-2 text-xs text-blue-700">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>Applying changes and rendering new video...</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Message;