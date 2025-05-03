import logging
import os
import sys
import cv2
import numpy as np
import torch
from ray import serve
from ray.serve.config import AutoscalingConfig
from transformers import CLIPProcessor, CLIPModel
from transnetv2_pytorch import TransNetV2
from starlette.requests import Request
from starlette.responses import JSONResponse
import hdbscan
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
class KeyFrameExtractionRequest(BaseModel):
    video_path: str = Field(..., description="Path to the input video file")
    output_directory: Optional[str] = Field(None, description="Directory to save extracted frames")

class KeyFrameExtractionResponse(BaseModel):
    status: str = Field(..., description="Status of the operation")
    shot_boundaries: Optional[List[int]] = Field(None, description="List of frame indices where shot boundaries are detected")
    keyframes: Optional[List[int]] = Field(None, description="List of frame indices selected as keyframes")
    message: Optional[str] = Field(None, description="Error message if status is 'error'")

@serve.deployment(ray_actor_options={"num_gpus": 1.0},
                  autoscaling_config=AutoscalingConfig(
                      min_replicas=1,
                      max_replicas=10,
                  ))
class KeyFrameExtractor:
    """A class for extracting keyframes from videos using TransNetV2 and CLIP."""

    def __init__(self):
        """Initialize the extractor with required models."""
        self.model_id = os.environ['CLIP_MODEL_ID']
        self.model_location = os.environ['CLIP_MODEL_PATH']
        self.transnet_weight = os.environ['TRANSNET_WEIGHT_PATH']

        # Load TransNetV2 model
        self.model = TransNetV2()
        state_dict = torch.load(self.transnet_weight)
        self.model.load_state_dict(state_dict)
        self.model.eval().cuda()

        # Load CLIP model and processor
        self.clip_model = CLIPModel.from_pretrained(self.model_id, cache_dir=self.model_location, local_files_only=True, device_map='cuda:0')
        self.clip_processor = CLIPProcessor.from_pretrained(self.model_id, cache_dir=self.model_location, local_files_only=True, device_map='cuda:0')
        logger.info("KeyFrameExtractor initialized and models loaded.")

    def load_video(self, video_path, resize_to=(27, 48)):
        """Load video frames and preprocess them for TransNetV2."""
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, resize_to[::-1])
            frames.append(frame)
        
        cap.release()
        return np.array(frames, dtype=np.uint8)

    def save_boundary_frames(self, video_path, shot_boundaries, output_dir="boundary_frames"):
        """Extract and save frames at shot boundaries from the original video."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count in shot_boundaries:
                output_path = os.path.join(output_dir, f"frame_{frame_count}.jpg")
                cv2.imwrite(output_path, frame)
                logger.info(f"Saved frame {frame_count} to {output_path}")
            frame_count += 1
        
        cap.release()

    def save_keyframes(self, video_path, keyframe_indices, output_dir="keyframes"):
        """Extract and save keyframes from the original video."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count in keyframe_indices:
                output_path = os.path.join(output_dir, f"keyframe_{frame_count}.jpg")
                cv2.imwrite(output_path, frame)
                logger.info(f"Saved keyframe {frame_count} to {output_path}")
            frame_count += 1
        
        cap.release()

    def detect_shot_boundaries(self, video_path, threshold=0.5, chunk_size=32):
        """Detect shot boundaries using TransNetV2, processing video in chunks."""
        frames = self.load_video(video_path)
        if len(frames) == 0:
            return [], []

        all_predictions = []
        for i in range(0, len(frames), chunk_size):
            chunk = frames[i:i + chunk_size]
            input_chunk = torch.from_numpy(chunk).permute(0, 3, 1, 2)
            input_chunk = input_chunk.unsqueeze(0)
            input_chunk = input_chunk.permute(0, 1, 3, 4, 2)

            with torch.no_grad():
                input_chunk = input_chunk.cuda()
                single_frame_pred, _ = self.model(input_chunk)
                single_frame_pred = torch.sigmoid(single_frame_pred).cpu().numpy()
                all_predictions.extend(single_frame_pred[0])

        shot_boundaries = []
        predictions = np.array(all_predictions)
        for i, prob in enumerate(predictions):
            if prob > threshold:
                shot_boundaries.append(i)

        return shot_boundaries, predictions

    def load_full_video_frames(self, video_path):
        """Load all frames from the video in original resolution."""
        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_indices = []
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_indices.append(frame_count)
            frame_count += 1
        
        cap.release()
        return frames, frame_indices

    def extract_clip_features(self, frames, model, processor, device="cuda"):
        """Extract semantic features using CLIP for a list of frames."""
        model = model.to(device)
        model.eval()
        features = []
        
        for frame in frames:
            inputs = processor(images=frame, return_tensors="pt", padding=True).to(device)
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
            features.append(image_features.cpu().numpy().flatten())
        
        return np.array(features)

    def adaptive_clustering(self, features, min_cluster_size=60):
        """Perform adaptive clustering using HDBSCAN."""
        n_samples = len(features)
        
        if n_samples < min_cluster_size:
            return np.zeros(n_samples, dtype=int), features

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=1,
            cluster_selection_method='eom'
        )
        labels = clusterer.fit_predict(features)
        
        if np.all(labels == -1):
            return np.zeros(n_samples, dtype=int), features
        
        unique_labels = np.unique(labels[labels != -1])
        centroids = []
        for label in unique_labels:
            cluster_features = features[labels == label]
            centroid = np.mean(cluster_features, axis=0)
            centroids.append(centroid)
        
        return labels, np.array(centroids) if len(centroids) > 0 else features

    def select_keyframes(self, shot_frames, shot_features, shot_indices):
        """Select keyframes from each shot using HDBSCAN clustering."""
        labels, centroids = self.adaptive_clustering(shot_features)
        keyframe_indices = []
        
        if len(shot_features) == 1 or len(centroids) == 1 and np.all(labels != -1):
            keyframe_indices.append(shot_indices[0])
            return keyframe_indices
        
        unique_labels = np.unique(labels[labels != -1])
        if len(unique_labels) == 0:
            keyframe_indices.append(shot_indices[0])
            return keyframe_indices
        
        for cluster_id in unique_labels:
            cluster_indices = [i for i, label in enumerate(labels) if label == cluster_id]
            cluster_features = shot_features[cluster_indices]
            centroid = centroids[np.where(unique_labels == cluster_id)[0][0]]
            
            distances = np.linalg.norm(cluster_features - centroid, axis=1)
            closest_frame_idx = cluster_indices[np.argmin(distances)]
            keyframe_indices.append(shot_indices[closest_frame_idx])
        
        return sorted(keyframe_indices)

    def extract_keyframes(self, video_path, shot_boundaries):
        """Extract keyframes from video using CLIP and clustering."""
        all_frames, all_indices = self.load_full_video_frames(video_path)
        shot_boundaries = [0] + shot_boundaries + [len(all_frames)]
        
        all_keyframes = []
        for i in range(len(shot_boundaries) - 1):
            start_idx = shot_boundaries[i]
            end_idx = shot_boundaries[i + 1]
            
            shot_frames = all_frames[start_idx:end_idx]
            shot_indices = all_indices[start_idx:end_idx]
            
            if len(shot_frames) == 0:
                continue
            
            shot_features = self.extract_clip_features(
                shot_frames, self.clip_model, self.clip_processor
            )
            keyframe_indices = self.select_keyframes(
                shot_frames, shot_features, shot_indices
            )
            all_keyframes.extend(keyframe_indices)
        
        return sorted(all_keyframes)

    async def __call__(self, req: Request):
        """
        Handle incoming HTTP requests.

        Args:
            req: HTTP request

        Returns:
            JSONResponse: Keyframe extraction results
        """
        try:
            # Parse and validate request data 
            data = await req.json()
            request_data = KeyFrameExtractionRequest(**data)
            
            video_path = request_data.video_path
            output_directory = request_data.output_directory

            shot_boundaries, _ = self.detect_shot_boundaries(video_path)
            keyframe_indices = self.extract_keyframes(video_path, shot_boundaries)

            logger.info(f"Detected shot boundaries: {shot_boundaries}")
            logger.info(f"Selected keyframes: {keyframe_indices}")
            
            # Save frames if output directory is provided
            if output_directory:
                boundary_dir = os.path.join(output_directory, "boundary_frames")
                keyframes_dir = os.path.join(output_directory, "keyframes")
                self.save_boundary_frames(video_path, shot_boundaries, boundary_dir)
                self.save_keyframes(video_path, keyframe_indices, keyframes_dir)

            # Create and validate response 
            response = KeyFrameExtractionResponse(
                status="success",
                shot_boundaries=shot_boundaries,
                keyframes=keyframe_indices
            )

            return JSONResponse(response.dict())

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            # Create error response using Pydantic
            error_response = KeyFrameExtractionResponse(
                status="error",
                message=str(e)
            )
            return JSONResponse(
                error_response.dict(),
                status_code=500
            )

app = KeyFrameExtractor.bind()