from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.outputs import ChatGenerationChunk

from transformers import TextIteratorStreamer, Pipeline

from typing import Any, AsyncIterator, List, Dict
from pydantic import Field
import asyncio
from threading import Thread

class CustomHuggingFaceChatModel(BaseChatModel):
    """
    Custom chat model implementation for Hugging Face pipelines with streaming support.
    
    Attributes:
        pipeline: Hugging Face text generation pipeline
        generation_config: Configuration parameters for text generation
    """
    
    pipeline: Pipeline = Field(..., description="Hugging Face pipeline instance")
    generation_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_new_tokens": 1024,
            "temperature": 0.75,
            "top_p": 0.95,
            "top_k": 1000,
            "do_sample": True
        },
        description="Text generation configuration"
    )
    
    def _generate(self, messages: List[HumanMessage], stop: List[str] = None, **kwargs):
        """Not implemented as this model only supports async streaming."""
        raise NotImplementedError("Please use the async streaming method instead")
    
    async def _astream(
        self, 
        messages: List[HumanMessage], 
        **kwargs
    ) -> AsyncIterator[ChatGenerationChunk]:
        """
        Asynchronous streaming implementation for model responses.
        
        Args:
            messages: List of chat messages
            **kwargs: Additional generation parameters
            
        Yields:
            ChatGenerationChunk: Response chunks
        """
        # Prepare chat history
        chat_history = [{"role": "user", "content": msg.content} for msg in messages]
        
        # Format input with chat template
        prompt = self.pipeline.tokenizer.apply_chat_template(
            chat_history, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Tokenize inputs
        inputs = self.pipeline.tokenizer([prompt], return_tensors="pt").to(self.pipeline.model.device)
        
        # Configure streamer
        streamer = TextIteratorStreamer(
            self.pipeline.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        # Start generation thread
        thread = Thread(target=self.pipeline.model.generate, kwargs={
            **inputs,
            **self.generation_config,
            "streamer": streamer
        })
        thread.start()

        # Async streaming setup
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()

        def stream_to_queue():
            try:
                for token in streamer:
                    if not loop.is_closed():
                        asyncio.run_coroutine_threadsafe(queue.put(token), loop)
                asyncio.run_coroutine_threadsafe(queue.put(None), loop)
            except RuntimeError:
                pass

        Thread(target=stream_to_queue).start()

        # Yield tokens from queue
        while True:
            token = await queue.get()
            if token is None:
                break
            yield ChatGenerationChunk(message=AIMessageChunk(content=token))

        thread.join()

    @property
    def _llm_type(self) -> str:
        return "custom-huggingface-chat"