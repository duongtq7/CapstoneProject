import requests
from fastapi import FastAPI
from ray import serve
# import clip
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import logging
import torch
import numpy as np
from starlette.requests import Request
from ray.serve.config import AutoscalingConfig
from fastapi import HTTPException

logger = logging.getLogger("ray.serve")

# app = FastAPI()


@serve.deployment(ray_actor_options={"num_gpus": 0.1},
                  autoscaling_config=AutoscalingConfig(
                      min_replicas=1,
                      max_replicas=100,
                  ))
# @serve.ingress(app)
class ClipOriginal:
    def __init__(self):
        self.model_id = "openai/clip-vit-base-patch32"
        self.model_path = "./models/"
        # self.model = CLIPModel.from_pretrained(self.model_id)
        # self.processor = CLIPProcessor.from_pretrained(self.model_id)
        
    @serve.multiplexed(max_num_models_per_replica=10)
    async def get_model(self, model_id):
        try:
            logger.info(f"Loading model {model_id}")    
            model_location = self.model_path + model_id.split("/")[1]
            logger.info(f"---Model Location {model_location}---")
            model = CLIPModel.from_pretrained(model_id, cache_dir=model_location, local_files_only=True, device_map='cuda:0')
            processor = CLIPProcessor.from_pretrained(model_id, cache_dir=model_location, local_files_only=True, device_map='cuda:0')
            
            return model, processor
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

    async def __call__(self, http_request: Request):
        try:
            model_id = serve.get_multiplexed_model_id()
            logger.info(f"Model_id: {model_id}")
            
            model, processor = await self.get_model(model_id)
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info("starting the inference")
            
            data: str = await http_request.json()
            if not data or 'image_url' not in data:
                raise HTTPException(status_code=400, detail="Missing required parameter: image_url")
                
            image_url = data['image_url']
            
            response = requests.get(image_url, stream=True)
            if not response.ok:
                raise HTTPException(status_code=400, detail=f"Failed to fetch image from URL: {response.status_code}")
                
            image = Image.open(response.raw)
            # image = np.asarray(image)
            # Move model to device
            images = processor(
                text=None,
                images=image,
                return_tensors='pt'
            )['pixel_values'].to(device)
            img_emb = model.get_image_features(images)
            img_emb = img_emb.detach().cpu().numpy()
            return img_emb
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Inference error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error during inference: {str(e)}")
# serve.start()
# ClipOriginal.deploy()

app = ClipOriginal.bind()