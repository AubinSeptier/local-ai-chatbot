"""
Module principal de l'API de chat.
Gère les requêtes HTTP et le streaming des réponses du modèle.
"""

from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
import json
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
from model import CustomHuggingFaceChatModel
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from contextlib import redirect_stderr
from io import StringIO
from typing import List, Dict

app = Flask(__name__)
CORS(app)

# Configuration
MAX_HISTORY = 5  # Nombre maximum de messages dans l'historique

# Initialisation du modèle
with redirect_stderr(StringIO()):
    model = AutoModelForCausalLM.from_pretrained("./models/3b", torch_dtype=torch.float16)
    tokenizer = AutoTokenizer.from_pretrained("./models/3b")
llm = CustomHuggingFaceChatModel(model=model, tokenizer=tokenizer)

# Stockage des conversations (en mémoire)
conversations: Dict[str, List[dict]] = {}

def stream_response(message: str, conversation_id: str):
    """
    Génère une réponse en streaming pour un message donné.

    Args:
        message (str): Le message de l'utilisateur
        conversation_id (str): Identifiant unique de la conversation

    Yields:
        str: Les chunks de réponse formatés en SSE
    """
    async def run_generation():
        # Récupération de l'historique
        history = conversations.get(conversation_id, [])
        messages = []
        
        # Construction de la liste des messages pour le modèle
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # Ajout du message actuel
        messages.append(HumanMessage(content=message))
        
        # Génération de la réponse
        current_response = ""
        async for chunk in llm.astream(messages):
            if chunk.content.strip():
                current_response += chunk.content
                yield f"data: {json.dumps({'token': chunk.content, 'continuing': True})}\n\n"
        
        # Mise à jour de l'historique
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": current_response})
        
        # Limitation de l'historique
        if len(history) > MAX_HISTORY * 2:  # *2 car on compte les paires user/assistant
            history = history[-MAX_HISTORY * 2:]
        
        conversations[conversation_id] = history
        
        # Message de fin
        yield f"data: {json.dumps({'continuing': False})}\n\n"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        gen = run_generation()
        while True:
            try:
                response = loop.run_until_complete(gen.__anext__())
                yield response
            except StopAsyncIteration:
                break
    finally:
        loop.close()

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Point d'entrée de l'API pour le chat.
    Attend un JSON avec 'message' et 'conversation_id'.
    """
    try:
        data = request.get_json()
        message = data.get('message', '')
        conversation_id = data.get('conversation_id', 'default')
        
        if not message:
            return Response(
                f"data: {json.dumps({'error': 'Message is required', 'continuing': False})}\n\n",
                mimetype='text/event-stream'
            )
        
        return Response(
            stream_with_context(stream_response(message, conversation_id)),
            mimetype='text/event-stream'
        )
        
    except Exception as e:
        return Response(
            f"data: {json.dumps({'error': str(e), 'continuing': False})}\n\n",
            mimetype='text/event-stream'
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=True, use_reloader=False)