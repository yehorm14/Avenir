"""Optional matcher service: free text -> best-matching careers, using the embedding model.

Run:  MATCHER_MODEL=<path or HF id> python -m uvicorn pathfinder_ml.service:app --port 8081
The app's backend may call it when it is up and fall back to the standard-library tag chain
(ML.match_tags + ML.fit_scores) when it is not. Same response envelope as the main API.

Endpoints:
  GET  /health            -> {ok, data: {model, device, n_careers, loaded}}
  POST /match             body {"text": str, "top_k": int=3}
                          -> {ok, data: {matches: [{soc2020, short_title, score, evidence}], tags: [...], model}}
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .api import ML

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
_REPO = Path(__file__).resolve().parents[3]
DEFAULT_MODEL = "BAAI/bge-base-en-v1.5"


def envelope(data=None, error=None, status=200, **meta):
    return JSONResponse({"ok": error is None, "data": data, "error": error, "meta": meta}, status_code=status)


class MatchRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)


class Matcher:
    def __init__(self, texts_path: Path, model_name: str):
        self.model_name, self.model, self.device = model_name, None, None
        self.texts = json.loads(texts_path.read_text(encoding="utf-8")) if texts_path.is_file() else {}
        self.vecs: dict[str, np.ndarray] = {}

    def load(self) -> None:
        import torch
        from sentence_transformers import SentenceTransformer
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(self.model_name, device=self.device)
        for soc, e in self.texts.items():
            chunks = [c["text"] for c in e["chunks"]] or [e["title"]]
            chunks.append(f"{e['title']}. Skills: {', '.join(e['skills'])}")
            self.vecs[soc] = np.asarray(self.model.encode(chunks, normalize_embeddings=True, show_progress_bar=False))

    def match(self, text: str, top_k: int) -> list[dict]:
        q = np.asarray(self.model.encode([QUERY_PREFIX + text], normalize_embeddings=True, show_progress_bar=False))[0]
        scored = sorted(((float((v @ q).max()), soc) for soc, v in self.vecs.items()), reverse=True)
        return [{"soc2020": soc, "short_title": self.texts[soc]["short_title"], "score": round(s, 4), "evidence": self.texts[soc]["evidence"]}
                for s, soc in scored[:top_k]]


app = FastAPI(title="Pathfinder matcher", version="1.0")
_ml = ML()
_matcher = Matcher(Path(os.environ.get("PATHFINDER_ML_DIR", _REPO / "snapshots" / "ml")) / "career_texts.json",
                   os.environ.get("MATCHER_MODEL", DEFAULT_MODEL))


@app.on_event("startup")
def _startup() -> None:
    try:
        _matcher.load()
    except Exception as ex:  # noqa: BLE001  (service stays up and reports not loaded; backend falls back)
        app.state.load_error = str(ex)


@app.get("/health")
def health():
    loaded = _matcher.model is not None
    return envelope({"model": _matcher.model_name, "device": _matcher.device, "n_careers": len(_matcher.vecs), "loaded": loaded,
                     "error": getattr(app.state, "load_error", None)}, status=200 if loaded else 503)


@app.post("/match")
def match(req: MatchRequest):
    if _matcher.model is None:
        return envelope(error={"code": "matcher_unavailable", "message": "embedding model not loaded; use the tag chain"}, status=503)
    tags = _ml.match_tags(req.text, top_k=5)
    return envelope({"matches": _matcher.match(req.text, req.top_k), "tags": tags, "model": _matcher.model_name},
                    method="embedding max-cosine over ESCO text chunks")
