from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import yfinance as yf
from datetime import datetime, timedelta
from features.feature_store import upsert_features


# Mapping fournisseur → commodités pertinentes
# Un fournisseur de semi-conducteurs dépend du silicium et du cuivre
# Un fournisseur automobile dépend de l'acier et du lithium
SUPPLIER_COMMODITIES = {
    "Samsung":  ["^GSPC", "GC=F"],      # S&P500, Gold
    "TSMC":     ["^GSPC", "HG=F"],      # S&P500, Copper
    "Tesla":    ["HG=F", "ALI=F"],      # Copper, Aluminum
    "Foxconn":  ["^GSPC", "HG=F"],      # S&P500, Copper
    "BASF":     ["CL=F", "NG=F"],       # Crude Oil, Natural Gas
}

# Commodités par défaut si fournisseur non mappé
DEFAULT_COMMODITIES = ["^GSPC", "GC=F"]


def fetch_commodity_data(ticker: str, days_back: int = 14) -> list:
    """
    Récupère les prix historiques d'une commodité via Yahoo Finance.

    Args:
        ticker: Symbole Yahoo Finance (ex: "GC=F" pour l'or)
        days_back: Nombre de jours d'historique

    Returns:
        Liste de prix de clôture
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        data = yf.download(
            ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            progress=False,
        )

        if data.empty:
            print(f"  ✗ Pas de données pour {ticker}")
            return []

        prices = data["Close"].dropna().tolist()
        return prices

    except Exception as e:
        print(f"  ✗ Erreur Yahoo Finance pour {ticker}: {e}")
        return []


def compute_commodity_features(supplier_name: str) -> dict:
    """
    Calcule les features commodités pour un fournisseur.

    Features calculées :
    - commodity_price_change_7d : variation moyenne du prix sur 7 jours
    - commodity_volatility_7d   : écart-type des prix sur 7 jours
    """
    tickers = SUPPLIER_COMMODITIES.get(supplier_name, DEFAULT_COMMODITIES)

    all_changes = []
    all_volatilities = []

    for ticker in tickers:
        prices = fetch_commodity_data(ticker, days_back=14)

        if len(prices) < 2:
            continue

        # Variation sur 7 jours
        # On compare la dernière semaine à la semaine précédente
        mid = len(prices) // 2
        prev_avg = sum(prices[:mid]) / len(prices[:mid])
        curr_avg = sum(prices[mid:]) / len(prices[mid:])

        if prev_avg != 0:
            change = (curr_avg - prev_avg) / prev_avg
        else:
            change = 0.0

        # Volatilité = écart-type normalisé
        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        volatility = (variance ** 0.5) / mean if mean != 0 else 0.0

        all_changes.append(change)
        all_volatilities.append(volatility)

    # Moyenne sur toutes les commodités du fournisseur
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