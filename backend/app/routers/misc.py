"""Miscellaneous endpoints: /health, /compare (rule-based), /admin/model."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..database import get_db
from ..auth import get_current_user, require_admin
from ..schemas import HealthResponse, TransactionInput
from ..ml.model_service import get_model_service
from ..ml.rule_based import rule_based_score
from ..ml.feature_engineering import compute_features
from ..models import Transaction
from sqlalchemy import func

router = APIRouter(tags=["misc"])


@router.get("/health", response_model=HealthResponse)
async def health():
    svc = get_model_service()
    return HealthResponse(
        status="ok",
        model_loaded=svc.is_loaded(),
        model_version=svc.model_version if svc.is_loaded() else None,
    )


@router.post("/compare")
async def compare(
    body: TransactionInput,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Return both ML and rule-based decisions for the same transaction.

    Useful for the Chapter 5 comparison demonstration.
    """
    svc = get_model_service()
    now = datetime.utcnow()

    # Minimal history (fresh account, no priors)
    history = {
        "tx_velocity_1hr": 0,
        "unique_receivers_1hr": 0,
        "device_changes_7d": 1,
        "agent_cashout_repeat_15min": 0,
    }
    tx_dict = body.model_dump()
    features = compute_features(tx_dict, history, now=now)

    ml_result = {}
    if svc.is_loaded():
        risk, cls, shap_top, latency = svc.score(features)
        ml_result = {
            "risk_score": risk, "classification": cls,
            "model_version": svc.model_version, "latency_ms": latency,
            "top_shap_features": shap_top,
        }
    rb = rule_based_score(tx_dict, history)
    return {"ml": ml_result, "rule_based": rb}


@router.post("/admin/model/reload")
async def reload_model(user: dict = Depends(require_admin)):
    """Reload the model artefacts from disk. Admin only."""
    svc = get_model_service()
    svc._loaded = False
    svc.load()
    return {
        "status": "reloaded" if svc.is_loaded() else "failed",
        "model_version": svc.model_version,
    }
