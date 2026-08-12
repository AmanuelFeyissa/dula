"""Dula AI training/eval runner (standalone GPU project — NOT in the uv workspace).

Runs on external free GPU (Kaggle / Lightning AI / Modal / Colab); see ``ml/README.md``. It
imports the torch-free logic from ``dula-ml`` (install it alongside: ``pip install -e
packages/dula-ml``) so dataset formatting, dedup, contamination checks, evaluation scoring, and
the ship/retire gate are identical to CI. Heavy libraries (torch/transformers/peft/trl/datasets/
mlflow) are imported inside functions so the torch-free steps run without a GPU environment.
"""
