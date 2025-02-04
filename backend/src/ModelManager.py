from transformers import AutoModelForCausalLM, AutoTokenizer, Pipeline, pipeline
import torch
from typing import Optional, Union, Dict
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

class ModelManager:
    """
    Manages the loading, saving, and configuration of language models.
    Handles both local and remote model management with Hugging Face.
    """

    def __init__(self, cache_dir: str = "./models/"):
        """
        Initialize the ModelManager.

        Args:
            cache_dir (str): Directory to store downloaded models
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline: Optional[Pipeline] = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_pipeline(self) -> Pipeline:
        """
        Get the current pipeline.

        Returns:
            Pipeline: The current text generation pipeline

        Raises:
            ValueError: If no pipeline is loaded
        """
        if self.pipeline is None:
            raise ValueError("No pipeline loaded. Please load a model first.")
        return self.pipeline

    def create_pipeline(
        self,
        model: AutoModelForCausalLM,
        tokenizer: AutoTokenizer,
        generation_config: Optional[Dict] = None
    ) -> Pipeline:
        """
        Create a text generation pipeline with the given model and tokenizer.

        Args:
            model: The model to use
            tokenizer: The tokenizer to use
            generation_config: Optional configuration for text generation

        Returns:
            Pipeline: Configured text generation pipeline
        """

        default_config = {
            "max_new_tokens": 1024,
            "do_sample": True,
            "temperature": 0.7,
            "top_k": 50,
            "top_p": 0.95,
            "repetition_penalty": 1.1,
        }

        if generation_config:
            default_config.update(generation_config)

        return pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            **default_config
        )

    def load_model(
        self,
        model_name: str,
        generation_config: Optional[Dict] = None
    ) -> Pipeline:
        """
        Load a model from local cache or download it if necessary.

        Args:
            model_name (str): Name of the model (HuggingFace model ID)
            device: Device to run the model on
            generation_config: Optional configuration for text generation

        Returns:
            Pipeline: Configured text generation pipeline
        """
        try:
            self.logger.info(f"Loading model '{model_name}'...")
            local_path = self.cache_dir / model_name.replace("/", "_")

            # Load from local cache if available
            if local_path.exists():
                self.logger.info(f"Loading model from local cache: {local_path}")
                tokenizer = AutoTokenizer.from_pretrained(local_path)
                model = AutoModelForCausalLM.from_pretrained(local_path)
            else:
                self.logger.info(f"Model not found in cache. Downloading '{model_name}'...")
                self._download_model(model_name, local_path)
                tokenizer = AutoTokenizer.from_pretrained(local_path)
                model = AutoModelForCausalLM.from_pretrained(local_path)

            self.pipeline = self.create_pipeline(model, tokenizer, generation_config)
            self.logger.info("Model loaded successfully")
            return self.pipeline

        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise

    def _download_model(self, model_name: str, save_path: Path):
        """
        Download a model from Hugging Face.

        Args:
            model_name (str): Name of the model to download
            save_path (Path): Path to save the downloaded model
        """
        try:
            load_dotenv()
            hf_token = os.getenv("HF_TOKEN")
            if not hf_token:
                raise ValueError("HF_TOKEN not found in .env file")

            self.logger.info(f"Downloading model '{model_name}' from Hugging Face...")
            
            # Download tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                token=hf_token,
                use_fast=True
            )
            
            # Download model
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                token=hf_token,
                trust_remote_code=False,
                revision="main"
            )

            # Save locally
            tokenizer.save_pretrained(save_path)
            model.save_pretrained(save_path)
            self.logger.info(f"Model saved successfully to {save_path}")

        except Exception as e:
            self.logger.error(f"Error downloading model: {str(e)}")
            raise

    def update_pipeline_config(self, **kwargs):
        """
        Update the configuration of the current pipeline.

        Args:
            **kwargs: Configuration parameters to update
        """
        if self.pipeline is None:
            raise ValueError("No pipeline loaded")
        
        for key, value in kwargs.items():
            if hasattr(self.pipeline, key):
                setattr(self.pipeline, key, value)
            else:
                self.pipeline.task_specific_params = {
                    **self.pipeline.task_specific_params,
                    key: value
                }