from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select

from .config import CORS_ORIGINS, FRONTEND_DIST, STATIC_DIR
from .database import Base, SessionLocal, engine
from .models import Interaction, Order, Product, User
from .routers import admin, auth, cart, events, orders, products, recommendations
from .ml.recommender import get_recommender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("shopwise")

app = FastAPI(
    title="Shopwise API",
    description=(
        "A complete e-commerce backend with authentication, catalogue, cart, checkout, "
        "order history, admin analytics and a hybrid recommendation engine."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def access_log(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - started) * 1000
    if request.url.path.startswith("/api"):
        logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, elapsed)
    response.headers["X-Process-Time-Ms"] = f"{elapsed:.2f}"
    return response


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(engine)
    logger.info("Shopwise API ready | static=%s | frontend=%s", STATIC_DIR, FRONTEND_DIST if FRONTEND_DIST.exists() else "dev mode")
    if not get_recommender().ready:
        logger.warning("Recommendation artifact not found - falling back to popularity. Run the training pipeline.")


app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(events.router)
app.include_router(recommendations.router)
app.include_router(admin.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/api/health", tags=["system"])
def health() -> dict:
    db = SessionLocal()
    try:
        counts = {
            "products": db.scalar(select(func.count(Product.id)).where(Product.is_active.is_(True))),
            "customers": db.scalar(select(func.count(User.id)).where(User.is_admin.is_(False))),
            "orders": db.scalar(select(func.count(Order.id))),
            "interactions": db.scalar(select(func.count(Interaction.id))),
        }
    finally:
        db.close()
    return {
        "status": "ok",
        "service": "Shopwise API",
        "counts": counts,
        "recommender": get_recommender().info(),
    }


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        if full_path.startswith(("api", "static")):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")

else:
    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {
            "service": "Shopwise API",
            "message": "API is running. Start the React app with `npm run dev` in the frontend folder.",
            "docs": "/api/docs",
            "health": "/api/health",
        }
