"""GET /transactions and /transactions/{id}."""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..auth import get_current_user
from ..models import Transaction, Prediction, Review
from ..schemas import TransactionSummary, TransactionDetail, ShapFeature

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=List[TransactionSummary])
async def list_transactions(
    limit: int = Query(50, le=200),
    offset: int = 0,
    classification: Optional[str] = None,
    reviewed: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    q = (db.query(Transaction)
           .options(joinedload(Transaction.prediction).joinedload(Prediction.review))
           .order_by(Transaction.timestamp.desc()))
    if classification:
        q = q.join(Prediction).filter(Prediction.classification == classification.upper())
    results = q.offset(offset).limit(limit).all()

    out: List[TransactionSummary] = []
    for tx in results:
        pred = tx.prediction
        top_feat = None
        if pred and pred.shap_top_features:
            try:
                top = json.loads(pred.shap_top_features)
                if top:
                    top_feat = top[0]["feature"]
            except Exception:
                pass
        reviewed_flag = bool(pred and pred.review)
        if reviewed is not None and reviewed_flag != reviewed:
            continue
        out.append(TransactionSummary(
            transaction_id=tx.transaction_id,
            type=tx.type,
            sender_account=tx.sender_account,
            receiver_account=tx.receiver_account,
            amount=tx.amount,
            timestamp=tx.timestamp,
            risk_score=pred.risk_score if pred else None,
            classification=pred.classification if pred else None,
            top_feature=top_feat,
            reviewed=reviewed_flag,
        ))
    return out


@router.get("/{transaction_id}", response_model=TransactionDetail)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    tx = (db.query(Transaction)
            .options(joinedload(Transaction.prediction).joinedload(Prediction.review))
            .filter(Transaction.transaction_id == transaction_id)
            .first())
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    pred = tx.prediction
    shap_top = None
    if pred and pred.shap_top_features:
        try:
            raw = json.loads(pred.shap_top_features)
            shap_top = [ShapFeature(**f) for f in raw]
        except Exception:
            shap_top = None
    review_outcome = pred.review.outcome if (pred and pred.review) else None

    return TransactionDetail(
        transaction_id=tx.transaction_id,
        prediction_id=pred.prediction_id if pred else None,
        type=tx.type,
        sender_account=tx.sender_account,
        receiver_account=tx.receiver_account,
        amount=tx.amount,
        sender_balance_before=tx.sender_balance_before,
        sender_balance_after=tx.sender_balance_after,
        receiver_balance_before=tx.receiver_balance_before,
        receiver_balance_after=tx.receiver_balance_after,
        channel=tx.channel,
        timestamp=tx.timestamp,
        risk_score=pred.risk_score if pred else None,
        classification=pred.classification if pred else None,
        threshold=pred.threshold if pred else None,
        model_version=pred.model_version if pred else None,
        shap_top_features=shap_top,
        review_outcome=review_outcome,
    )
