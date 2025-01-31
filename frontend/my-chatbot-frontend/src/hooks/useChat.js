import { useState } from 'react';
import { chatApi } from '../api/chatApi';

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId] = useState('default'); // ou générez un ID unique si nécessaire

  const sendMessage = async (message) => {
    try {
      setIsLoading(true);
      setError(null);
      
      setMessages(prev => [...prev, { text: message, isUser: true }]);
      
      let currentResponse = '';
      setMessages(prev => [...prev, { text: '', isUser: false }]);
      
      await chatApi.sendMessage(
        message,
        conversationId,
        (token) => {
          currentResponse += token;
          setMessages(prev => {
            const newMessages = [...prev];
            const lastIndex = newMessages.length - 1;
            newMessages[lastIndex] = {
              ...newMessages[lastIndex],
              text: currentResponse
            };
            return newMessages;
          });
        }
      );
    } catch (err) {
      setError('Failed to send message');
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    messages,
    isLoading,
    error,
    sendMessage,
  };
};