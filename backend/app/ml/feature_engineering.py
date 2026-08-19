"""Feature engineering for inference time.

Kept in sync with backend/scripts/train_models.py so that the features
computed at inference are identical to those seen during training.

The function accepts a raw transaction dict (matching TransactionInput) plus
a small account-history dict, and returns an ordered dict of engineered
features keyed by feature name.
"""
from datetime import datetime, timezone
from typing import Dict, Optional


def _defaulted(input_dict: Dict, key: str, default):
    v = input_dict.get(key)
    return default if v is None else v


def compute_features(
    tx: Dict,
    account_history: Optional[Dict] = None,
    now: Optional[datetime] = None,
) -> Dict[str, float]:
    """Compute the full feature vector for one transaction.

    Parameters
    ----------
    tx : dict
        Raw transaction as sent by the client (matches TransactionInput).
    account_history : dict, optional
        Aggregates fetched from the DB for this account. Keys used:
        tx_velocity_1hr, unique_receivers_1hr, device_changes_7d,
        agent_cashout_repeat_15min.
    now : datetime
        Current time (used for time-of-day features).

    Returns
    -------
    Dict[str, float]  ordered feature vector.
    """
    if account_history is None:
        account_history = {}
    if now is None:
        now = datetime.now(timezone.utc)

    amount = float(tx["amount"])
    old_bal = float(tx["sender_balance_before"])

    # --- General features ---
    tx_velocity_1hr = int(_defaulted(account_history, "tx_velocity_1hr", 0))
    balance_drain_ratio = float(min(amount / old_bal, 5.0)) if old_bal > 0 else 0.0
    hour_of_day = int(now.hour)
    time_of_day_risk = 1 if (hour_of_day >= 22 or hour_of_day <= 5) else 0
    round_amount_flag = 1 if (amount % 1000 == 0 and amount >= 10000) else 0

    # --- Nigerian-context features (Table 3.1) ---
    geo_zone = _defaulted(tx, "geo_zone", 12)
    agent_density_zone = float(abs(int(geo_zone) - 12) * 0.04)
    cashout_agent_risk_score = float(_defaulted(tx, "agent_risk_score", 0.0))
    hours_since_sim_change = float(_defaulted(tx, "hours_since_sim_change", 720.0))
    sim_change_24hr_flag = 1 if hours_since_sim_change < 24 else 0
    unique_receivers_1hr = int(_defaulted(account_history, "unique_receivers_1hr", 0))
    beneficiary_fan_out_ratio = (
        unique_receivers_1hr / max(tx_velocity_1hr, 1)
    ) if tx_velocity_1hr > 0 else 0.0
    channel = tx.get("channel", "APP") or "APP"
    is_ussd_channel = 1 if channel == "USSD" else 0
    ussd_session_duration = int(_defaulted(tx, "ussd_session_duration", 0))
    agent_cashout_repeat_15min = int(_defaulted(account_history, "agent_cashout_repeat_15min", 0))
    import math
    cashout_cluster_score = math.log1p(agent_cashout_repeat_15min) * cashout_agent_risk_score
    device_changes_7d = int(_defaulted(account_history, "device_changes_7d", 1))
    is_new_device_flag = 1 if _defaulted(tx, "is_new_device", False) else 0
    location_distance_from_typical = float(_defaulted(tx, "distance_from_home_km", 0.0))
    impossible_travel_flag = 1 if _defaulted(tx, "impossible_travel", False) else 0

    features = {
        # General
        "tx_velocity_1hr": tx_velocity_1hr,
        "balance_drain_ratio": balance_drain_ratio,
        "hour_of_day": hour_of_day,
        "time_of_day_risk": time_of_day_risk,
        "round_amount_flag": round_amount_flag,
        # Nigerian-context
        "agent_density_zone": agent_density_zone,
        "cashout_agent_risk_score": cashout_agent_risk_score,
        "hours_since_sim_change": hours_since_sim_change,
        "sim_change_24hr_flag": sim_change_24hr_flag,
        "unique_receivers_1hr": unique_receivers_1hr,
        "beneficiary_fan_out_ratio": beneficiary_fan_out_ratio,
        "is_ussd_channel": is_ussd_channel,
        "ussd_session_duration": ussd_session_duration,
        "agent_cashout_repeat_15min": agent_cashout_repeat_15min,
        "cashout_cluster_score": cashout_cluster_score,
        "device_changes_7d": device_changes_7d,
        "is_new_device_flag": is_new_device_flag,
        "location_distance_from_typical": location_distance_from_typical,
        "impossible_travel_flag": impossible_travel_flag,
    }
    # One-hot type
    tx_type = tx["type"]
    for t in ["CASH-OUT", "TRANSFER", "PAYMENT", "CASH-IN", "DEBIT"]:
        features[f"type_{t}"] = 1 if tx_type == t else 0

    return features
