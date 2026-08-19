"""Container bootstrap: generate data, train models, seed DB if not already done.

Safe to run every start-up since each step is idempotent.
"""
import os
import sys
from pathlib import Path

# Ensure imports work when run as `python -m scripts.bootstrap`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA_CSV = Path(__file__).resolve().parent.parent / "data" / "synthetic_transactions.csv"
MODEL_FILE = Path(__file__).resolve().parent.parent / "models" / "xgboost_model.joblib"
DB_FILE = Path(__file__).resolve().parent.parent / "fraud_detection.db"


def run(script_name):
    print(f"\n>> Running scripts/{script_name}")
    from importlib import import_module
    mod = import_module(f"scripts.{script_name}")
    if hasattr(mod, "main"):
        mod.main()


def main():
    if not DATA_CSV.exists():
        print(f"Data file missing at {DATA_CSV}, generating.")
        # generate_synthetic_data.py runs at import (top-level code)
        # so we exec it as a script rather than import it
        os.system(f"{sys.executable} {Path(__file__).parent}/generate_synthetic_data.py")
    else:
        print(f"Data file already present at {DATA_CSV}, skipping generation.")

    if not MODEL_FILE.exists():
        print(f"Model artefact missing at {MODEL_FILE}, training.")
        os.system(f"{sys.executable} {Path(__file__).parent}/train_models.py")
    else:
        print(f"Model artefact already present at {MODEL_FILE}, skipping training.")

    if not DB_FILE.exists():
        print(f"Database missing at {DB_FILE}, seeding.")
        os.system(f"{sys.executable} {Path(__file__).parent}/seed_database.py")
    else:
        print(f"Database already present at {DB_FILE}, skipping seed.")

    print("\nBootstrap complete.")


if __name__ == "__main__":
    main()
