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

  // Basic markdown-to-html for bold and code blocks
  const formatText = (text: string) => {
    let formattedText = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
      .replace(/`([^`]+)`/g, '<code class="bg-slate-800 text-sm rounded px-1 py-0.5">$1</code>'); // Inline code
    
    const codeBlockRegex = /```(\w*?)\n([\s\S]*?)```/g;
    formattedText = formattedText.replace(codeBlockRegex, (match, lang, code) => {
        return `<pre class="bg-slate-800 p-3 rounded-lg my-2 overflow-x-auto"><code class="language-${lang || ''}">${code.trim()}</code></pre>`;
    });

    return { __html: formattedText };
  };

  if (!message.text.trim() && !isUser) {
    return null; // Don't render empty model messages (placeholders)
  }

  return (
    <div className={`${containerClasses} group`}>
      <div className={`flex items-start space-x-3 max-w-lg ${contentOrder}`}>
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center mt-1">
          {icon}
        </div>
        <div className={`p-3.5 ${bubbleClasses} transition-opacity duration-300`}>
          <p className="text-base leading-relaxed whitespace-pre-wrap" dangerouslySetInnerHTML={formatText(message.text)}></p>
        </div>
      </div>
    </div>
  );
};

export default Message;