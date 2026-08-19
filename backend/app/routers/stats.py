"""GET /stats — dashboard summary numbers, plus /alerts/recent for the home widget."""
import json
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..auth import get_current_user
from ..models import Transaction, Prediction, Review
from ..schemas import Stats, RecentAlert

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=Stats)
async def get_stats(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    scored_today = (db.query(Prediction)
                      .filter(Prediction.created_at >= today_start)
                      .count())
    fraud_flagged = (db.query(Prediction)
                       .filter(Prediction.created_at >= today_start,
                               Prediction.classification == "FRAUD")
                       .count())
    reviewed_ids = db.query(Review.prediction_id).subquery()
    under_review = (db.query(Prediction)
                      .filter(Prediction.classification == "FRAUD",
                              ~Prediction.prediction_id.in_(reviewed_ids))
                      .count())

    total_transactions = db.query(Transaction).count()
    total_reviews = db.query(Review).count()

    # False-positive rate = FALSE_ALERT reviews / all reviews
    fa = db.query(Review).filter(Review.outcome == "FALSE_ALERT").count()
    fpr = (fa / total_reviews) if total_reviews > 0 else 0.0

    return Stats(
        scored_today=scored_today,
        fraud_flagged=fraud_flagged,
        under_review=under_review,
        false_positive_rate=round(fpr, 4),
        total_transactions=total_transactions,
        total_reviews=total_reviews,
    )


@router.get("/alerts/recent", response_model=List[RecentAlert])
async def recent_alerts(
    limit: int = 10,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Return the most recent alerts (fraud + high-scoring transactions)."""
    rows = (db.query(Prediction, Transaction, Review)
              .join(Transaction, Prediction.transaction_id == Transaction.transaction_id)
              .outerjoin(Review, Review.prediction_id == Prediction.prediction_id)
              .order_by(Prediction.created_at.desc())
              .limit(limit)
              .all())

    out: List[RecentAlert] = []
    for pred, tx, review in rows:
        top_feature = "n/a"
        if pred.shap_top_features:
            try:
                top = json.loads(pred.shap_top_features)
                if top:
                    top_feature = top[0]["feature"]
            except Exception:
                pass
        # Status derivation
        if review:
            status = review.outcome
        elif pred.classification == "FRAUD":
            status = "FLAGGED"
        elif pred.risk_score >= 0.35:
            status = "REVIEW"
        else:
            status = "OK"
        out.append(RecentAlert(
            transaction_id=tx.transaction_id,
            amount=tx.amount,
            type=tx.type,
            risk_score=pred.risk_score,
            top_feature=top_feature,
            classification=pred.classification,
            status=status,
            timestamp=pred.created_at,
        ))
    return out
