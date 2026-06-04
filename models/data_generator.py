from __future__ import annotations
import random
import json
import os


def generate_synthetic_dataset(n_samples: int = 1000, seed: int = 42) -> list[dict]:
    """
    Génère un dataset synthétique avec distributions qui se chevauchent.
    Aucune feature seule ne prédit le label — le modèle doit apprendre
    les interactions entre features.
    """
    random.seed(seed)
    dataset = []

    for _ in range(n_samples):
        # Chaque feature est tirée indépendamment
        # avec du bruit pour créer des cas ambigus
        sample = {
            "neg_article_cnt_7d":        max(0, random.gauss(2.0, 2.5)),
            "neg_article_cnt_30d":       max(0, random.gauss(5.0, 4.0)),
            "avg_relevance_score_7d":    max(0, random.gauss(1.5, 1.2)),
            "article_velocity_7d":       max(0, random.gauss(1.2, 0.8)),
            "commodity_price_change_7d": random.gauss(0.05, 0.12),
            "commodity_volatility_7d":   max(0, random.gauss(0.07, 0.06)),
        }

        sample["risk_label"] = _compute_label(sample)
        dataset.append(sample)

    return dataset


def _compute_label(sample: dict) -> int:
    """
    Label basé sur un score composite — aucune feature seule ne suffit.
    Le modèle doit apprendre les interactions.
    """
    score = 0.0

    # Chaque feature contribue partiellement
    score += min(sample["neg_article_cnt_7d"] / 5.0,  1.0) * 0.25
    score += min(sample["neg_article_cnt_30d"] / 10.0, 1.0) * 0.20
    score += min(sample["avg_relevance_score_7d"] / 3.0, 1.0) * 0.20
    score += min(sample["article_velocity_7d"] / 3.0, 1.0) * 0.15
    score += min(abs(sample["commodity_price_change_7d"]) / 0.20, 1.0) * 0.10
    score += min(sample["commodity_volatility_7d"] / 0.15, 1.0) * 0.10

    # Ajoute du bruit pour simuler l'incertitude réelle
    score += random.gauss(0, 0.05)

    return 1 if score >= 0.45 else 0


def save_dataset(dataset: list[dict], path: str = "data/synthetic_dataset.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"✓ Dataset sauvegardé : {len(dataset)} exemples → {path}")


def load_dataset(path: str = "data/synthetic_dataset.json") -> list[dict]:
    with open(path, "r") as f:
        return json.load(f)