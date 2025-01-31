import { useState } from 'react';
import { useChat } from '../../hooks/useChat';

const ChatBubble = ({ message, isUser }) => (
  <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
    <div className={`rounded-lg px-4 py-2 max-w-[70%] ${
      isUser ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'
    }`}>
      {message}
    </div>
  </div>
);

export default function ChatContainer() {
  const [input, setInput] = useState('');
  const { messages, isLoading, error, sendMessage } = useChat();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    await sendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto p-4">
      <div className="flex-1 overflow-auto mb-4 space-y-4">
        {messages.map((msg, index) => (
          <ChatBubble 
            key={index}
            message={msg.text}
            isUser={msg.isUser}
          />
        ))}
        {isLoading && (
          <div className="text-center text-gray-500">
            Bot is typing...
          </div>
        )}
        {error && (
          <div className="text-center text-red-500">
            {error}
          </div>
        )}
      </div>
      
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 p-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
        >
          Send
        </button>
      </form>
    </div>
  );
}