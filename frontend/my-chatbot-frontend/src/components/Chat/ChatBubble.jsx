import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';

const ChatBubble = ({ message, isUser }) => (
  <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
    <div className={`rounded-lg px-4 py-2 max-w-[70%] prose ${
      isUser ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-100'
    }`}>
      <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
        {message}
      </ReactMarkdown>
    </div>
  </div>
);

export default ChatBubble;