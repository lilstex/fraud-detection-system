"""
Generate synthetic mobile money transaction data with Nigerian-context metadata.

This mirrors the PaySim structure and augments it with the fields needed for
the Nigerian-context features described in Chapter 3 of the project report:
SIM changes, device identifiers, geographic location, USSD sessions, and
agent history.

Fraud cases receive distributions consistent with the seven Nigerian fraud
patterns identified in the literature (NIBSS 2025; Alao et al. 2022).
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Reproducibility
RNG = np.random.default_rng(42)

# Configuration
N_ROWS = 60_000
FRAUD_RATE = 0.012  # ~1.2% fraud
N_ACCOUNTS = 8_000
N_AGENTS = 400
N_ZONES = 25  # geographic zones (e.g. LGA-level)
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_transactions.csv")


def gen_accounts(n):
    """Generate account IDs."""
    return [f"C{RNG.integers(1_000_000_000, 9_999_999_999)}" for _ in range(n)]


def gen_devices(n_per_account_avg=1.5):
    """Return a per-account device history."""
    device_history = {}
    total_devices = int(N_ACCOUNTS * n_per_account_avg)
    device_ids = [f"D{RNG.integers(100000, 999999)}" for _ in range(total_devices)]
    devices_iter = iter(device_ids)
    for acc in ACCOUNTS:
        # Most accounts have 1-2 devices; some fraud-prone have more
        k = max(1, int(RNG.poisson(1.3)))
        device_history[acc] = [next(devices_iter, f"D{RNG.integers(100000, 999999)}") for _ in range(k)]
    return device_history


print("Generating base accounts and agents...")
ACCOUNTS = gen_accounts(N_ACCOUNTS)
AGENTS = gen_accounts(N_AGENTS)  # agents use same ID format
DEVICE_HISTORY = gen_devices()

# Each account has a "home" zone and a "last SIM change" timestamp
ZONES = list(range(N_ZONES))
account_home_zone = {a: RNG.integers(0, N_ZONES) for a in ACCOUNTS}

# Base date for the simulation
BASE_DATE = datetime(2025, 1, 1, 0, 0, 0)

# Agent risk scores (some agents are high-risk / collusive)
agent_risk = {a: float(np.clip(RNG.beta(1.5, 15), 0, 1)) for a in AGENTS}
# Boost a few agents to explicitly high risk
for a in RNG.choice(AGENTS, size=20, replace=False):
    agent_risk[a] = float(RNG.uniform(0.6, 0.95))


def account_recent_activity(account, current_time, hours_back=1):
    """Placeholder helper. Real velocity is computed later from the DataFrame."""
    return {}


TX_TYPES = ["CASH-OUT", "TRANSFER", "PAYMENT", "CASH-IN", "DEBIT"]
CHANNELS = ["APP", "USSD", "WEB"]

records = []


def sample_amount(is_fraud):
    """Sample transaction amount in NGN."""
    if is_fraud:
        # Fraudsters go for bigger amounts sometimes but also try round-number structuring
        if RNG.random() < 0.35:
            return round(RNG.choice([50000, 100000, 150000, 200000, 500000, 1000000]))
        return round(float(RNG.lognormal(mean=11.5, sigma=1.1)), 2)
    return round(float(RNG.lognormal(mean=9.5, sigma=1.3)), 2)


def sample_type(is_fraud):
    if is_fraud:
        # Fraud skews to CASH-OUT and TRANSFER
        return str(RNG.choice(["CASH-OUT", "TRANSFER", "TRANSFER", "CASH-OUT", "PAYMENT"]))
    return str(RNG.choice(TX_TYPES, p=[0.25, 0.30, 0.30, 0.10, 0.05]))


def sample_channel(is_fraud):
    if is_fraud:
        # Fraud shows more USSD usage (SIM-swap driven)
        return str(RNG.choice(CHANNELS, p=[0.35, 0.55, 0.10]))
    return str(RNG.choice(CHANNELS, p=[0.65, 0.25, 0.10]))


def sample_ussd_duration(channel, is_fraud):
    if channel != "USSD":
        return 0
    if is_fraud:
        return int(RNG.uniform(5, 45))  # rushed sessions
    return int(RNG.uniform(20, 180))  # normal user pace


def sample_last_sim_change(current_time, is_fraud):
    """Return hours since last SIM change."""
    if is_fraud and RNG.random() < 0.45:
        # High chance of recent SIM change
        return float(RNG.uniform(0.5, 48))
    return float(RNG.uniform(120, 8760))  # anywhere from 5 days to 1 year


def sample_device(account, is_fraud):
    """Return (device_id, is_new_flag)."""
    hist = DEVICE_HISTORY[account]
    if is_fraud and RNG.random() < 0.55:
        new_device = f"D{RNG.integers(100000, 999999)}"
        return new_device, True
    return str(RNG.choice(hist)), False


def sample_geo(account, is_fraud):
    """Return (zone, distance_from_home_km)."""
    home = account_home_zone[account]
    if is_fraud and RNG.random() < 0.35:
        # Away from home zone
        zone = int(RNG.integers(0, N_ZONES))
        while zone == home:
            zone = int(RNG.integers(0, N_ZONES))
        distance = float(RNG.uniform(50, 800))
        return zone, distance
    if RNG.random() < 0.85:
        return home, float(RNG.uniform(0, 15))
    return int(RNG.integers(0, N_ZONES)), float(RNG.uniform(15, 60))


def sample_impossible_travel(is_fraud):
    """Rare, only set for a subset of fraud cases."""
    return 1 if (is_fraud and RNG.random() < 0.20) else 0


print(f"Generating {N_ROWS} transactions...")

# We'll build in order of time so velocity features can be computed later
for i in range(N_ROWS):
    if i % 10_000 == 0 and i > 0:
        print(f"  {i:,} done")

    is_fraud = RNG.random() < FRAUD_RATE
    hour_offset = i * (24 * 30 / N_ROWS)  # spread across 30 days
    tx_time = BASE_DATE + timedelta(hours=hour_offset + float(RNG.uniform(-0.5, 0.5)))

    tx_type = sample_type(is_fraud)
    amount = sample_amount(is_fraud)

    sender = str(RNG.choice(ACCOUNTS))
    # For CASH-OUT, receiver is an agent
    if tx_type == "CASH-OUT":
        receiver = str(RNG.choice(AGENTS))
    else:
        receiver = str(RNG.choice(ACCOUNTS))
        while receiver == sender:
            receiver = str(RNG.choice(ACCOUNTS))

    sender_bal_before = round(float(RNG.uniform(amount * 0.9, amount * 10 + 5000)), 2)
    sender_bal_after = round(max(0, sender_bal_before - amount), 2)
    receiver_bal_before = round(float(RNG.uniform(0, 500000)), 2)
    receiver_bal_after = round(receiver_bal_before + amount, 2)

    channel = sample_channel(is_fraud)
    ussd_dur = sample_ussd_duration(channel, is_fraud)
    hours_since_sim = sample_last_sim_change(tx_time, is_fraud)
    device_id, is_new_device = sample_device(sender, is_fraud)
    zone, dist_from_home = sample_geo(sender, is_fraud)
    imp_travel = sample_impossible_travel(is_fraud)

    records.append({
        "step": i,
        "timestamp": tx_time.isoformat(),
        "type": tx_type,
        "amount": amount,
        "nameOrig": sender,
        "oldbalanceOrg": sender_bal_before,
        "newbalanceOrig": sender_bal_after,
        "nameDest": receiver,
        "oldbalanceDest": receiver_bal_before,
        "newbalanceDest": receiver_bal_after,
        # Nigerian-context metadata
        "channel": channel,
        "ussd_session_duration": ussd_dur,
        "hours_since_sim_change": hours_since_sim,
        "device_id": device_id,
        "is_new_device": int(is_new_device),
        "geo_zone": zone,
        "distance_from_home_km": dist_from_home,
        "impossible_travel_flag": imp_travel,
        "agent_risk_score": agent_risk.get(receiver, 0.0) if tx_type == "CASH-OUT" else 0.0,
        "isFraud": int(is_fraud),
    })

df = pd.DataFrame(records)
print(f"Generated {len(df):,} rows | Fraud rate: {df['isFraud'].mean():.3%}")

# Sort by time then compute velocity-style features
df = df.sort_values("timestamp").reset_index(drop=True)
df["timestamp"] = pd.to_datetime(df["timestamp"])

print("Computing per-account rolling features...")
df = df.sort_values(["nameOrig", "timestamp"]).reset_index(drop=True)

# Rolling counts of transactions per sender in prior hour
df["tx_velocity_1hr"] = 0
df["unique_receivers_1hr"] = 0
df["device_changes_7d"] = 0
df["agent_cashout_repeat_15min"] = 0

for name, group in df.groupby("nameOrig"):
    g = group.copy()
    times = g["timestamp"].values.astype("datetime64[m]").astype(int)  # minutes
    receivers = g["nameDest"].values
    devices = g["device_id"].values

    velocities = np.zeros(len(g), dtype=int)
    unique_recs = np.zeros(len(g), dtype=int)
    dev_changes = np.zeros(len(g), dtype=int)

    for i in range(len(g)):
        window_start_1hr = times[i] - 60
        mask_1hr = (times[:i] >= window_start_1hr)
        velocities[i] = int(mask_1hr.sum())
        unique_recs[i] = len(set(receivers[:i][mask_1hr]))
        window_start_7d = times[i] - 60 * 24 * 7
        mask_7d = (times[:i] >= window_start_7d)
        dev_changes[i] = len(set(devices[:i][mask_7d]))

    df.loc[g.index, "tx_velocity_1hr"] = velocities
    df.loc[g.index, "unique_receivers_1hr"] = unique_recs
    df.loc[g.index, "device_changes_7d"] = dev_changes

# Agent-side clustering: cash-outs at same agent within 15 minutes
print("Computing agent cash-out clustering...")
cashout_only = df[df["type"] == "CASH-OUT"].copy()
for agent, group in cashout_only.groupby("nameDest"):
    g = group.sort_values("timestamp")
    times = g["timestamp"].values.astype("datetime64[m]").astype(int)
    counts = np.zeros(len(g), dtype=int)
    for i in range(len(g)):
        window_start = times[i] - 15
        counts[i] = int(((times[:i] >= window_start)).sum())
    df.loc[g.index, "agent_cashout_repeat_15min"] = counts

# Final sort and save
df = df.sort_values("timestamp").reset_index(drop=True)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
df.to_csv(OUT_PATH, index=False)
print(f"Saved: {OUT_PATH}")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
