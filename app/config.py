import os
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./transactions.db")
    
    # OpenRouter
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo")
    
    # Cache
    USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))
    
    # App
    MAX_QUERY_COMPLEXITY = int(os.getenv("MAX_QUERY_COMPLEXITY", 10))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

@lru_cache()
def get_config():
    return Config()