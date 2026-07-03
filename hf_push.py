from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from dotenv import load_dotenv
import os

load_dotenv()

MODEL_ID=os.getenv('MODEL_ID')
HF_USERNAME = os.getenv('HF_USERNAME')
ADAPTER_PATH = os.getenv("ADAPTER_PATH")
HF_TOKEN = os.getenv("HF_TOKEN")


base_model = AutoModelForCausalLM.from_pretrained(MODEL_ID) # type: ignore
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

model = PeftModel.from_pretrained(base_model, ADAPTER_PATH) # type: ignore

merged_model = model.merge_and_unload() # type: ignore


merged_model.push_to_hub(f'{HF_USERNAME}/qwen2.5-3b-sql', token=HF_TOKEN)
tokenizer.push_to_hub(f'{HF_USERNAME}/qwen2.5-3b-sql', token=HF_TOKEN)