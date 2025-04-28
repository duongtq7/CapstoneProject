# AI Service for CLIP and Translation

A Ray Serve-powered AI service providing CLIP embedding and Vietnamese-English translation capabilities.

## Overview

This project provides scalable AI services using Ray Serve for:
- CLIP (Contrastive Language-Image Pre-training) embeddings for images and text
- Vietnamese to English translation

The services are designed to support high-performance, scalable inference with automatic scaling based on demand.

## Features

- 🖼️ **CLIP Image Embedding**: Generate embeddings from images
- 📝 **CLIP Text Embedding**: Generate embeddings from text
- 🌏 **Vietnamese to English Translation**: Neural machine translation

## Tech Stack

- **Framework**: [Ray Serve](https://docs.ray.io/en/latest/serve/index.html) for model serving
- **Deep Learning**: [PyTorch](https://pytorch.org/) + [Transformers](https://huggingface.co/docs/transformers/index)
- **Models**:
  - CLIP (OpenAI's Contrastive Language-Image Pre-training)
  - VINAI Vietnamese-English Translation model
- **Performance Testing**: [Locust](https://locust.io/) for load testing

## Prerequisites

- Python 3.10 or higher
- CUDA-compatible GPU (recommended)
- CUDA Toolkit 12.4 (for GPU acceleration)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd CapstoneProject/AI-Service
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Download models:
   ```bash
   python download_model.py
   ```

## Running the Services

Start the Ray Serve application:

```bash
serve run config.yaml
```

This will start the following services:
- CLIP Text Encoder at `/clip_text_encoder`
- CLIP Image Encoder at `/clip_image_encoder`

For the custom CLIP model:

```bash
serve run clip.yaml
```

For the translation service:

```bash
serve run -m translate_model:app
```

## API Usage

### CLIP Text Embedding

```bash
curl -X POST "http://localhost:8100/clip_text_encoder" \
     -H "Content-Type: application/json" \
     -d '{"text": "a photo of a cat"}'
```

### CLIP Image Embedding

```bash
curl -X POST "http://localhost:8100/clip_image_encoder" \
     -H "Content-Type: application/json" \
     -d '{"image_url": "https://example.com/image.jpg"}'
```

### Vietnamese to English Translation

```bash
curl -X POST "http://localhost:8000/" \
     -H "Content-Type: application/json" \
     -d '{"text": "Xin chào thế giới"}'
```

## Load Testing

Use Locust for load testing:

```bash
locust -f locustfile.py
```

Then open http://localhost:8089 in your browser to start the test.

## Project Structure

```
AI-Service/
├── .venv/                  # Virtual environment
├── models/                 # Downloaded model files
├── clip_custom_model.py    # Custom CLIP model for images
├── clip_custom_text_encoder.py # Custom CLIP model for text
├── clip_image_model.py     # Standard CLIP image embeddings
├── clip_text_encoder.py    # Standard CLIP text embeddings
├── translate_model.py      # Vietnamese to English translation
├── config.yaml             # Ray Serve configuration
├── clip.yaml               # Custom CLIP configuration
├── locustfile.py           # Load testing configuration
├── download_model.py       # Script to download models
├── pyproject.toml          # Python project configuration
└── README.md               # Project documentation
```

## License

[Specify your license here]

## Acknowledgments

- [OpenAI CLIP](https://github.com/openai/CLIP)
- [VINAI Translation Models](https://huggingface.co/vinai)
