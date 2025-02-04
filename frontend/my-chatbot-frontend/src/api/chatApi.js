// src/api/chatApi.js
const API_BASE_URL = 'http://localhost:7860';

export const chatApi = {
  sendMessage: async (message, conversationId = 'default', onToken) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important pour les cookies
        body: JSON.stringify({ 
          message,
          conversation_id: conversationId 
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Unauthorized');
        }
        throw new Error('API Error');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value);
        const events = buffer.split('\n\n');
        
        buffer = events[events.length - 1];
        
        for (let i = 0; i < events.length - 1; i++) {
          const event = events[i].trim();
          if (event.startsWith('data: ')) {
            try {
              const data = JSON.parse(event.slice(5));
              if (data.token !== undefined && data.token !== '') {
                onToken(data.token);
              }
              if (data.error) {
                onToken(`[Erreur] ${data.error}`);
              }
            } catch (e) {
              console.error('Erreur de parsing:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }
};