from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.outputs import ChatGenerationChunk
import asyncio
from threading import Thread
from transformers import TextIteratorStreamer
from typing import Any, AsyncIterator, List

class CustomHuggingFaceChatModel(BaseChatModel):
    model: Any
    tokenizer: Any

    def __init__(self, model, tokenizer):
        super().__init__(model=model, tokenizer=tokenizer)

    def _generate(self, messages: List[HumanMessage], stop: List[str] | None = None, **kwargs):
        raise NotImplementedError("Utilisez les méthodes async instead")

    async def _astream(self, messages: List[HumanMessage], **kwargs) -> AsyncIterator[ChatGenerationChunk]:
        chat_history = []
        for message in messages:
            if isinstance(message, HumanMessage):
                chat_history.append({"role": "user", "content": message.content})
        
        messages_text = self.tokenizer.apply_chat_template(
            chat_history, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        model_inputs = self.tokenizer([messages_text], return_tensors="pt").to(self.model.device)
        
        streamer = TextIteratorStreamer(
            self.tokenizer, 
            skip_prompt=True, 
            skip_special_tokens=True
        )
        
        generate_kwargs = dict(
            **model_inputs,
            streamer=streamer,
            max_new_tokens=1024,
            do_sample=True,
            top_p=0.95,
            top_k=1000,
            temperature=0.75,
            num_beams=1,
        )
        
        thread = Thread(target=self.model.generate, kwargs=generate_kwargs)
        thread.start()

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
        return "custom-huggingface-chat-model"