from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ingestion.database import get_connection


def initialize_feature_store():
    """
    Crée la table feature store si elle n'existe pas.
    Idempotent.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supplier_features (
            id             SERIAL PRIMARY KEY,
            supplier_name  VARCHAR(255) NOT NULL,
            feature_name   VARCHAR(255) NOT NULL,
            feature_value  FLOAT NOT NULL,
            computed_day   DATE NOT NULL DEFAULT CURRENT_DATE,
            computed_at    TIMESTAMP DEFAULT NOW(),

            -- Contrainte : une seule valeur par feature par supplier par jour
            UNIQUE(supplier_name, feature_name, computed_day)
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_features_supplier
        ON supplier_features(supplier_name);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_features_computed
        ON supplier_features(computed_at DESC);
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✓ Feature store initialisé")


def upsert_features(supplier_name: str, features: dict) -> None:
    """
    Insère ou met à jour les features d'un fournisseur.
    Si une feature existe déjà aujourd'hui, on la met à jour.

    Args:
        supplier_name: Nom du fournisseur
        features: Dict {feature_name: feature_value}
    """
    conn = get_connection()
    cursor = conn.cursor()

    for feature_name, feature_value in features.items():
        cursor.execute("""
            INSERT INTO supplier_features (supplier_name, feature_name, feature_value, computed_day)
            VALUES (%s, %s, %s, CURRENT_DATE)
            ON CONFLICT (supplier_name, feature_name, computed_day)
            DO UPDATE SET
                feature_value = EXCLUDED.feature_value,
                computed_at   = NOW()
        """, (supplier_name, feature_name, float(feature_value)))

    conn.commit()
    cursor.close()
    conn.close()


def get_latest_features(supplier_name: str) -> dict:
    """
    Récupère les dernières features connues pour un fournisseur.

    Returns:
        Dict {feature_name: feature_value}
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT ON (feature_name)
            feature_name,
            feature_value,
            computed_at
        FROM supplier_features
        WHERE supplier_name = %s
        ORDER BY feature_name, computed_at DESC
    """, (supplier_name,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return {row[0]: row[1] for row in rows}


def get_feature_vector(supplier_name: str) -> list:
    """
    Retourne les features sous forme de vecteur ordonné.
    C'est ce que le modèle ML va consommer.
    """
    features = get_latest_features(supplier_name)

    # Ordre fixe — critique pour la reproductibilité du modèle
    feature_order = [
        "neg_article_cnt_7d",
        "neg_article_cnt_30d",
        "avg_relevance_score_7d",
        "article_velocity_7d",
        "commodity_price_change_7d",
        "commodity_volatility_7d",
    ]

    return [features.get(f, 0.0) for f in feature_order]