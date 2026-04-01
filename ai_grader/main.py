import os
import threading
from functools import lru_cache

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

_model: SentenceTransformer | None = None
_model_ready = threading.Event()


def _load_model():
    global _model
    _model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    _model_ready.set()


# Load model in background so the container starts immediately and the
# healthcheck can detect readiness separately.
threading.Thread(target=_load_model, daemon=True).start()


@lru_cache(maxsize=128)
def _embed(text: str):
    _model_ready.wait()  # block until model is loaded
    return _model.encode([text])


class CompareRequest(BaseModel):
    student_answer: str
    reference_answer: str


@app.get("/health")
def health():
    if _model_ready.is_set():
        return {"status": "ready"}
    return JSONResponse({"status": "loading"}, status_code=503)


@app.post("/compare")
def compare(req: CompareRequest):
    student = req.student_answer.strip()
    reference = req.reference_answer.strip()

    cached_before = _embed.cache_info().hits
    student_vec = _embed(student)
    reference_vec = _embed(reference)
    cached = _embed.cache_info().hits > cached_before

    score = float(cosine_similarity(student_vec, reference_vec)[0][0])
    return {"similarity_score": score, "cached": cached}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
