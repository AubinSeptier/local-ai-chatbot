from transformers import AutoModel, AutoTokenizer

class Model:
    def __init__(self):
        self.model_path = "models/"
        self.tokenizer = None
        self.model = None
    
    def load_model(self, model_name: str):
        saved_model_path = self.model_path + model_name
        tokenizer = AutoTokenizer.from_pretrained(saved_model_path)
        model = AutoModel.from_pretrained(saved_model_path)
        
        return tokenizer, model
        
    def save_model(self, model_name: str):
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        
        model.save_pretrained(self.model_path)
        tokenizer.save_pretrained(self.model_path)
        
        
        