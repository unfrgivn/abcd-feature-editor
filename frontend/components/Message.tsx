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
    ? 'bg-blue-600 text-white rounded-l-xl rounded-t-xl'
    : 'bg-slate-800 text-slate-200 rounded-r-xl rounded-t-xl';
  const icon = isUser ? <UserIcon /> : <BotIcon />;
  const contentOrder = isUser ? 'flex-row-reverse' : 'flex-row';

  const formatText = (text: string) => {
    let formattedText = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code class="bg-slate-800 text-sm rounded px-1 py-0.5">$1</code>');
    
    const codeBlockRegex = /```(\w*?)\n([\s\S]*?)```/g;
    formattedText = formattedText.replace(codeBlockRegex, (match, lang, code) => {
        return `<pre class="bg-slate-800 p-3 rounded-lg my-2 overflow-x-auto"><code class="language-${lang || ''}">${code.trim()}</code></pre>`;
    });

    return { __html: formattedText };
  };

  if (!message.text.trim() && !isUser && !message.media) {
    return null;
  }

  return (
    <div className={`${containerClasses} group`}>
      <div className={`flex items-start space-x-3 max-w-2xl ${contentOrder}`}>
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center mt-1">
          {icon}
        </div>
        <div className="flex flex-col space-y-3">
          {message.text.trim() && (
            <div className={`p-3.5 ${bubbleClasses} transition-opacity duration-300`}>
              <p className="text-base leading-relaxed whitespace-pre-wrap" dangerouslySetInnerHTML={formatText(message.text)}></p>
            </div>
          )}
          {message.media?.audio_urls && message.media.audio_urls.length > 0 && (
            <div className="bg-slate-800 p-3 rounded-xl space-y-3">
              <p className="text-xs text-slate-400">Generated Audio ({message.media.audio_urls.length})</p>
              {message.media.audio_urls.map((audioUrl, index) => (
                <div key={index}>
                  <p className="text-xs text-slate-500 mb-1">Audio {index + 1}</p>
                  <audio controls className="w-full">
                    <source src={audioUrl} type="audio/mpeg" />
                    Your browser does not support the audio element.
                  </audio>
                </div>
              ))}
            </div>
          )}
          {message.media?.video_url && (
            <div className="bg-slate-800 p-3 rounded-xl">
              <p className="text-xs text-slate-400 mb-2">Edited Video</p>
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