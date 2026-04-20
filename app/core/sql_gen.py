import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from loguru import logger
import os

# Configuration
# Base model matching the Qwen2.5-3B architecture
BASE_MODEL_NAME = "Qwen/Qwen2.5-3B" 
ADAPTER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class SQLGenerator:
    """
    Singleton class to handle the loading and inference of the Qwen2.5-3B model with custom LoRA adapters.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SQLGenerator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        logger.info(f"SQLGen: Initializing on device: {DEVICE}")
        try:
            # 1. Load Tokenizer
            # Using the local model dir for tokenizer to ensure compatibility with adapters
            self.tokenizer = AutoTokenizer.from_pretrained(
                ADAPTER_PATH, 
                trust_remote_code=True,
                local_files_only=True 
            )
            
            # fallback to base if local fails
            if not self.tokenizer:
                self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME, trust_remote_code=True)
            
            # 2. Load Base Model
            logger.info(f"SQLGen: Loading base model {BASE_MODEL_NAME}...")
            base_model = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL_NAME,
                torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
                device_map="auto" if DEVICE == "cuda" else None,
                trust_remote_code=True
            )
            
            # 3. Load and Apply LoRA Adapters
            logger.info(f"SQLGen: Applying LoRA adapters from {ADAPTER_PATH}...")
            self.model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
            
            if DEVICE == "cpu":
                self.model.to(DEVICE)
                
            self.model.eval()
            self._initialized = True
            logger.success("SQLGen: Model and LoRA adapters loaded successfully.")
            
        except Exception as e:
            logger.error(f"SQLGen: Failed to load model/adapters: {e}")
            # We don't raise here to allow the app to boot even if model loading fails
            # but we set a flag
            self.model = None

    def format_prompt(self, question: str, schema_context: str) -> str:
        """Prepares the prompt using ChatML format and schema injection."""
        system_msg = (
            "You are an expert SQL generator. Given a database schema and a question, "
            "provide the correct SQL query to answer the question. "
            "Use only the tables and columns provided. Output only the SQL code."
        )
        
        user_msg = f"Schema:\n{schema_context}\n\nQuestion: {question}"
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
        
        return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def generate(self, question: str, schema_info: dict) -> str:
        """Generates SQL string from NL question and schema dictionary."""
        if not self.model:
            return "-- Model not loaded. Check logs for details."

        # Convert internal schema dict to a string for the model
        schema_parts = []
        for table, cols in schema_info.items():
            col_strings = []
            for c in cols:
                info = f"{c['name']} ({c['type']})"
                if c.get('pk'): 
                    info += " PRIMARY KEY"
                col_strings.append(info)
            schema_parts.append(f"Table {table} ({', '.join(col_strings)})")
        
        schema_context = "\n".join(schema_parts)
        logger.info(f"SQLGen: Generating SQL for question: {question}")
        prompt = self.format_prompt(question, schema_context)
        
        # Ensure tokenizer has a pad token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        inputs = self.tokenizer(prompt, return_tensors="pt").to(DEVICE)
        
        logger.info("SQLGen: Model generating...")
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=150,
                temperature=0.1,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        logger.info("SQLGen: Generation complete.")
        
        generated_text = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        # Clean up any potential markdown formatting in output
        return generated_text.replace("```sql", "").replace("```", "").strip()

# Helper for singleton access
_generator = None

def get_generator():
    global _generator
    if _generator is None:
        _generator = SQLGenerator()
    return _generator

def generate_sql(question: str, schema_info: dict) -> str:
    """Wrapper function to be called from the UI."""
    gen = get_generator()
    return gen.generate(question, schema_info)