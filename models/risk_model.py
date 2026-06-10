from __future__ import annotations
import os
import sys
import json
import joblib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler


# Ordre fixe des features — doit correspondre au feature store
FEATURE_NAMES = [
    "neg_article_cnt_7d",
    "neg_article_cnt_30d",
    "avg_relevance_score_7d",
    "article_velocity_7d",
    "commodity_price_change_7d",
    "commodity_volatility_7d",
]

_MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(_MODELS_DIR, "artifacts", "risk_model.joblib")
SCALER_PATH = os.path.join(_MODELS_DIR, "artifacts", "scaler.joblib")
META_PATH   = os.path.join(_MODELS_DIR, "artifacts", "model_meta.json")


def prepare_data(dataset: list[dict]) -> tuple:
    """
    Transforme le dataset en matrices X, y pour sklearn/xgboost.
    """
    X = [[sample[f] for f in FEATURE_NAMES] for sample in dataset]
    y = [sample["risk_label"] for sample in dataset]
    return X, y


def train(dataset: list[dict]) -> dict:
    """
    Entraîne le modèle XGBoost et sauvegarde les artifacts.

    Returns:
        Dict avec les métriques d'évaluation
    """
    os.makedirs("models/artifacts", exist_ok=True)

    X, y = prepare_data(dataset)

    # Split train/test — 80/20
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Normalisation — important pour la stabilité du modèle
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # Modèle XGBoost
    # scale_pos_weight : compense le déséquilibre des classes
    # (50% low risk vs 20% high risk)
    n_negative = sum(1 for label in y_train if label == 0)
    n_positive = sum(1 for label in y_train if label == 1)
    scale_pos_weight = n_negative / n_positive if n_positive > 0 else 1

    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric="logloss",
        verbosity=0,
    )

    model.fit(X_train_scaled, y_train)

    # Évaluation
    y_pred      = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    auc         = roc_auc_score(y_test, y_pred_proba)

    print("\n── Évaluation du modèle ──")
    print(classification_report(y_test, y_pred, target_names=["Low Risk", "High Risk"]))
    print(f"AUC-ROC : {auc:.4f}")

    # Feature importance
    print("\n── Feature Importance ──")
    importances = model.feature_importances_
    for name, imp in sorted(zip(FEATURE_NAMES, importances), key=lambda x: -x[1]):
        bar = "█" * int(imp * 50)
        print(f"  {name:<35} {bar} {imp:.4f}")

    # Sauvegarde des artifacts
    joblib.dump(model,  MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    metrics = {
        "auc_roc":        round(auc, 4),
        "n_train":        len(X_train),
        "n_test":         len(X_test),
        "feature_names":  FEATURE_NAMES,
        "model_version":  "1.0.0",
    }

    with open(META_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n✓ Modèle sauvegardé → {MODEL_PATH}")
    print(f"✓ Scaler sauvegardé → {SCALER_PATH}")
    print(f"✓ Metadata sauvegardée → {META_PATH}")

    return metrics


def load_model():
    """Charge le modèle et le scaler depuis les artifacts."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Modèle introuvable : {MODEL_PATH}")

    model  = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler


def predict_risk_score(feature_vector: list) -> dict:
    """
    Prédit le risk score pour un fournisseur.

    Args:
        feature_vector: Liste de 6 valeurs dans l'ordre FEATURE_NAMES

    Returns:
        Dict avec risk_score (0-100), risk_label, risk_level
    """
    model, scaler = load_model()

    X_scaled = scaler.transform([feature_vector])

    # Probabilité d'être HIGH RISK
    proba_high_risk = model.predict_proba(X_scaled)[0][1]

    # Convertit en score 0-100
    risk_score = round(proba_high_risk * 100, 1)

    # Niveau de risque
    if risk_score < 30:
        risk_level = "LOW"
    elif risk_score < 60:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "proba_high_risk": round(proba_high_risk, 4),
    }