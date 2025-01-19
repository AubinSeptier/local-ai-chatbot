from model import Model


llm = Model()
llm.save_model("meta-llama/Llama-3.2-1B")
print("Model saved successfully")
llm.load_model("meta-llama_Llama-3.2-1B")
print("Model loaded successfully")
print("END")
