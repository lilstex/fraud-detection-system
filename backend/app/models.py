"""SQLAlchemy ORM models.

Matches the Entity-Relationship Diagram in Chapter 4:
Transactions 1:1 Features, Transactions 1:1 Predictions, Predictions 1:0..1 Reviews
"""
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Float, DateTime, ForeignKey,
                        Text, Boolean)
from sqlalchemy.orm import relationship
from .database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(20), nullable=False)
    sender_account = Column(String(30), nullable=False, index=True)
    receiver_account = Column(String(30), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    sender_balance_before = Column(Float, nullable=False)
    sender_balance_after = Column(Float, nullable=False)
    receiver_balance_before = Column(Float, nullable=False)
    receiver_balance_after = Column(Float, nullable=False)
    # Optional Nigerian-context metadata (may be null if not supplied)
    channel = Column(String(10), nullable=True)
    device_id = Column(String(30), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    features = relationship("Features", back_populates="transaction",
                             uselist=False, cascade="all, delete-orphan")
    prediction = relationship("Prediction", back_populates="transaction",
                               uselist=False, cascade="all, delete-orphan")


class Features(Base):
    __tablename__ = "features"

    feature_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"),
                             nullable=False, unique=True)
    # Nigerian-context features (Table 3.1)
    agent_density_zone = Column(Float, default=0)
    cashout_agent_risk_score = Column(Float, default=0)
    hours_since_sim_change = Column(Float, default=0)
    sim_change_24hr_flag = Column(Integer, default=0)
    unique_receivers_1hr = Column(Integer, default=0)
    beneficiary_fan_out_ratio = Column(Float, default=0)
    is_ussd_channel = Column(Integer, default=0)
    ussd_session_duration = Column(Integer, default=0)
    agent_cashout_repeat_15min = Column(Integer, default=0)
    cashout_cluster_score = Column(Float, default=0)
    device_changes_7d = Column(Integer, default=0)
    is_new_device_flag = Column(Integer, default=0)
    location_distance_from_typical = Column(Float, default=0)
    impossible_travel_flag = Column(Integer, default=0)
    # General features
    tx_velocity_1hr = Column(Integer, default=0)
    balance_drain_ratio = Column(Float, default=0)
    time_of_day_risk = Column(Integer, default=0)
    round_amount_flag = Column(Integer, default=0)

    transaction = relationship("Transaction", back_populates="features")


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"),
                             nullable=False, unique=True, index=True)
    risk_score = Column(Float, nullable=False)
    classification = Column(String(15), nullable=False, index=True)  # FRAUD | LEGITIMATE
    threshold = Column(Float, nullable=False)
    model_version = Column(String(30), nullable=False)
    shap_top_features = Column(Text, nullable=True)  # JSON
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    transaction = relationship("Transaction", back_populates="prediction")
    review = relationship("Review", back_populates="prediction",
                          uselist=False, cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(Integer, ForeignKey("predictions.prediction_id"),
                            nullable=False, unique=True)
    reviewer_id = Column(String(50), nullable=False)
    outcome = Column(String(20), nullable=False)  # CONFIRMED_FRAUD | FALSE_ALERT
    notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    prediction = relationship("Prediction", back_populates="review")
