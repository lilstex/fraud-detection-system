"""Record analyst review decisions."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import get_current_user
from ..models import Prediction, Review
from ..schemas import ReviewInput, ReviewOut

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewOut)
async def create_review(
    body: ReviewInput,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pred = db.query(Prediction).filter(
        Prediction.prediction_id == body.prediction_id
    ).first()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")
    if body.outcome not in ("CONFIRMED_FRAUD", "FALSE_ALERT"):
        raise HTTPException(
            status_code=400,
            detail="outcome must be CONFIRMED_FRAUD or FALSE_ALERT",
        )
    existing = db.query(Review).filter(Review.prediction_id == body.prediction_id).first()
    if existing:
        # Update existing review
        existing.outcome = body.outcome
        existing.notes = body.notes
        existing.reviewer_id = user["username"]
        existing.reviewed_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    review = Review(
        prediction_id=body.prediction_id,
        reviewer_id=user["username"],
        outcome=body.outcome,
        notes=body.notes,
        reviewed_at=datetime.utcnow(),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review
