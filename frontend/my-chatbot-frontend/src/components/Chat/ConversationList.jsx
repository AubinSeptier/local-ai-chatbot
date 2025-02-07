export default function ConversationList({ conversations, currentConversationId, onSelectConversation }) {
    return (
      <div className="w-64 h-full bg-gray-100 dark:bg-gray-800 p-4 overflow-y-auto overflow-x-hidden">
        <button
          onClick={() => onSelectConversation(null)}
          className="w-full mb-4 p-2 bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-800 dark:hover:bg-indigo-900 text-white rounded-md"
        >
          New Chat
        </button>
        
        <div className="space-y-2">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => onSelectConversation(conv.id)}
              className={`p-2 cursor-pointer rounded truncate transition-colors ${
                currentConversationId === conv.id 
                  ? 'bg-indigo-800 text-white' 
                  : 'hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-300'
              }`}
              title={conv.title || 'New Conversation'}
            >
              {conv.title || 'New Conversation'}
            </div>
          ))}
        </div>
      </div>
    );
  }