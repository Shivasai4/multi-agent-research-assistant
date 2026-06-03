from fastapi import FastAPI
from src.api.routes import router
from src.observability.langfuse_setup import init_langfuse
from src.cache.redis_cache import init_redis
from loguru import logger
from src.api.hitl_routes import router as hitl_router

app = FastAPI(title="Multi-Agent Research Assistant", version="1.0.0")
app.include_router(router)
app.include_router(hitl_router)

@app.on_event("startup")
def startup():
    init_langfuse()
    init_redis()   # <-- add this
    logger.info("Multi-Agent Research Assistant started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)