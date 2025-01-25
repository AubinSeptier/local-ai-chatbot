from model import Model
from conversation import Conversation

from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFacePipeline

from transformers import pipeline
import torch

def download_model(llm_name: str):
    llm = Model()
    llm.save_model(llm_name)

def setup_chatbot(llm_name: str):
    llm = Model()
    llm.load_model(llm_name)
    
    device = 0 if torch.cuda.is_available() else -1
    print(device)

    pipe = pipeline(
        "text-generation",
        model=llm.get_model(),
        tokenizer=llm.get_tokenizer(),
        max_new_tokens=64,
        temperature=0.7,
        device=device
    )

    chatbot = HuggingFacePipeline(pipeline=pipe)
    
    return chatbot
    
    
if __name__ == "__main__":
    download_model("meta-llama/Llama-3.2-1B")
    chatbot = setup_chatbot("meta-llama/Llama-3.2-1B")
    chat = Conversation(chatbot, "test")
    chat.start_chat()
    chat.chat_message("Hello, how are you ?")
    chat.chat_message("My name is Bob.")
    chat.chat_message("What is my name ?")
    

