from __future__ import annotations
import requests
import os

from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class NewsCollector:
    """
    Collecte les articles de news depuis NewsAPI
    pour une liste de fournisseurs donnés.
    """

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        if not self.api_key:
            raise ValueError("NEWS_API_KEY manquante dans .env")

    def fetch_supplier_news(self, supplier_name: str, days_back: int = 7) -> list[dict]:
        """
        Récupère les articles récents pour un fournisseur donné.

        Args:
            supplier_name: Nom du fournisseur à surveiller
            days_back: Nombre de jours en arrière à chercher

        Returns:
            Liste d'articles sous forme de dictionnaires
        """
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        params = {
            "q": f"{supplier_name} supplier risk disruption",
            "from": from_date,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 20,
            "apiKey": self.api_key,
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()  # lève une exception si status != 200

            data = response.json()

            # On extrait uniquement ce dont on a besoin
            articles = []
            for article in data.get("articles", []):
                articles.append({
                    "supplier_name": supplier_name,
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "published_at": article.get("publishedAt", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "collected_at": datetime.now().isoformat(),
                })

            return articles

        except requests.exceptions.Timeout:
            print(f"Timeout lors de la collecte pour {supplier_name}")
            return []

        except requests.exceptions.RequestException as e:
            print(f"Erreur API pour {supplier_name}: {e}")
            return []

    def fetch_multiple_suppliers(self, suppliers: list[str]) -> list[dict]:
        """
        Collecte les news pour une liste de fournisseurs.
        """
        all_articles = []

        for supplier in suppliers:
            print(f"Collecte news pour : {supplier}")
            articles = self.fetch_supplier_news(supplier)
            all_articles.extend(articles)
            print(f"  → {len(articles)} articles trouvés")

        return all_articles