import torch
import logging
import numpy as np
from ray import serve
from starlette.requests import Request
from ray.serve.config import AutoscalingConfig
from fastapi import HTTPException
import os
from transformers import CLIPModel, CLIPProcessor

logger = logging.getLogger("ray.serve")
os.environ['HF_HOME'] = './models'

MODEL_PATH = "/home/duongtq/capstone/Demo/Sample/AI-Services/models/clip_pretrain/clip_vi_best.pt"
# Base CLIP model to load the state dict into
BASE_MODEL_ID = "openai/clip-vit-base-patch32"

@serve.deployment(ray_actor_options={"num_gpus": 0.1},
                  autoscaling_config=AutoscalingConfig(
                      min_replicas=1,
                      max_replicas=10,
                  ))
class ClipCustomTextEncoder:
    def __init__(self):
        try:
            logger.info(f"Loading custom CLIP model from {MODEL_PATH}")
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            # Load the checkpoint file
            checkpoint = torch.load(MODEL_PATH, map_location=self.device)
            
            # Initialize base model from transformers
            self.model = CLIPModel.from_pretrained(BASE_MODEL_ID)
            
            # Load the state dict from the checkpoint
            if 'model_state_dict' in checkpoint:
                model_state_dict = checkpoint['model_state_dict']
                logger.info("Found model_state_dict in checkpoint")
            else:
                logger.info("model_state_dict not found in checkpoint, using the checkpoint as state dict")
                model_state_dict = checkpoint
            
            # Load compatible weights
            self.model.load_state_dict(model_state_dict, strict=False)
            
            # Move model to device
            self.model.to(self.device)
            
            # Put model in evaluation mode
            self.model.eval()
            
            # Initialize processor
            self.processor = CLIPProcessor.from_pretrained(BASE_MODEL_ID)
            
            logger.info("Custom CLIP model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

    async def __call__(self, http_request: Request):
        try:
            logger.info("Starting text encoding with custom CLIP model")
            
            data = await http_request.json()
            if not data or 'text' not in data:
                raise HTTPException(status_code=400, detail="Missing required parameter: text")
                
            text = data['text']
            
            # Process the text using CLIP processor
            inputs = self.processor(
                text=text,
                images=None,
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            # Get text embeddings
            with torch.no_grad():
                text_features = self.model.get_text_features(**inputs)
                # Normalize embeddings
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy and return
            text_features = text_features.detach().cpu().numpy()
            return text_features.tolist()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Text encoding error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error during text encoding: {str(e)}")

app = ClipCustomTextEncoder.bind() 