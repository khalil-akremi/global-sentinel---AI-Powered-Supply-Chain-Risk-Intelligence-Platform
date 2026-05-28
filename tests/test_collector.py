import pytest
import sys
import os
from unittest.mock import patch, MagicMock

from ingestion.news_collector import NewsCollector


# Fausse réponse API qu'on contrôle
FAKE_API_RESPONSE = {
    "articles": [
        {
            "title": "Samsung supply chain disruption reported",
            "description": "Factory delays affect semiconductor manufacturing",
            "url": "https://example.com/article-1",
            "publishedAt": "2026-05-01T10:00:00Z",
            "source": {"name": "Reuters"},
        },
        {
            "title": "Another Samsung supplier article",
            "description": "Supply risk increases for electronics manufacturer",
            "url": "https://example.com/article-2",
            "publishedAt": "2026-05-01T11:00:00Z",
            "source": {"name": "Bloomberg"},
        },
    ]
}


class TestNewsCollector:

    @patch("ingestion.news_collector.requests.get")
    def test_fetch_returns_articles(self, mock_get):
        """Le collector doit retourner les articles de l'API."""
        # On configure le mock pour retourner notre fausse réponse
        mock_response = MagicMock()
        mock_response.json.return_value = FAKE_API_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        collector = NewsCollector()
        articles = collector.fetch_supplier_news("Samsung")

        assert len(articles) == 2
        assert articles[0]["supplier_name"] == "Samsung"
        assert articles[0]["title"] == "Samsung supply chain disruption reported"

    @patch("news_collector.requests.get")
    def test_fetch_handles_timeout(self, mock_get):
        """Le collector doit retourner une liste vide en cas de timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        collector = NewsCollector()
        articles = collector.fetch_supplier_news("Samsung")

        # Pas d'exception levée, liste vide retournée
        assert articles == []

    @patch("news_collector.requests.get")
    def test_fetch_handles_api_error(self, mock_get):
        """Le collector doit gérer les erreurs API sans planter."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        collector = NewsCollector()
        articles = collector.fetch_supplier_news("Samsung")

        assert articles == []

    @patch("news_collector.requests.get")
    def test_fetch_multiple_suppliers(self, mock_get):
        """fetch_multiple_suppliers doit agréger les résultats."""
        mock_response = MagicMock()
        mock_response.json.return_value = FAKE_API_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        collector = NewsCollector()
        articles = collector.fetch_multiple_suppliers(["Samsung", "TSMC"])

        # 2 suppliers × 2 articles chacun = 4 articles
        assert len(articles) == 4