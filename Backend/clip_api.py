import requests
from fastapi import FastAPI
from ray import serve
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import logging
import torch
import numpy as np
from starlette.requests import Request
from ray.serve.config import AutoscalingConfig
from fastapi import HTTPException
import os
import boto3
from typing import List, Union, Dict, Any
import io
from botocore.exceptions import ClientError

logger = logging.getLogger("ray.serve")
os.environ['HF_HOME'] = './models'

# S3 Configuration - Update these values based on your deployment environment
# Force the S3 URL to explicitly use the service name
S3_INTERNAL_URL = os.environ.get("S3_INTERNAL_URL", "http://minio:9000")  
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "my-bucket")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "admin")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "admin123")
S3_REGION = os.environ.get("S3_REGION", "")

# Log the configuration
logger.info(f"S3 configuration: URL={S3_INTERNAL_URL}, BUCKET={S3_BUCKET_NAME}")


@serve.deployment(ray_actor_options={"num_gpus": 0.1},
                  autoscaling_config=AutoscalingConfig(
                      min_replicas=1,
                      max_replicas=10,
                  ))
class ClipOriginal:
    def __init__(self):
        self.model_id = "openai/clip-vit-base-patch32"
        self.model_path = "./models/"
        self.s3_client = None
        
        # Try to initialize S3 client (but don't block on failure)
        self._init_s3_client()
        
        try:
            logger.info(f"Loading model {self.model_id}")    
            model_location = self.model_path + self.model_id.split("/")[1]
            logger.info(f"---Model Location {model_location}---")
            self.model = CLIPModel.from_pretrained(self.model_id, cache_dir=model_location, local_files_only=True, device_map='cuda:0')
            self.processor = CLIPProcessor.from_pretrained(self.model_id, cache_dir=model_location, local_files_only=True, device_map='cuda:0')
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

    def _init_s3_client(self):
        """Initialize the S3 client with retry logic"""
        # Define possible endpoints to try
        endpoints = [
            S3_INTERNAL_URL,  # From environment (minio:9000)
            "http://minio:9000",  # Docker service name
            "http://localhost:9000"  # Local testing
        ]
        
        for endpoint in endpoints:
            try:
                logger.info(f"Trying to initialize S3 client with endpoint: {endpoint}")
                client = boto3.client(
                    "s3",
                    endpoint_url=endpoint,
                    aws_access_key_id=S3_ACCESS_KEY,
                    aws_secret_access_key=S3_SECRET_KEY,
                    region_name=S3_REGION,
                    config=boto3.session.Config(
                        signature_version="s3v4",
                        s3={"addressing_style": "path"},
                    ),
                )
                
                # Test connection
                client.list_buckets()
                logger.info(f"Successfully connected to S3/MinIO using endpoint: {endpoint}")
                self.s3_client = client
                self.s3_endpoint = endpoint
                return
            except Exception as e:
                logger.warning(f"Failed to connect to S3 at {endpoint}: {str(e)}")
        
        logger.error("Failed to initialize S3 client with any endpoint")

    def _is_s3_url(self, url: str) -> bool:
        """Check if the URL is from our S3/MinIO storage"""
        return "/my-bucket/" in url or f"/{S3_BUCKET_NAME}/" in url

    def _get_object_key_from_url(self, url: str) -> str:
        """Extract the object key from an S3 URL"""
        # Example URL: http://localhost:9000/my-bucket/users/123/albums/456/image.jpg
        parts = url.split(f"/{S3_BUCKET_NAME}/")
        if len(parts) > 1:
            return parts[1]
        return ""

    def _load_image_from_url(self, url: str) -> Image.Image:
        """Load image from URL using requests"""
        logger.info(f"Fetching image from URL: {url}")
        response = requests.get(url, stream=True, timeout=10)
        if not response.ok:
            raise HTTPException(status_code=400, detail=f"Failed to fetch image from URL: {response.status_code}")
        return Image.open(response.raw)

    def _get_image_from_s3(self, url: str) -> Image.Image:
        """Try to get image from S3, with fallback to HTTP request"""
        object_key = self._get_object_key_from_url(url)
        if not object_key:
            logger.warning(f"Could not extract object key from URL: {url}")
            return self._load_image_from_url(url)
        
        logger.info(f"Getting image from S3 with key: {object_key}")
        
        # If S3 client isn't initialized or fails, fall back to HTTP
        if self.s3_client is None:
            logger.warning("S3 client not initialized, falling back to HTTP request")
            return self._load_image_from_url(url)
        
        try:
            response = self.s3_client.get_object(
                Bucket=S3_BUCKET_NAME,
                Key=object_key,
            )
            
            image_data = response['Body'].read()
            return Image.open(io.BytesIO(image_data))
        except Exception as e:
            logger.warning(f"S3 direct access failed: {str(e)}, falling back to HTTP request")
            return self._load_image_from_url(url)

    async def __call__(self, http_request: Request) -> Union[np.ndarray, Dict[str, Any]]:
        try:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"Starting inference on device: {device}")
            
            data = await http_request.json()
            if not data or 'image_url' not in data:
                raise HTTPException(status_code=400, detail="Missing required parameter: image_url")
                
            image_url = data['image_url']
            logger.info(f"Processing image URL: {image_url}")
            
            # Always try to load the image, regardless of URL type
            try:
                if self._is_s3_url(image_url):
                    logger.info("Detected S3/MinIO URL")
                    image = self._get_image_from_s3(image_url)
                else:
                    logger.info("Using regular HTTP request")
                    image = self._load_image_from_url(image_url)
            except Exception as e:
                logger.error(f"Failed to load image: {str(e)}")
                # Last resort - direct HTTP request
                image = self._load_image_from_url(image_url)
            
            images = self.processor(
                text=None,
                images=image,
                return_tensors='pt'
            )['pixel_values'].to(device)
            
            img_emb = self.model.get_image_features(images)
            img_emb = img_emb.detach().cpu().numpy()
            
            return img_emb.tolist()  # Convert to list for JSON serialization
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Inference error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error during inference: {str(e)}")

app = ClipOriginal.bind() 