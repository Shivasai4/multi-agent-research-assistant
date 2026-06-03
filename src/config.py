from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    llm_model: str = Field(default="llama3.1:latest", alias="LLM_MODEL")
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5", alias="EMBEDDING_MODEL")
    
    langfuse_public_key: Optional[str] = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: Optional[str] = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", alias="LANGFUSE_HOST")
    
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL") 
    vector_db_path: str = Field(default="./data/chroma_db", alias="VECTOR_DB_PATH")
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    
    max_research_steps: int = Field(default=5, alias="MAX_RESEARCH_STEPS")
    temperature: float = Field(default=0.2, alias="TEMPERATURE")
    request_timeout: int = Field(default=120, alias="REQUEST_TIMEOUT")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()