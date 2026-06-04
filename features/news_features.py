from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
from ingestion.database import get_connection
from features.feature_store import upsert_features


def compute_news_features(supplier_name: str) -> dict:
    """
    Calcule toutes les features news pour un fournisseur donné.

    Features calculées :
    - neg_article_cnt_7d   : articles avec relevance >= 2 sur 7 jours
    - neg_article_cnt_30d  : même chose sur 30 jours
    - avg_relevance_7d     : score moyen sur 7 jours
    - article_velocity_7d  : ratio articles semaine N / semaine N-1
    """
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    day_7  = now - timedelta(days=7)
    day_14 = now - timedelta(days=14)
    day_30 = now - timedelta(days=30)

    # ── Feature 1 : nombre d'articles à risque élevé sur 7 jours ──
    cursor.execute("""
        SELECT COUNT(*)
        FROM raw_articles
        WHERE supplier_name = %s
          AND published_at >= %s
          AND relevance_score >= 2
    """, (supplier_name, day_7))
    neg_7d = cursor.fetchone()[0]

    # ── Feature 2 : même chose sur 30 jours ──
    cursor.execute("""
        SELECT COUNT(*)
        FROM raw_articles
        WHERE supplier_name = %s
          AND published_at >= %s
          AND relevance_score >= 2
    """, (supplier_name, day_30))
    neg_30d = cursor.fetchone()[0]

    # ── Feature 3 : score moyen sur 7 jours ──
    cursor.execute("""
        SELECT COALESCE(AVG(relevance_score), 0.0)
        FROM raw_articles
        WHERE supplier_name = %s
          AND published_at >= %s
    """, (supplier_name, day_7))
    avg_relevance_7d = float(cursor.fetchone()[0])

    # ── Feature 4 : article velocity ──
    # Compare le volume de la semaine courante vs semaine précédente
    # Ratio > 1 = accélération du signal = potentiellement plus risqué
    cursor.execute("""
        SELECT COUNT(*)
        FROM raw_articles
        WHERE supplier_name = %s
          AND published_at >= %s
          AND published_at < %s
    """, (supplier_name, day_14, day_7))
    prev_week_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM raw_articles
        WHERE supplier_name = %s
          AND published_at >= %s
    """, (supplier_name, day_7))
    curr_week_count = cursor.fetchone()[0]

    # Évite la division par zéro
    if prev_week_count == 0:
        velocity = 1.0 if curr_week_count == 0 else 2.0
    else:
        velocity = curr_week_count / prev_week_count

    cursor.close()
    conn.close()

    features = {
        "neg_article_cnt_7d":  float(neg_7d),
        "neg_article_cnt_30d": float(neg_30d),
        "avg_relevance_score_7d": avg_relevance_7d,
        "article_velocity_7d": velocity,
    }

    print(f"  {supplier_name}: {features}")
    return features


def compute_and_store_news_features(suppliers: list) -> None:
    """
    Calcule et stocke les features news pour une liste de fournisseurs.
    C'est cette fonction qu'Airflow va appeler.
    """
    for supplier in suppliers:
        features = compute_news_features(supplier)
        upsert_features(supplier, features)
        print(f"✓ Features stockées pour {supplier}")