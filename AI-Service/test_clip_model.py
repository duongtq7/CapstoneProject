import torch
from transformers import CLIPModel, CLIPProcessor
import os

MODEL_PATH = "/home/duongtq/capstone/Demo/Sample/AI-Services/models/clip_pretrain/clip_vi_best.pt"
BASE_MODEL_ID = "openai/clip-vit-base-patch32"

def test_custom_clip_model():
    print("Testing custom CLIP model loading...")
    try:
        # Set device
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {device}")
        
        # Load the checkpoint file
        print(f"Loading checkpoint from {MODEL_PATH}")
        checkpoint = torch.load(MODEL_PATH, map_location=device)
        
        # Check if model_state_dict exists in the checkpoint
        if 'model_state_dict' in checkpoint:
            print("model_state_dict found in checkpoint")
            model_state_dict = checkpoint['model_state_dict']
            print("State dict keys sample:", list(model_state_dict.keys())[:5])
        else:
            print("model_state_dict not found in checkpoint")
            print("Available keys:", checkpoint.keys())
            return
        
        # Initialize base model from transformers
        print(f"Loading base model: {BASE_MODEL_ID}")
        model = CLIPModel.from_pretrained(BASE_MODEL_ID)
        processor = CLIPProcessor.from_pretrained(BASE_MODEL_ID)
        
        # Try to load the state dict
        print("Loading state dict into model...")
        try:
            model.load_state_dict(model_state_dict, strict=False)
            print("State dict loaded successfully with strict=False")
        except Exception as e:
            print(f"Error loading state dict: {e}")
            
        # Put model on device
        model.to(device)
        
        # Put model in evaluation mode
        model.eval()
        
        # Test with some text
        print("\nTesting text encoding...")
        test_text = ["a photo of a cat", "a photo of a dog"]
        text_inputs = processor(
            text=test_text,
            images=None,
            return_tensors="pt",
            padding=True
        ).to(device)
        
        with torch.no_grad():
            text_features = model.get_text_features(**text_inputs)
            # Normalize embeddings
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        print(f"Text features shape: {text_features.shape}")
        print(f"First few values: {text_features[0, :5]}")

        print("\nCustom CLIP model test completed successfully!")
            
    except Exception as e:
        print(f"Error testing custom CLIP model: {e}")

if __name__ == "__main__":
    test_custom_clip_model() 