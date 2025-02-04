import { useState, useEffect, useRef } from 'react';
import { useChat } from '../../hooks/useChat';
import ConversationList from './ConversationList';
import ChatBubble from './ChatBubble';
import DarkModeToggle from './DarkModeToggle';

function useAutoScroll(messages) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "auto" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return messagesEndRef;
}

export default function ChatContainer({ onLogout, darkMode, toggleDarkMode }) {
  const [input, setInput] = useState('');
  
  // Initialiser useChat() EN PREMIER
  const { 
    messages, 
    isLoading, 
    error, 
    sendMessage,
    conversations,
    currentConversationId,
    selectConversation 
  } = useChat();

  // Maintenant messages est disponible
  const messagesEndRef = useAutoScroll(messages);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    await sendMessage(input);
    setInput('');
  };

  return (
    <div className="flex h-full">
      <DarkModeToggle darkMode={darkMode} toggleDarkMode={toggleDarkMode} className="absolute top-4 right-4" />
      
      {/* Sidebar */}
      <div className="w-64 bg-gray-100 dark:bg-gray-800 border-r dark:border-gray-700 overflow-y-auto custom-scrollbar">
        <div className="p-4">
          <button 
            onClick={onLogout}
            className="w-full mb-4 p-2 bg-red-600 text-white rounded-md hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800"
          >
            Logout
          </button>
        </div>
        <ConversationList 
          conversations={conversations}
          currentConversationId={currentConversationId}
          onSelectConversation={selectConversation}
        />
      </div>
      
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-auto p-4 custom-scrollbar">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((msg, index) => (
              <ChatBubble 
                key={index}
                message={msg.text}
                isUser={msg.isUser}
              />
            ))}
            {isLoading && (
              <div className="text-center text-gray-500 dark:text-gray-400">
                Bot is typing...
              </div>
            )}
            {error && (
              <div className="text-center text-red-500 dark:text-red-400">
                {error}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area - Fixed at bottom */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 p-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 bg-gray-100 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
              />
              <button
                type="submit"
                disabled={isLoading}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 dark:bg-blue-600 dark:hover:bg-blue-700"
              >
                Send
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}