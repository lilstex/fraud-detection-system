"""FastAPI application entry point.

Run:
    uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .database import init_db
from .ml.model_service import get_model_service
from .routers import auth, predict, transactions, reviews, stats, misc


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    print("Starting fraud detection API...")
    init_db()
    get_model_service().load()
    yield
    print("Shutting down.")


app = FastAPI(
    title="Nigerian Mobile Money Fraud Detection API",
    description=(
        "AI-Powered Real-Time Fraud Detection System for Mobile Money Transactions "
        "with Nigerian-Context Feature Adaptation. Built for the MIT Professional "
        "Master's Project at MIVA Open University."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(transactions.router)
app.include_router(reviews.router)
app.include_router(stats.router)
app.include_router(misc.router)


@app.get("/")
async def root():
    return {
        "name": "Nigerian Mobile Money Fraud Detection API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
