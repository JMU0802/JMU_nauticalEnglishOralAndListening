"""
本地 OpenAI 兼容 embedding 服务器
使用 sentence-transformers 中已缓存的 paraphrase-multilingual-MiniLM-L12-v2 模型
监听 http://localhost:9622
供 LightRAG 的 openai embedding binding 使用

运行方式（在项目根目录）：
    lightrag/.venv/Scripts/python.exe local_embedding_server.py

或通过启动脚本：
    .\start_lightrag.ps1

需要安装 sentence-transformers：
    uv pip install sentence-transformers（在 lightrag/.venv 中）

嵌入维度: 384
"""

import asyncio
import logging
from typing import List

import numpy as np
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
PORT = 9622

app = FastAPI(title="Local Embedding Server")

# Lazy-loaded model instance
_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading model: {MODEL_NAME} ...")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded successfully (dim=384)")
    return _model


class EmbeddingRequest(BaseModel):
    input: List[str] | str
    model: str = MODEL_NAME
    encoding_format: str = "float"


class EmbeddingObject(BaseModel):
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingObject]
    model: str
    usage: dict


@app.on_event("startup")
async def startup_event():
    # Pre-load model on startup
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, get_model)
    logger.info(f"Embedding server ready on port {PORT}")


@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL_NAME, "dim": 384}


@app.post("/v1/embeddings")
async def create_embeddings(req: EmbeddingRequest):
    # Normalize input to list
    texts = req.input if isinstance(req.input, list) else [req.input]

    model = get_model()
    loop = asyncio.get_event_loop()

    def encode_texts():
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.astype(np.float32)

    embeddings = await loop.run_in_executor(None, encode_texts)

    data = [
        EmbeddingObject(embedding=emb.tolist(), index=i)
        for i, emb in enumerate(embeddings)
    ]

    return EmbeddingResponse(
        data=data,
        model=MODEL_NAME,
        usage={"prompt_tokens": sum(len(t.split()) for t in texts), "total_tokens": sum(len(t.split()) for t in texts)},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
