"""Model loading and inference service (singleton).

Loads the trained XGBoost model, the fitted scaler, the SHAP TreeExplainer,
and the feature-name manifest at process start-up. Exposes score() and
explain() for use by the /predict endpoint.
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np

from ..config import MODELS_DIR, DEFAULT_THRESHOLD, TOP_SHAP_FEATURES


class ModelService:
    """Singleton wrapping the primary model, scaler, and SHAP explainer."""

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self.model = None
        self.scaler = None
        self.explainer = None
        self.feature_names: List[str] = []
        self.metadata: Dict = {}
        self.model_version = "unknown"
        self.threshold = DEFAULT_THRESHOLD
        self._loaded = False

    def load(self) -> None:
        """Load all artefacts. Idempotent."""
        if self._loaded:
            return
        if not self.models_dir.exists():
            print(f"[ModelService] Models directory not found: {self.models_dir}")
            print("[ModelService] Train first: python scripts/train_models.py")
            return
        try:
            self.model = joblib.load(self.models_dir / "xgboost_model.joblib")
            self.scaler = joblib.load(self.models_dir / "scaler.joblib")
            self.explainer = joblib.load(self.models_dir / "shap_explainer.joblib")
            with open(self.models_dir / "feature_names.json") as f:
                self.feature_names = json.load(f)
            with open(self.models_dir / "metadata.json") as f:
                self.metadata = json.load(f)
            self.model_version = self.metadata.get("model_version", "xgb-v1.0")
            self.threshold = float(self.metadata.get("threshold", DEFAULT_THRESHOLD))
            self._loaded = True
            print(f"[ModelService] Loaded model {self.model_version} "
                  f"with {len(self.feature_names)} features.")
        except Exception as e:
            print(f"[ModelService] Failed to load artefacts: {e}")
            self._loaded = False

    def is_loaded(self) -> bool:
        return self._loaded

    def _to_vector(self, features: Dict[str, float]) -> np.ndarray:
        vec = np.zeros((1, len(self.feature_names)), dtype=float)
        for i, name in enumerate(self.feature_names):
            vec[0, i] = float(features.get(name, 0.0))
        return vec

    def score(self, features: Dict[str, float],
              threshold: Optional[float] = None
              ) -> Tuple[float, str, List[Dict], int]:
        """Score a transaction. Returns (risk_score, classification,
        shap_top_features, latency_ms)."""
        if not self._loaded:
            raise RuntimeError("Model not loaded. Run scripts/train_models.py first.")

        threshold = threshold if threshold is not None else self.threshold
        t0 = time.perf_counter()

        # Order features and scale
        raw_vec = self._to_vector(features)
        scaled_vec = self.scaler.transform(raw_vec)

        # Predict probability
        prob = float(self.model.predict_proba(scaled_vec)[0, 1])
        classification = "FRAUD" if prob >= threshold else "LEGITIMATE"

        # SHAP contributions
        shap_values = self.explainer.shap_values(scaled_vec)
        # For XGBoost binary classifier TreeExplainer returns a single array
        if isinstance(shap_values, list):
            shap_arr = np.array(shap_values[1] if len(shap_values) > 1 else shap_values[0])[0]
        else:
            shap_arr = np.array(shap_values)[0]

        # Pick top-N by absolute contribution
        abs_shap = np.abs(shap_arr)
        top_idx = np.argsort(abs_shap)[::-1][:TOP_SHAP_FEATURES]
        top = [
            {
                "feature": self.feature_names[i],
                "value": float(raw_vec[0, i]),
                "contribution": float(shap_arr[i]),
            }
            for i in top_idx
        ]

        latency_ms = int((time.perf_counter() - t0) * 1000)
        return prob, classification, top, latency_ms


# Module-level singleton
_service = ModelService()


def get_model_service() -> ModelService:
    return _service
