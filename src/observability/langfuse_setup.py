import os
from langfuse.langchain import CallbackHandler
from src.config import settings
from loguru import logger

langfuse_handler = None

def init_langfuse():
    global langfuse_handler
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host
        
        langfuse_handler = CallbackHandler()
        logger.info("Langfuse initialized with LangChain callback")
    else:
        logger.warning("Langfuse credentials missing, tracing disabled")

def get_langfuse_handler():
    return langfuse_handler