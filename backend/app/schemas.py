"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TransactionInput(BaseModel):
    """Input body for POST /predict."""
    type: str = Field(..., description="TRANSFER, CASH-OUT, PAYMENT, CASH-IN, or DEBIT")
    sender_account: str = Field(..., min_length=3, max_length=30)
    receiver_account: str = Field(..., min_length=3, max_length=30)
    amount: float = Field(..., gt=0)
    sender_balance_before: float = Field(..., ge=0)
    sender_balance_after: float = Field(..., ge=0)
    receiver_balance_before: float = Field(..., ge=0)
    receiver_balance_after: float = Field(..., ge=0)
    # Optional Nigerian-context metadata
    channel: Optional[str] = Field(None, description="APP, USSD, or WEB")
    device_id: Optional[str] = None
    hours_since_sim_change: Optional[float] = None
    is_new_device: Optional[bool] = None
    geo_zone: Optional[int] = None
    distance_from_home_km: Optional[float] = None
    impossible_travel: Optional[bool] = None
    ussd_session_duration: Optional[int] = None
    agent_risk_score: Optional[float] = None


class ShapFeature(BaseModel):
    feature: str
    value: float
    contribution: float


class PredictionResult(BaseModel):
    transaction_id: int
    risk_score: float
    classification: str
    threshold: float
    model_version: str
    shap_top_features: List[ShapFeature]
    latency_ms: int
    timestamp: datetime


class TransactionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    type: str
    sender_account: str
    receiver_account: str
    amount: float
    timestamp: datetime
    risk_score: Optional[float] = None
    classification: Optional[str] = None
    top_feature: Optional[str] = None
    reviewed: bool = False


class TransactionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    prediction_id: Optional[int] = None
    type: str
    sender_account: str
    receiver_account: str
    amount: float
    sender_balance_before: float
    sender_balance_after: float
    receiver_balance_before: float
    receiver_balance_after: float
    channel: Optional[str] = None
    timestamp: datetime
    risk_score: Optional[float] = None
    classification: Optional[str] = None
    threshold: Optional[float] = None
    model_version: Optional[str] = None
    shap_top_features: Optional[List[ShapFeature]] = None
    review_outcome: Optional[str] = None


class ReviewInput(BaseModel):
    prediction_id: int
    outcome: str = Field(..., description="CONFIRMED_FRAUD or FALSE_ALERT")
    notes: Optional[str] = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    review_id: int
    prediction_id: int
    reviewer_id: str
    outcome: str
    notes: Optional[str]
    reviewed_at: datetime


class Stats(BaseModel):
    scored_today: int
    fraud_flagged: int
    under_review: int
    false_positive_rate: float
    total_transactions: int
    total_reviews: int


class RecentAlert(BaseModel):
    transaction_id: int
    amount: float
    type: str
    risk_score: float
    top_feature: str
    classification: str
    status: str
    timestamp: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: Optional[str] = None
