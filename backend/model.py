from transformers import AutoModelForCausalLM, AutoTokenizer
import os
from dotenv import load_dotenv

class Model:
    def __init__(self):
        self.model_path = "./models/"
        self.tokenizer = None
        self.model = None
        
    def get_tokenizer(self):
        return self.tokenizer
    
    def get_model(self):
        return self.model
    
    def load_model(self, model_name: str):
        try:
            print(f"Loading model '{model_name}'...")
            model_name = model_name.replace("/", "_")
            saved_model_path = os.path.join(self.model_path, model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(saved_model_path)
            self.model = AutoModelForCausalLM.from_pretrained(saved_model_path)
            print(f"Model loaded successfully")
        except Exception as e:
            print("Error loading model: ", e)
        
    def save_model(self, model_name: str):
        try:
            load_dotenv()
            hf_token = os.getenv("HF_TOKEN")
            if not hf_token:
                raise Exception("HF_TOKEN not found in .env file")
            
            print(f"Saving model '{model_name}' from Hugging Face...")
            tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
            model = AutoModelForCausalLM.from_pretrained(model_name, token=hf_token)
        
            save_path = os.path.join(self.model_path, model_name.replace("/", "_"))            
            tokenizer.save_pretrained(save_path)
            model.save_pretrained(save_path)
            print(f"Model saved successfully to {save_path}")
        except Exception as e:
            print("Error saving model: ", e)
        
        
        