"""Live recommender used by the FastAPI endpoints.

The offline experiment persists a serving artifact trained on all interactions.
This module loads it lazily, keeps it in memory, and blends:
  - a content-based user profile (TF-IDF cosine), and
  - collaborative signals (item-CF + SVD),
using the weights selected on the validation split.
"""
from __future__ import annotations

import threading
from pathlib import Path

import joblib
import numpy as np
from sklearn.preprocessing import normalize

from ..config import ARTIFACTS_DIR


def _normalise(vector: np.ndarray) -> np.ndarray:
    if vector.size == 0:
        return vector
    lo = float(np.min(vector))
    hi = float(np.max(vector))
    if hi - lo < 1e-12:
        return np.zeros_like(vector)
    return (vector - lo) / (hi - lo)


class Recommender:
    def __init__(self, artifact_path: Path | None = None) -> None:
        self.artifact_path = artifact_path or (ARTIFACTS_DIR / "model.joblib")
        self._artifact: dict | None = None
        self._mtime: float | None = None
        self._lock = threading.Lock()

    def _load(self) -> dict | None:
        if not self.artifact_path.exists():
            return None
        mtime = self.artifact_path.stat().st_mtime
        if self._artifact is not None and self._mtime == mtime:
            return self._artifact
        with self._lock:
            mtime = self.artifact_path.stat().st_mtime
            if self._artifact is None or self._mtime != mtime:
                self._artifact = joblib.load(self.artifact_path)
                self._mtime = mtime
        return self._artifact

    def reload(self) -> None:
        with self._lock:
            self._artifact = None
            self._mtime = None
        self._load()

    @property
    def ready(self) -> bool:
        return self._load() is not None

    def info(self) -> dict:
        artifact = self._load()
        if not artifact:
            return {"ready": False}
        return {
            "ready": True,
            "trained_at": artifact.get("trained_at"),
            "content_weight": artifact.get("alpha"),
            "svd_weight": (1 - artifact.get("alpha", 0.5)) * (1 - artifact.get("beta", 0.5)),
            "item_cf_weight": (1 - artifact.get("alpha", 0.5)) * artifact.get("beta", 0.5),
            "catalog_size": len(artifact.get("item_ids", [])),
            "known_customers": len(artifact.get("user_ids", [])),
            "svd_rank": artifact.get("svd_rank"),
        }

    def _index_for_item(self, artifact: dict, product_id: int) -> int | None:
        return artifact["product_index"].get(int(product_id))

    def _rank(self, scores: np.ndarray, artifact: dict, exclude: set[int], limit: int) -> list[int]:
        item_ids = artifact["item_ids"]
        scores = scores.astype(np.float64, copy=True)
        for pid in exclude:
            idx = artifact["product_index"].get(int(pid))
            if idx is not None:
                scores[idx] = -np.inf
        finite = np.isfinite(scores)
        if not finite.any():
            return []
        top_n = min(len(scores), max(limit * 3, limit + 20))
        candidate_idx = np.argpartition(-scores, top_n - 1)[:top_n]
        candidate_idx = candidate_idx[np.isfinite(scores[candidate_idx])]
        candidate_idx = candidate_idx[np.argsort(-scores[candidate_idx])]
        return [int(item_ids[i]) for i in candidate_idx[:limit]]

    def popular(self, limit: int = 8, exclude: set[int] | None = None) -> list[int]:
        artifact = self._load()
        if not artifact:
            return []
        exclude = exclude or set()
        ordered = [int(pid) for pid in artifact["popularity_order_ids"] if int(pid) not in exclude]
        return ordered[:limit]

    def similar(self, product_id: int, limit: int = 8) -> list[int]:
        artifact = self._load()
        if not artifact:
            return []
        idx = self._index_for_item(artifact, product_id)
        if idx is None:
            return []
        scores = artifact["content_sim"][idx].copy()
        scores[idx] = -np.inf
        top = np.argsort(-scores)[:limit]
        return [int(artifact["item_ids"][i]) for i in top if np.isfinite(scores[i])]

    def also_bought(self, product_id: int, limit: int = 8) -> list[int]:
        artifact = self._load()
        if not artifact:
            return []
        idx = self._index_for_item(artifact, product_id)
        if idx is None:
            return []
        scores = artifact["item_cf_sim"][idx].copy()
        scores[idx] = -np.inf
        top = np.argsort(-scores)[: limit * 2]
        positive = [i for i in top if scores[i] > 0 and np.isfinite(scores[i])]
        if len(positive) < limit:
            content = artifact["content_sim"][idx]
            for i in np.argsort(-content):
                if len(positive) >= limit:
                    break
                if i != idx and i not in positive and content[i] > 0:
                    positive.append(int(i))
        return [int(artifact["item_ids"][i]) for i in positive[:limit]]

    def for_user(
        self,
        user_id: int | None,
        history: dict[int, float],
        exclude: set[int] | None = None,
        limit: int = 8,
    ) -> tuple[list[int], str]:
        artifact = self._load()
        if not artifact:
            return [], "popularity"
        exclude = set(exclude or set())
        if not history:
            return self.popular(limit, exclude), "popularity"

        item_index = artifact["product_index"]
        content_matrix = artifact["content_item_matrix"]
        weights = np.zeros(len(artifact["item_ids"]), dtype=np.float32)
        valid_idx = []
        valid_weights = []
        for pid, weight in history.items():
            idx = item_index.get(int(pid))
            if idx is not None:
                valid_idx.append(idx)
                valid_weights.append(max(float(weight), 0.01))
        if not valid_idx:
            return self.popular(limit, exclude), "popularity"

        weights[valid_idx] = valid_weights
        weighted = content_matrix[valid_idx].multiply(np.array(valid_weights)[:, None]).sum(axis=0)
        profile = normalize(np.asarray(weighted).ravel().reshape(1, -1))
        content_result = profile @ content_matrix.T
        content_scores = content_result.toarray().ravel() if hasattr(content_result, "toarray") else np.asarray(content_result).ravel()
        content_norm = _normalise(content_scores)

        item_cf = artifact["item_cf_sim"]
        cf_raw = np.average(item_cf[valid_idx], axis=0, weights=np.array(valid_weights))
        cf_norm = _normalise(cf_raw)

        alpha = float(artifact.get("alpha", 0.2))
        beta = float(artifact.get("beta", 0.33))
        user_idx = artifact["user_index"].get(int(user_id)) if user_id is not None else None
        if user_idx is not None:
            svd_raw = artifact["svd_user_factors"][user_idx] @ artifact["svd_components"]
            svd_norm = _normalise(svd_raw)
            scores = alpha * content_norm + (1 - alpha) * (beta * cf_norm + (1 - beta) * svd_norm)
            strategy = "hybrid"
        else:
            scores = 0.45 * content_norm + 0.55 * cf_norm
            strategy = "content_cf"

        ranked = self._rank(scores, artifact, exclude | set(history.keys()), limit)
        if len(ranked) < limit:
            for pid in self.popular(limit * 2, exclude | set(history.keys())):
                if pid not in ranked:
                    ranked.append(pid)
                if len(ranked) >= limit:
                    break
        return ranked[:limit], strategy


_recommender: Recommender | None = None


def get_recommender() -> Recommender:
    global _recommender
    if _recommender is None:
        _recommender = Recommender()
    return _recommender
