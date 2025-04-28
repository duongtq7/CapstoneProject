import torch
from transformers import CLIPProcessor, CLIPModel
import logging
from fastapi import HTTPException
from typing import Union, List, Any
import numpy as np
from ray import serve
from starlette.requests import Request
from ray.serve.config import AutoscalingConfig
import os

logger = logging.getLogger("ray.serve")
os.environ['HF_HOME'] = './models'

@serve.deployment(ray_actor_options={"num_gpus": 0.1},
                  autoscaling_config=AutoscalingConfig(
                      min_replicas=1,
                      max_replicas=10,
                  ))
class ClipTextEncoder:
    def __init__(self):
        self.model_id = "openai/clip-vit-base-patch32"
        self.model_path = "./models/"
        try:
            logger.info(f"Loading model {self.model_id}")    
            model_location = self.model_path + self.model_id.split("/")[1]
            logger.info(f"---Model Location {model_location}---")
            
            # Initialize the model and processor
            self.model = CLIPModel.from_pretrained(self.model_id, cache_dir=model_location, local_files_only=True, device_map='cuda:0')
            self.processor = CLIPProcessor.from_pretrained(self.model_id, cache_dir=model_location, local_files_only=True, device_map='cuda:0')
            
            # Set device
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

    async def __call__(self, http_request: Request):
        try:
            logger.info("Starting text encoding inference")
            
            # Parse request data
            data = await http_request.json()
            if not data or 'text' not in data:
                raise HTTPException(status_code=400, detail="Missing required parameter: text")
            
            text = data['text']
            
            # Process the text
            inputs = self.processor(
                text=text,
                images=None,
                return_tensors="pt",
                padding=True,
                truncation=True
            ).to(self.device)
            
            # Get text features
            with torch.no_grad():
                text_embeddings = self.model.get_text_features(**inputs)
            
            # Convert to numpy array
            text_embeddings = text_embeddings.detach().cpu().numpy()
            return text_embeddings.tolist()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error encoding text: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error during inference: {str(e)}")

app = ClipTextEncoder.bind()