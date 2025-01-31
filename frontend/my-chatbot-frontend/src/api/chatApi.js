const API_BASE_URL = 'http://localhost:7860';

export const chatApi = {
  sendMessage: async (message, conversationId = 'default', onToken) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message,
          conversation_id: conversationId 
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value);
        const events = buffer.split('\n\n');
        
        // Garder le dernier événement s'il est incomplet
        buffer = events[events.length - 1];
        
        // Traiter tous les événements complets
        for (let i = 0; i < events.length - 1; i++) {
          const event = events[i].trim();
          if (event.startsWith('data: ')) {
            try {
              const data = JSON.parse(event.slice(5));
              if (data.token !== undefined && data.token !== '') {
                onToken(data.token);
              }
              // Ne pas traiter les messages vides
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
      throw new Error('Failed to send message');
    }
  }
};