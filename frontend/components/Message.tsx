import React from 'react';
import { Message as MessageType, Role } from '../types';
import { BotIcon } from './icons/BotIcon';
import { UserIcon } from './icons/UserIcon';

interface MessageProps {
  message: MessageType;
}

const Message: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.role === Role.USER;

  const containerClasses = isUser ? 'flex justify-end' : 'flex justify-start';
  const bubbleClasses = isUser
    ? 'bg-[#1a2b52] text-white rounded-2xl'
    : 'bg-white border border-gray-200 text-gray-900 rounded-2xl shadow-sm';
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
            <div className={`px-4 py-3 ${bubbleClasses}`}>
              <p className="text-sm leading-relaxed whitespace-pre-wrap" dangerouslySetInnerHTML={formatText(message.text)}></p>
            </div>
          )}
          {message.media?.audio_urls && message.media.audio_urls.length > 0 && (
            <div className="bg-white border border-gray-200 p-4 rounded-xl space-y-3 shadow-sm">
              <p className="text-xs font-medium text-gray-600 uppercase">Generated Audio ({message.media.audio_urls.length})</p>
              {message.media.audio_urls.map((audioUrl, index) => (
                <div key={index}>
                  <p className="text-xs text-gray-500 mb-2 font-medium">Audio {index + 1}</p>
                  <audio controls className="w-full">
                    <source src={audioUrl} type="audio/mpeg" />
                    Your browser does not support the audio element.
                  </audio>
                </div>
              ))}
            </div>
          )}
          {message.media?.video_url && (
            <div className="bg-white border border-gray-200 p-4 rounded-xl shadow-sm">
              <p className="text-xs font-medium text-gray-600 uppercase mb-3">Edited Video</p>
              <video controls className="w-full rounded-lg">
                <source src={message.media.video_url} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Message;