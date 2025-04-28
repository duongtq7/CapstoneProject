
import huggingface_hub
import os
from dotenv import load_dotenv
load_dotenv()

huggingface_hub.snapshot_download("openai/clip-vit-base-patch32",
                                   cache_dir="./models/clip-vit-base-patch32",
                                   token=os.environ['HUGGINGFACE_TOKEN']
                                  )

