"""Populate the database with sample scored transactions.

Runs the scoring pipeline directly (not via HTTP) so that the dashboard has
data to show on first launch. Uses the sample_transactions.json file which
contains a mix of legitimate and clearly fraudulent patterns.
"""
import json
import os
import sys
import random
from datetime import datetime, timedelta

# Allow imports from the app package when run from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, SessionLocal
from app.models import Transaction, Features, Prediction, Review
from app.ml.model_service import get_model_service
from app.ml.feature_engineering import compute_features

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES_PATH = os.path.join(HERE, "..", "data", "sample_transactions.json")


def _score_and_save(db, tx_dict, ts, svc):
    tx = Transaction(
        type=tx_dict["type"],
        sender_account=tx_dict["sender_account"],
        receiver_account=tx_dict["receiver_account"],
        amount=tx_dict["amount"],
        sender_balance_before=tx_dict["sender_balance_before"],
        sender_balance_after=tx_dict["sender_balance_after"],
        receiver_balance_before=tx_dict["receiver_balance_before"],
        receiver_balance_after=tx_dict["receiver_balance_after"],
        channel=tx_dict.get("channel"),
        device_id=tx_dict.get("device_id"),
        timestamp=ts,
    )
    db.add(tx)
    db.flush()

    # Use the metadata embedded in the sample transaction for history
    history = {
        "tx_velocity_1hr": tx_dict.get("tx_velocity_1hr", 0),
        "unique_receivers_1hr": tx_dict.get("unique_receivers_1hr", 0),
        "device_changes_7d": tx_dict.get("device_changes_7d", 1),
        "agent_cashout_repeat_15min": tx_dict.get("agent_cashout_repeat_15min", 0),
    }
    features = compute_features(tx_dict, history, now=ts)
    risk, cls, top_shap, latency = svc.score(features)

    feat_row = Features(
        transaction_id=tx.transaction_id,
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
    pred = Prediction(
        transaction_id=tx.transaction_id,
        risk_score=risk,
        classification=cls,
        threshold=svc.threshold,
        model_version=svc.model_version,
        shap_top_features=json.dumps(top_shap),
        latency_ms=latency,
        created_at=ts,
    )
    db.add(feat_row)
    db.add(pred)
    return tx, pred, risk


def main():
    print("Initialising DB...")
    init_db()

    svc = get_model_service()
    svc.load()
    if not svc.is_loaded():
        print("ERROR: Model not loaded. Run scripts/train_models.py first.")
        sys.exit(1)

    with open(SAMPLES_PATH) as f:
        samples = json.load(f)
    print(f"Loaded {len(samples)} sample transactions.")

    db = SessionLocal()
    now = datetime.utcnow()

    scored = 0
    flagged = 0
    for i, s in enumerate(samples):
        # Spread timestamps over the past 24 hours
        ts = now - timedelta(minutes=random.randint(1, 24 * 60))
        _, pred, risk = _score_and_save(db, s, ts, svc)
        scored += 1
        if pred.classification == "FRAUD":
            flagged += 1

    db.commit()
    print(f"Scored {scored} transactions; {flagged} flagged as FRAUD.")

    # Add a few sample reviews to show the review workflow
    fraud_preds = (db.query(Prediction)
                     .filter(Prediction.classification == "FRAUD")
                     .limit(2).all())
    for pred in fraud_preds:
        review = Review(
            prediction_id=pred.prediction_id,
            reviewer_id="analyst",
            outcome="CONFIRMED_FRAUD" if pred.risk_score > 0.7 else "FALSE_ALERT",
            notes="Sample review created by seed script.",
            reviewed_at=datetime.utcnow(),
        )
        db.add(review)
    db.commit()
    print(f"Created {len(fraud_preds)} sample reviews.")
    db.close()
    print("Done.")


if __name__ == "__main__":
    main()
