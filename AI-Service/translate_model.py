import requests
from ray import serve
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import logging
import torch
from starlette.requests import Request
from ray.serve.config import AutoscalingConfig
from fastapi import HTTPException
import os

logger = logging.getLogger("ray.serve")
os.environ['HF_HOME'] = './models'


@serve.deployment(ray_actor_options={
    "num_cpus": 0.2,
    "num_gpus": 0.1},
                  autoscaling_config=AutoscalingConfig(
                      min_replicas=1,
                      max_replicas=10,
                  ))
class VietnameseToEnglishTranslator:
    def __init__(self):
        self.model_id = "vinai/vinai-translate-vi2en-v2"
        try:
            logger.info(f"Loading translation model {self.model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, src_lang="vi_VN")
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_id)
            device_vi2en = torch.device("cuda")
            self.model.to(device_vi2en)
        except Exception as e:
            logger.error(f"Error loading translation model: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load translation model: {str(e)}")

    async def __call__(self, http_request: Request):
        data = await http_request.json()
        if not data or 'text' not in data:
            raise HTTPException(status_code=400, detail="Missing required parameter: text")
        vi_texts = data['text']
        
        try:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info("Starting Vietnamese to English translation")
            
            input_ids = self.tokenizer(vi_texts, padding=True, return_tensors="pt").to(device)
            output_ids = self.model.generate(
                **input_ids,
                decoder_start_token_id=self.tokenizer.lang_code_to_id["en_XX"],
                num_return_sequences=1,
                num_beams=5,
                early_stopping=True
            )
            en_texts = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)
            
            return {"original": vi_texts, "translated": en_texts}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error during translation: {str(e)}")


app = VietnameseToEnglishTranslator.bind()