from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.risk_model import predict_risk_score
from features.feature_store import get_feature_vector
from ingestion.database import (
    initialize_risk_scores_table,
    insert_risk_score,
    get_latest_risk_scores,
)

# Seuils d'alerte configurables
ALERT_THRESHOLD = 60.0


def score_all_suppliers(suppliers: list) -> list[dict]:
    """
    Score tous les fournisseurs et stocke les résultats.

    Returns:
        Liste de résultats avec alertes
    """
    initialize_risk_scores_table()

    results = []
    alerts  = []

    print("\n── Risk Scoring ──")
    for supplier in suppliers:

        # Récupère le feature vector depuis le feature store
        vector = get_feature_vector(supplier)

        # Prédit le risk score
        prediction = predict_risk_score(vector)

        # Stocke en DB
        insert_risk_score(
            supplier_name=supplier,
            risk_score=prediction["risk_score"],
            risk_level=prediction["risk_level"],
        )

        # Log
        emoji = "🔴" if prediction["risk_level"] == "HIGH" else \
                "🟡" if prediction["risk_level"] == "MEDIUM" else "🟢"

        print(f"  {emoji} {supplier:<15} "
              f"score={prediction['risk_score']:>5} | "
              f"{prediction['risk_level']}")

        result = {
            "supplier_name": supplier,
            **prediction,
        }
        results.append(result)

        # Détecte les alertes
        if prediction["risk_score"] >= ALERT_THRESHOLD:
            alerts.append(result)

    # Summary
    print(f"\n── Summary ──")
    print(f"Scorés   : {len(results)} fournisseurs")
    print(f"Alertes  : {len(alerts)} fournisseurs à risque élevé")

    if alerts:
        print("\n⚠️  ALERTES :")
        for alert in alerts:
            print(f"  🔴 {alert['supplier_name']} — score {alert['risk_score']}")

    return results


def get_risk_dashboard() -> dict:
    """
    Retourne une vue consolidée pour le dashboard.
    """
    scores = get_latest_risk_scores()

    high   = [s for s in scores if s["risk_level"] == "HIGH"]
    medium = [s for s in scores if s["risk_level"] == "MEDIUM"]
    low    = [s for s in scores if s["risk_level"] == "LOW"]

    return {
        "total_suppliers":  len(scores),
        "high_risk_count":  len(high),
        "medium_risk_count": len(medium),
        "low_risk_count":   len(low),
        "high_risk_suppliers": high,
        "all_scores":       scores,
    }