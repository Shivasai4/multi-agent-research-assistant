from langchain_ollama import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import settings
from loguru import logger
import time

def get_llm(temperature: float = None):
    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=temperature if temperature is not None else settings.temperature,
        timeout=settings.request_timeout,
        num_ctx=4096,  # reduced for speed
    )

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type(Exception),
    reraise=False
)
def invoke_llm_with_retry(llm, messages, structured_output_schema=None, max_retries=2):
    """Invoke LLM with retry and timeout (handled by llm.timeout)."""
    try:
        if structured_output_schema:
            structured_llm = llm.with_structured_output(structured_output_schema)
            return structured_llm.invoke(messages)
        else:
            return llm.invoke(messages)
    except Exception as e:
        logger.warning(f"LLM invocation failed: {e}, retrying...")
        raise  # tenacity will retry