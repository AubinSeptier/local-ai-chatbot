from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from transformers import Pipeline

from pathlib import Path
import torch
import logging
import os

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Handles model loading and pipeline configuration.
    
    Attributes:
        cache_dir: Directory for model storage
        pipeline: Active text generation pipeline
    """
    
    def __init__(self, cache_dir: str = "./models/"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline: Pipeline = None

    def load_model(self, model_name: str, generation_config: dict) -> Pipeline:
        """
        Load or download specified model.
        
        Args:
            model_name: Hugging Face model identifier
            generation_config: Text generation parameters
            
        Returns:
            Configured text generation pipeline
        """
        try:
            local_path = self.cache_dir / model_name.replace("/", "_")
            
            if local_path.exists():
                logger.info(f"Loading cached model: {model_name}")
                tokenizer = AutoTokenizer.from_pretrained(local_path)
                model = AutoModelForCausalLM.from_pretrained(local_path)
            else:
                logger.info(f"Downloading model: {model_name}")
                tokenizer, model = self._download_model(model_name, local_path)

            return self._create_pipeline(model, tokenizer, generation_config)
            
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            raise

    def _download_model(self, model_name: str, save_path: Path):
        """Download and save model from Hugging Face Hub."""
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN environment variable required")
            
        tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
        model = AutoModelForCausalLM.from_pretrained(model_name, token=hf_token)
        
        tokenizer.save_pretrained(save_path)
        model.save_pretrained(save_path)
        return tokenizer, model

    def _create_pipeline(self, model, tokenizer, generation_config: dict) -> Pipeline:
        """Create text generation pipeline with default parameters."""
        config = {
            "max_new_tokens": 1024,
            "temperature": 0.7,
            "top_k": 50,
            "top_p": 0.95,
            **generation_config
        }
        
        return pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            **config
        )