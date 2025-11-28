from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from dotenv import load_dotenv

# resolve project root (chrome-extension)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

# load .env explicitly so env vars are available immediately
load_dotenv(dotenv_path=ENV_PATH)

class ModelSetting(BaseSettings):
    embedding_model: str = Field(..., env="EMBEDDING_MODEL")
    redis_vector_url: str = Field(..., env="REDIS_VECTOR_URL")
    redis_db_url: str = Field(..., env="REDIS_DB_URL")
    api_key: str = Field(..., env="API_KEY")
    primary_model: str = Field(..., env="PRIMARY_MODEL")
    secondary_model: str = Field(..., env="SECONDARY_MODEL")
    max_tokens: int = Field(1024, env="MAX_TOKENS")
    temperature: float = Field(0.0, env="TEMPERATURE")

    class Config:
        env_file = str(ENV_PATH)
        env_file_encoding = "utf-8"

# instantiate settings after loading .env
setting = ModelSetting()