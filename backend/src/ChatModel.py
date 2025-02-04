from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.outputs import ChatGenerationChunk
import asyncio
from threading import Thread
from transformers import TextIteratorStreamer, Pipeline
from typing import Any, AsyncIterator, List, Optional, Dict
from pydantic import Field

class CustomHuggingFaceChatModel(BaseChatModel):
    """
    A custom implementation of a Hugging Face chat model that supports token streaming.
    This class extends the BaseChatModel from LangChain to provide streaming capabilities
    with Hugging Face models.
    """
    pipeline: Pipeline = Field(..., description="Pipeline for text generation")
    generation_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_new_tokens": 1024,
            "do_sample": True,
            "top_p": 0.95,
            "top_k": 1000,
            "temperature": 0.75,
            "num_beams": 1,
        },
        description="Configuration for text generation"
    )

    async def _ainvoke(
        self,
        messages: List[HumanMessage],
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> AIMessageChunk:
        """
        Asynchronously invoke the model without streaming.
        
        Args:
            messages (List[HumanMessage]): List of messages in the conversation
            stop (Optional[List[str]]): List of stop sequences (not implemented)
            **kwargs: Additional arguments for generation

        Returns:
            AIMessageChunk: The complete generated response
        """
        # Collect all chunks into a single response
        chunks = []
        async for chunk in self._astream(messages, stop=stop, **kwargs):
            chunks.append(chunk.message.content)
        
        # Combine all chunks into a single message
        return AIMessageChunk(content="".join(chunks))

    def _generate(self, messages: List[HumanMessage], stop: Optional[List[str]] = None, **kwargs):
        """Not implemented as this model only supports async streaming."""
        raise NotImplementedError("Please use the async streaming method instead")

    async def _astream(
        self, 
        messages: List[HumanMessage], 
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> AsyncIterator[ChatGenerationChunk]:
        """
        Asynchronously stream the model's response.
        
        Args:
            messages (List[HumanMessage]): List of messages in the conversation
            stop (Optional[List[str]]): List of stop sequences (not implemented)
            **kwargs: Additional arguments for generation

        Yields:
            ChatGenerationChunk: Chunks of the generated response
        """
        # Convert messages to chat format
        chat_history = []
        for message in messages:
            if isinstance(message, HumanMessage):
                chat_history.append({"role": "user", "content": message.content})
        
        # Apply chat template
        messages_text = self.pipeline.tokenizer.apply_chat_template(
            chat_history, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Prepare model inputs
        model_inputs = self.pipeline.tokenizer(
            [messages_text], 
            return_tensors="pt"
        ).to(self.pipeline.model.device)
        
        # Setup streamer
        streamer = TextIteratorStreamer(
            self.pipeline.tokenizer, 
            skip_prompt=True, 
            skip_special_tokens=True
        )
        
        # Prepare generation configuration
        generate_kwargs = {
            **model_inputs,
            **self.generation_config,
            "streamer": streamer,
        }
        
        # Override with any kwargs provided
        if kwargs:
            generate_kwargs.update(kwargs)
        
        # Start generation in a separate thread
        thread = Thread(target=self.pipeline.model.generate, kwargs=generate_kwargs)
        thread.start()

        # Setup async streaming
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()

        def streamer_to_queue():
            try:
                for token in streamer:
                    if loop.is_closed():
                        break
                    asyncio.run_coroutine_threadsafe(
                        queue.put(token), 
                        loop=loop
                    )
                if not loop.is_closed():
                    asyncio.run_coroutine_threadsafe(queue.put(None), loop=loop)
            except RuntimeError:
                pass

        Thread(target=streamer_to_queue).start()

        # Stream tokens
        while True:
            token = await queue.get()
            if token is None:
                break
            yield ChatGenerationChunk(
                message=AIMessageChunk(content=token)
            )

        thread.join()

    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return "custom-huggingface-chat-model"