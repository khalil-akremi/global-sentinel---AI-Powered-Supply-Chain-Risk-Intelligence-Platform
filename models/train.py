from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.data_generator import generate_synthetic_dataset, save_dataset
from models.risk_model import _MODELS_DIR, train, predict_risk_score

# Génère le dataset
print("── Génération du dataset synthétique ──")
dataset = generate_synthetic_dataset(n_samples=1000)
save_dataset(dataset, os.path.join(_MODELS_DIR, "data", "synthetic_dataset.json"))

# Distribution des labels
n_high = sum(1 for d in dataset if d["risk_label"] == 1)
n_low  = sum(1 for d in dataset if d["risk_label"] == 0)
print(f"Distribution : {n_low} low risk | {n_high} high risk")

# Entraînement
print("\n── Entraînement ──")
metrics = train(dataset)

# Test sur des cas concrets
print("\n── Test sur cas réels ──")

cas_tests = [
    {
        "name": "Fournisseur sain",
        "vector": [0.0, 1.0, 0.5, 0.8, 0.02, 0.03]
    },
    {
        "name": "Fournisseur Samsung actuel",
        "vector": [0.0, 3.0, 0.0, 1.0, 0.22, 0.12]
    },
    {
        "name": "Fournisseur en crise",
        "vector": [5.0, 12.0, 3.5, 3.0, 0.25, 0.20]
    },
]

for cas in cas_tests:
    result = predict_risk_score(cas["vector"])
    emoji  = "🔴" if result["risk_level"] == "HIGH" else "🟡" if result["risk_level"] == "MEDIUM" else "🟢"
    print(f"  {emoji} {cas['name']:<30} score={result['risk_score']:>5} | {result['risk_level']}")