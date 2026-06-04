from __future__ import annotations
import os
import sys
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from features.feature_store import upsert_features

load_dotenv()

# Mapping fournisseur → commodités pertinentes
# On utilise les symboles Alpha Vantage
SUPPLIER_COMMODITIES = {
    "Samsung":  ["COPPER"],
    "TSMC":     ["COPPER"],
    "Tesla":    ["COPPER"],
    "Foxconn":  ["COPPER"],
    "BASF":     ["CRUDE_OIL_WTI"],
}

DEFAULT_COMMODITIES = ["COPPER"]

BASE_URL = "https://www.alphavantage.co/query"


def fetch_commodity_data(commodity: str) -> list:
    """
    Récupère les prix mensuels d'une commodité via Alpha Vantage.
    
    Args:
        commodity: Nom Alpha Vantage (ex: COPPER, CRUDE_OIL_WTI)
    
    Returns:
        Liste des 14 derniers prix
    """
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    if not api_key:
        print("  ✗ ALPHA_VANTAGE_KEY manquante dans .env")
        return []

    try:
        params = {
            "function": commodity,
            "interval": "monthly",
            "apikey": api_key,
        }

        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Alpha Vantage retourne {"data": [{"date": "...", "value": "..."}, ...]}
        if "data" not in data:
            print(f"  ✗ Réponse inattendue pour {commodity}: {list(data.keys())}")
            return []

        # On prend les 14 dernières entrées
        prices = []
        for entry in data["data"][:14]:
            try:
                prices.append(float(entry["value"]))
            except (ValueError, KeyError):
                continue

        return prices

    except requests.exceptions.Timeout:
        print(f"  ✗ Timeout pour {commodity}")
        return []
    except Exception as e:
        print(f"  ✗ Erreur pour {commodity}: {e}")
        return []


def compute_commodity_features(supplier_name: str) -> dict:
    """
    Calcule les features commodités pour un fournisseur.
    """
    commodities = SUPPLIER_COMMODITIES.get(supplier_name, DEFAULT_COMMODITIES)

    all_changes = []
    all_volatilities = []

    for commodity in commodities:
        prices = fetch_commodity_data(commodity)

        if len(prices) < 2:
            continue

        mid = len(prices) // 2
        prev_avg = sum(prices[mid:]) / len(prices[mid:])
        curr_avg = sum(prices[:mid]) / len(prices[:mid])

        if prev_avg != 0:
            change = (curr_avg - prev_avg) / prev_avg
        else:
            change = 0.0

        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        volatility = (variance ** 0.5) / mean if mean != 0 else 0.0

        all_changes.append(change)
        all_volatilities.append(volatility)
        print(f"  ✓ {commodity}: change={change:.4f}, volatility={volatility:.4f}")

    avg_change     = sum(all_changes) / len(all_changes) if all_changes else 0.0
    avg_volatility = sum(all_volatilities) / len(all_volatilities) if all_volatilities else 0.0

    features = {
        "commodity_price_change_7d": avg_change,
        "commodity_volatility_7d":   avg_volatility,
    }

    print(f"  {supplier_name} commodities: {features}")
    return features


def compute_and_store_commodity_features(suppliers: list) -> None:
    """
    Calcule et stocke les features commodités pour une liste de fournisseurs.
    """
    for supplier in suppliers:
        features = compute_commodity_features(supplier)
        upsert_features(supplier, features)
        print(f"✓ Commodity features stockées pour {supplier}")