import { useState, useEffect } from 'react';
import { chatApi } from '../api/chatApi';

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const response = await fetch('http://localhost:7860/api/conversations', {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Server error:', errorData);
        throw new Error(errorData.error || 'Failed to fetch conversations');
      }
      
      const data = await response.json();
      console.log('Fetched conversations:', data);
      
      if (data.conversations && Array.isArray(data.conversations)) {
        setConversations(data.conversations);
      } else {
        console.error('Invalid conversations format:', data);
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    }
  };

  const createNewConversation = async () => {
    try {
      const response = await fetch('http://localhost:7860/api/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title: 'New Conversation' })
      });
      if (response.ok) {
        const data = await response.json();
        setCurrentConversationId(data.conversation_id);
        setMessages([]);
        await fetchConversations();
        return data.conversation_id;
      }
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const generateTitle = async (conversationId, firstMessage) => {
    try {
      const response = await fetch(`http://localhost:7860/api/conversations/${conversationId}/title`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ first_message: firstMessage })
      });
      if (response.ok) {
        await fetchConversations();
      }
    } catch (error) {
      console.error('Failed to generate title:', error);
    }
  };

  const selectConversation = async (conversationId) => {
    try {
      if (!conversationId) {
        const newId = await createNewConversation();
        setCurrentConversationId(newId);
        setMessages([]);
        return;
      }
  
      setCurrentConversationId(conversationId);
      console.log(`Loading history for conversation: ${conversationId}`);
      
      const response = await fetch(`http://localhost:7860/api/conversations/${conversationId}/history`, {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error loading history:', errorData);
        throw new Error(errorData.error || 'Failed to load conversation history');
      }
      
      const data = await response.json();
      console.log('Received history:', data);
      
      if (data.history && Array.isArray(data.history)) {
        setMessages(data.history);
      } else {
        console.warn('No history found or invalid format:', data);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
      setMessages([]);
    }
  };

  const sendMessage = async (message) => {
    try {
      setIsLoading(true);
      setError(null);
      
      let currentId = currentConversationId;
      if (!currentId) {
        currentId = await createNewConversation();
      }
      
      setMessages(prev => [...prev, { text: message, isUser: true }]);
      
      let currentResponse = '';
      setMessages(prev => [...prev, { text: '', isUser: false }]);
      
      await chatApi.sendMessage(
        message,
        currentId,
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

      if (messages.length === 0) {
        await generateTitle(currentId, message);
      }
      
      await fetchConversations();
    } catch (err) {
      if (err.message === 'Unauthorized') {
        window.location.reload();
      }
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
    conversations,
    currentConversationId,
    selectConversation,
    createNewConversation
  };
};
