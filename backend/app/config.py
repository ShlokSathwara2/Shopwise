from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
STATIC_DIR = BASE_DIR / "static"
DATABASE_URL = os.getenv("SHOPWISE_DATABASE_URL", f"sqlite:///{(BASE_DIR / 'shopwise.db').as_posix()}")
JWT_SECRET = os.getenv("SHOPWISE_JWT_SECRET", "shopwise-local-dev-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
CORS_ORIGINS = os.getenv("SHOPWISE_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
