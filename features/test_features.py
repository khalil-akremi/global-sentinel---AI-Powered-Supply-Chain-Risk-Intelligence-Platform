from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from feature_store import initialize_feature_store, get_latest_features, get_feature_vector
from news_features import compute_and_store_news_features
from commodity_features import compute_and_store_commodity_features

suppliers = ["Samsung", "TSMC", "Tesla"]

# Init
initialize_feature_store()

# Calcul
print("\n── News Features ──")
compute_and_store_news_features(suppliers)

print("\n── Commodity Features ──")
compute_and_store_commodity_features(suppliers)

# Vérification
print("\n── Feature Vectors ──")
for supplier in suppliers:
    vector = get_feature_vector(supplier)
    features = get_latest_features(supplier)
    print(f"\n{supplier}:")
    for name, value in features.items():
        print(f"  {name}: {value:.4f}")
    print(f"  Vector: {vector}")