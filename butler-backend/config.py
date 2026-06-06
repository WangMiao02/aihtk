import os

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:38000")
LLM_MODEL    = os.getenv("LLM_MODEL",    "qwen3.5-27b")
LLM_TIMEOUT  = int(os.getenv("LLM_TIMEOUT", "8"))

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "artifacts"), exist_ok=True)
