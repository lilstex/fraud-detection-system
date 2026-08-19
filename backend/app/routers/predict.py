"""POST /predict — the main scoring endpoint."""
import json
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..database import get_db
from ..auth import get_current_user
from ..models import Transaction, Features, Prediction
from ..schemas import TransactionInput, PredictionResult, ShapFeature
from ..ml.feature_engineering import compute_features
from ..ml.model_service import get_model_service

router = APIRouter(prefix="/predict", tags=["predict"])


def _fetch_account_history(db: Session, sender: str, receiver: str,
                            tx_type: str, now: datetime) -> Dict:
    """Compute rolling features from the DB for this sender/agent."""
    one_hour_ago = now - timedelta(hours=1)
    seven_days_ago = now - timedelta(days=7)
    fifteen_min_ago = now - timedelta(minutes=15)

    # tx_velocity_1hr
    tx_velocity_1hr = (db.query(Transaction)
                         .filter(Transaction.sender_account == sender,
                                 Transaction.timestamp >= one_hour_ago)
                         .count())

    # unique_receivers_1hr
    unique_recs = (db.query(func.count(func.distinct(Transaction.receiver_account)))
                     .filter(Transaction.sender_account == sender,
                             Transaction.timestamp >= one_hour_ago)
                     .scalar() or 0)

    # device_changes_7d
    device_changes = (db.query(func.count(func.distinct(Transaction.device_id)))
                        .filter(Transaction.sender_account == sender,
                                Transaction.device_id != None,  # noqa: E711
                                Transaction.timestamp >= seven_days_ago)
                        .scalar() or 0)

    # agent_cashout_repeat_15min (cash-outs at same agent in last 15 min)
    if tx_type == "CASH-OUT":
        cashout_repeat = (db.query(Transaction)
                            .filter(Transaction.receiver_account == receiver,
                                    Transaction.type == "CASH-OUT",
                                    Transaction.timestamp >= fifteen_min_ago)
                            .count())
    else:
        cashout_repeat = 0

    return {
        "tx_velocity_1hr": tx_velocity_1hr,
        "unique_receivers_1hr": unique_recs,
        "device_changes_7d": max(1, device_changes),
        "agent_cashout_repeat_15min": cashout_repeat,
    }


@router.post("", response_model=PredictionResult)
async def predict(
    body: TransactionInput,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Score a transaction and return the risk score plus SHAP explanation."""
    svc = get_model_service()
    if not svc.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not available. Please run scripts/train_models.py first.",
        )

    # Persist the raw transaction first (so history queries can see it if desired)
    now = datetime.utcnow()
    tx_row = Transaction(
        type=body.type,
        sender_account=body.sender_account,
        receiver_account=body.receiver_account,
        amount=body.amount,
        sender_balance_before=body.sender_balance_before,
        sender_balance_after=body.sender_balance_after,
        receiver_balance_before=body.receiver_balance_before,
        receiver_balance_after=body.receiver_balance_after,
        channel=body.channel,
        device_id=body.device_id,
        timestamp=now,
    )
    db.add(tx_row)
    db.flush()  # get transaction_id

    # Fetch account history (excluding current tx since it isn't committed)
    history = _fetch_account_history(
        db, body.sender_account, body.receiver_account, body.type, now
    )

    # Compute features
    tx_dict = body.model_dump()
    features = compute_features(tx_dict, history, now=now)

    # Score
    try:
        risk_score, classification, top_shap, latency_ms = svc.score(features)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Scoring error: {e}")

    # Save Features + Prediction rows
    feat_row = Features(
        transaction_id=tx_row.transaction_id,
        agent_density_zone=features["agent_density_zone"],
        cashout_agent_risk_score=features["cashout_agent_risk_score"],
        hours_since_sim_change=features["hours_since_sim_change"],
        sim_change_24hr_flag=features["sim_change_24hr_flag"],
        unique_receivers_1hr=features["unique_receivers_1hr"],
        beneficiary_fan_out_ratio=features["beneficiary_fan_out_ratio"],
        is_ussd_channel=features["is_ussd_channel"],
        ussd_session_duration=features["ussd_session_duration"],
        agent_cashout_repeat_15min=features["agent_cashout_repeat_15min"],
        cashout_cluster_score=features["cashout_cluster_score"],
        device_changes_7d=features["device_changes_7d"],
        is_new_device_flag=features["is_new_device_flag"],
        location_distance_from_typical=features["location_distance_from_typical"],
        impossible_travel_flag=features["impossible_travel_flag"],
        tx_velocity_1hr=features["tx_velocity_1hr"],
        balance_drain_ratio=features["balance_drain_ratio"],
        time_of_day_risk=features["time_of_day_risk"],
        round_amount_flag=features["round_amount_flag"],
    )
    pred_row = Prediction(
        transaction_id=tx_row.transaction_id,
        risk_score=risk_score,
        classification=classification,
        threshold=svc.threshold,
        model_version=svc.model_version,
        shap_top_features=json.dumps(top_shap),
        latency_ms=latency_ms,
        created_at=now,
    )
    db.add(feat_row)
    db.add(pred_row)
    db.commit()

    return PredictionResult(
        transaction_id=tx_row.transaction_id,
        risk_score=risk_score,
        classification=classification,
        threshold=svc.threshold,
        model_version=svc.model_version,
        shap_top_features=[ShapFeature(**f) for f in top_shap],
        latency_ms=latency_ms,
        timestamp=now,
    )
