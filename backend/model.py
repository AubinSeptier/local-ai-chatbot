from transformers import AutoModelForCausalLM, AutoTokenizer
import os

class Model:
    def __init__(self):
        self.model_path = "models/"
        self.tokenizer = None
        self.model = None
    
    def load_model(self, model_name: str):
        try:
            saved_model_path = os.path.join(self.model_path, model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(saved_model_path)
            self.model = AutoModelForCausalLM.from_pretrained(saved_model_path)
        except Exception as e:
            print("Error loading model: ", e)
        
    def save_model(self, model_name: str):
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
        
            save_path = os.path.join(self.model_path, model_name)
            model.save_pretrained(save_path)
            tokenizer.save_pretrained(save_path)
        except Exception as e:
            print("Error saving model: ", e)
        
        
        