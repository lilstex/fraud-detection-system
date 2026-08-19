"""
Train and serialise the three fraud detection models for the app.

Reads the synthetic dataset produced by generate_synthetic_data.py, applies
the feature engineering pipeline, trains Logistic Regression, Random Forest,
and XGBoost with SMOTE, and saves the best model plus its SHAP explainer
to backend/models/.
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (precision_score, recall_score, f1_score,
                              roc_auc_score, confusion_matrix)
import xgboost as xgb
from imblearn.over_sampling import SMOTE
import shap

# Paths
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "..", "data", "synthetic_transactions.csv")
MODELS_DIR = os.path.join(HERE, "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def engineer_features(df):
    """Compute the 14 Nigerian-context features + general features.

    Kept in sync with backend/app/ml/feature_engineering.py so training-time
    and inference-time features are identical.
    """
    out = pd.DataFrame(index=df.index)

    # --- General features ---
    out["tx_velocity_1hr"] = df["tx_velocity_1hr"]
    out["balance_drain_ratio"] = np.where(
        df["oldbalanceOrg"] > 0,
        df["amount"] / df["oldbalanceOrg"],
        0.0
    ).clip(0, 5)
    ts = pd.to_datetime(df["timestamp"])
    out["hour_of_day"] = ts.dt.hour
    out["time_of_day_risk"] = ((ts.dt.hour >= 22) | (ts.dt.hour <= 5)).astype(int)
    out["round_amount_flag"] = ((df["amount"] % 1000 == 0) & (df["amount"] >= 10000)).astype(int)

    # --- Nigerian-context features (Table 3.1) ---
    out["agent_density_zone"] = np.abs(df["geo_zone"] - 12) * 0.04
    out["cashout_agent_risk_score"] = df["agent_risk_score"]
    out["hours_since_sim_change"] = df["hours_since_sim_change"]
    out["sim_change_24hr_flag"] = (df["hours_since_sim_change"] < 24).astype(int)
    out["unique_receivers_1hr"] = df["unique_receivers_1hr"]
    out["beneficiary_fan_out_ratio"] = np.where(
        df["tx_velocity_1hr"] > 0,
        df["unique_receivers_1hr"] / df["tx_velocity_1hr"].clip(lower=1),
        0.0
    )
    out["is_ussd_channel"] = (df["channel"] == "USSD").astype(int)
    out["ussd_session_duration"] = df["ussd_session_duration"]
    out["agent_cashout_repeat_15min"] = df["agent_cashout_repeat_15min"]
    out["cashout_cluster_score"] = np.log1p(df["agent_cashout_repeat_15min"]) * df["agent_risk_score"]
    out["device_changes_7d"] = df["device_changes_7d"]
    out["is_new_device_flag"] = df["is_new_device"]
    out["location_distance_from_typical"] = df["distance_from_home_km"]
    out["impossible_travel_flag"] = df["impossible_travel_flag"]

    # Transaction type one-hot
    for t in ["CASH-OUT", "TRANSFER", "PAYMENT", "CASH-IN", "DEBIT"]:
        out[f"type_{t}"] = (df["type"] == t).astype(int)

    return out


def evaluate(name, y_true, y_pred, y_prob):
    p = precision_score(y_true, y_pred, zero_division=0)
    r = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_prob)
    except Exception:
        auc = float('nan')
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    print(f"  {name:20s}  P={p:.3f}  R={r:.3f}  F1={f1:.3f}  AUC={auc:.3f}  FPR={fpr:.3%}")
    return {"precision": p, "recall": r, "f1": f1, "auc": auc, "fpr": fpr}


print("=" * 70)
print("FRAUD DETECTION MODEL TRAINING")
print("=" * 70)

print(f"\nLoading data from {DATA_PATH}...")
df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df):,} rows.  Fraud rate: {df['isFraud'].mean():.3%}")

print("\nEngineering features...")
X = engineer_features(df)
y = df["isFraud"].values
feature_names = list(X.columns)
print(f"Feature count: {len(feature_names)}")

print("\nSplitting train/validation/test (70/15/15, stratified)...")
X_train_full, X_temp, y_train_full, y_temp = train_test_split(
    X, y, test_size=0.30, stratify=y, random_state=42
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=42
)
print(f"  Train: {X_train_full.shape}  Val: {X_val.shape}  Test: {X_test.shape}")

print("\nStandardising features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_full)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

print("\nApplying SMOTE to training set only...")
smote = SMOTE(sampling_strategy=0.20, random_state=42)
X_train_smote, y_train_smote = smote.fit_resample(X_train_scaled, y_train_full)
print(f"  Balanced train shape: {X_train_smote.shape}")
print(f"  Fraud rate after SMOTE: {y_train_smote.mean():.3%}")

results = {}

# --- Logistic Regression ---
print("\n[1/3] Training Logistic Regression...")
lr = LogisticRegression(max_iter=500, C=1.0, random_state=42)
lr.fit(X_train_smote, y_train_smote)
y_prob = lr.predict_proba(X_test_scaled)[:, 1]
y_pred = (y_prob >= 0.5).astype(int)
results["logistic_regression"] = evaluate("Logistic Regression", y_test, y_pred, y_prob)

# --- Random Forest ---
print("\n[2/3] Training Random Forest...")
rf = RandomForestClassifier(
    n_estimators=100, max_depth=12, min_samples_split=5,
    n_jobs=-1, random_state=42
)
rf.fit(X_train_smote, y_train_smote)
y_prob = rf.predict_proba(X_test_scaled)[:, 1]
y_pred = (y_prob >= 0.5).astype(int)
results["random_forest"] = evaluate("Random Forest", y_test, y_pred, y_prob)

# --- XGBoost ---
print("\n[3/3] Training XGBoost...")
xgb_model = xgb.XGBClassifier(
    n_estimators=200, max_depth=6, learning_rate=0.1,
    subsample=0.9, colsample_bytree=0.9,
    eval_metric='logloss', random_state=42,
    tree_method='hist', n_jobs=-1
)
xgb_model.fit(X_train_smote, y_train_smote)
y_prob = xgb_model.predict_proba(X_test_scaled)[:, 1]
y_pred = (y_prob >= 0.5).astype(int)
results["xgboost"] = evaluate("XGBoost", y_test, y_pred, y_prob)

# Pick the winner by F1
winner = max(results.items(), key=lambda x: x[1]["f1"])
print(f"\n>> Best model by F1: {winner[0]} (F1={winner[1]['f1']:.3f})")

# --- Build SHAP explainer for XGBoost (used at inference) ---
print("\nBuilding SHAP TreeExplainer for XGBoost...")
explainer = shap.TreeExplainer(xgb_model)
# Test the explainer
sample_shap = explainer.shap_values(X_test_scaled[:5])
print(f"  SHAP values shape (sample): {np.array(sample_shap).shape}")

# --- Persist artefacts ---
print("\nSaving model artefacts...")
joblib.dump(xgb_model, os.path.join(MODELS_DIR, "xgboost_model.joblib"))
joblib.dump(rf, os.path.join(MODELS_DIR, "rf_model.joblib"))
joblib.dump(lr, os.path.join(MODELS_DIR, "lr_model.joblib"))
joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.joblib"))
joblib.dump(explainer, os.path.join(MODELS_DIR, "shap_explainer.joblib"))

with open(os.path.join(MODELS_DIR, "feature_names.json"), "w") as f:
    json.dump(feature_names, f, indent=2)

metadata = {
    "model_version": "xgb-v1.0",
    "trained_at": datetime.now(timezone.utc).isoformat(),
    "training_rows": int(len(X_train_smote)),
    "test_rows": int(len(X_test)),
    "feature_count": len(feature_names),
    "results": results,
    "primary_model": "xgboost",
    "threshold": 0.5,
}
with open(os.path.join(MODELS_DIR, "metadata.json"), "w") as f:
    json.dump(metadata, f, indent=2)

print(f"\nSaved to: {MODELS_DIR}")
print("\nDone.")
