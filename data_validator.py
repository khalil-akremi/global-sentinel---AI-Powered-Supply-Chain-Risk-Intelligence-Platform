from datetime import datetime
from urllib.parse import urlparse


# Mots-clés qui indiquent un article pertinent pour le risk scoring
RISK_KEYWORDS = [
    "supply chain", "supplier", "disruption", "shortage", "bankruptcy",
    "factory", "manufacturing", "delay", "sanctions", "tariff",
    "geopolitical", "risk", "crisis", "shutdown", "recall", "strike"
]


class ArticleValidator:
    """
    Valide et filtre les articles collectés.
    Rejette les articles non pertinents ou malformés.
    """

    def __init__(self, min_relevance_score: int = 1):
        """
        Args:
            min_relevance_score: Nombre minimum de keywords requis
                                 pour considérer un article pertinent
        """
        self.min_relevance_score = min_relevance_score
        self.stats = {"validated": 0, "rejected": 0, "reasons": {}}

    def _is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _is_valid_date(self, date_str: str) -> bool:
        try:
            datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return True
        except Exception:
            return False

    def _compute_relevance_score(self, article: dict) -> int:
        """
        Compte combien de risk keywords apparaissent
        dans le titre + description de l'article.
        """
        text = " ".join([
            article.get("title", ""),
            article.get("description", ""),
            article.get("supplier_name", ""),
        ]).lower()

        return sum(1 for keyword in RISK_KEYWORDS if keyword in text)

    def _reject(self, article: dict, reason: str) -> None:
        self.stats["rejected"] += 1
        self.stats["reasons"][reason] = self.stats["reasons"].get(reason, 0) + 1
        print(f"  ✗ Rejeté ({reason}): {article.get('title', 'no title')[:60]}")

    def validate(self, article: dict) -> dict | None:
        """
        Valide un article. Retourne l'article enrichi si valide, None sinon.
        """

        # 1. Champs obligatoires présents ?
        if not article.get("title"):
            self._reject(article, "missing_title")
            return None

        if not article.get("url"):
            self._reject(article, "missing_url")
            return None

        # 2. URL valide ?
        if not self._is_valid_url(article["url"]):
            self._reject(article, "invalid_url")
            return None

        # 3. Date valide ?
        if not self._is_valid_date(article.get("published_at", "")):
            self._reject(article, "invalid_date")
            return None

        # 4. Pertinent ?
        relevance_score = self._compute_relevance_score(article)
        if relevance_score < self.min_relevance_score:
            self._reject(article, "not_relevant")
            return None

        # Article valide — on l'enrichit avec son score
        self.stats["validated"] += 1
        print(f"  ✓ Validé (score={relevance_score}): {article['title'][:60]}")

        return {
            **article,
            "relevance_score": relevance_score,
        }

    def validate_batch(self, articles: list[dict]) -> list[dict]:
        """
        Valide une liste d'articles et retourne uniquement les valides.
        """
        validated = []

        for article in articles:
            result = self.validate(article)
            if result:
                validated.append(result)

        print(f"\n── Validation summary ──")
        print(f"Total     : {len(articles)}")
        print(f"Validés   : {self.stats['validated']}")
        print(f"Rejetés   : {self.stats['rejected']}")
        print(f"Raisons   : {self.stats['reasons']}")

        return validated