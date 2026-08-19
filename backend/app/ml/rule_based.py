"""Rule-based baseline detector — used for the Chapter 5 comparison.

Implements the four rules described in Section 5.5.1:
  1. TRANSFER or CASH-OUT > NGN 200,000 to a new receiver
  2. Three or more cash-outs at the same agent within 15 minutes
  3. New account (< 30 days) emptied by the transaction
  4. Transaction within 24 hours of a SIM change
"""
from typing import Dict, List


def rule_based_score(tx: Dict, account_history: Dict) -> Dict:
    """Return a fraud decision from the rule-based baseline."""
    triggered_rules: List[str] = []

    amount = float(tx["amount"])
    tx_type = tx.get("type", "")
    hours_since_sim = tx.get("hours_since_sim_change", 720)
    unique_recs = account_history.get("unique_receivers_1hr", 0)
    cashout_repeat = account_history.get("agent_cashout_repeat_15min", 0)
    old_bal = float(tx["sender_balance_before"])
    new_bal = float(tx["sender_balance_after"])

    # Rule 1: large transfer/cash-out to a new receiver
    if tx_type in ("TRANSFER", "CASH-OUT") and amount > 200_000 and unique_recs <= 1:
        triggered_rules.append("R1: large_transfer_to_new_receiver")

    # Rule 2: cash-out clustering at the same agent
    if tx_type == "CASH-OUT" and cashout_repeat >= 3:
        triggered_rules.append("R2: agent_cashout_clustering")

    # Rule 3: account emptied — proxy since we don't have account age here
    if old_bal > 0 and (new_bal / old_bal) < 0.05 and amount > 50_000:
        triggered_rules.append("R3: account_balance_drained")

    # Rule 4: recent SIM change
    if hours_since_sim is not None and float(hours_since_sim) < 24:
        triggered_rules.append("R4: recent_sim_change")

    is_fraud = len(triggered_rules) > 0
    return {
        "classification": "FRAUD" if is_fraud else "LEGITIMATE",
        "risk_score": min(1.0, 0.25 * len(triggered_rules)),
        "triggered_rules": triggered_rules,
    }
