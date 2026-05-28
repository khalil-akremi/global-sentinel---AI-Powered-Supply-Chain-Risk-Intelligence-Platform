import pytest
import sys
import os

from ingestion.data_validator import ArticleValidator


# ── Fixtures : données de test réutilisables ──

@pytest.fixture
def validator():
    """Crée un validator frais pour chaque test."""
    return ArticleValidator(min_relevance_score=1)


@pytest.fixture
def valid_article():
    """Un article valide et pertinent."""
    return {
        "supplier_name": "Samsung",
        "title": "Samsung factory faces supply chain disruption",
        "description": "Manufacturing delays affect semiconductor supplier",
        "url": "https://example.com/samsung-disruption",
        "published_at": "2026-05-01T10:00:00Z",
        "source": "Reuters",
        "collected_at": "2026-05-01T11:00:00Z",
    }


@pytest.fixture
def irrelevant_article():
    """Un article sans keywords de risque."""
    return {
        "supplier_name": "Samsung",
        "title": "Why Japanese companies do so many different things",
        "description": "A look at corporate diversification strategies",
        "url": "https://example.com/japanese-companies",
        "published_at": "2026-05-01T10:00:00Z",
        "source": "Some Blog",
        "collected_at": "2026-05-01T11:00:00Z",
    }


# ── Tests ──

class TestArticleValidator:

    def test_valid_article_passes(self, validator, valid_article):
        """Un article pertinent doit passer la validation."""
        result = validator.validate(valid_article)
        assert result is not None
        assert result["relevance_score"] >= 1

    def test_irrelevant_article_rejected(self, validator, irrelevant_article):
        """Un article sans keywords de risque doit être rejeté."""
        result = validator.validate(irrelevant_article)
        assert result is None

    def test_missing_title_rejected(self, validator, valid_article):
        """Un article sans titre doit être rejeté."""
        valid_article["title"] = ""
        result = validator.validate(valid_article)
        assert result is None

    def test_missing_url_rejected(self, validator, valid_article):
        """Un article sans URL doit être rejeté."""
        valid_article["url"] = ""
        result = validator.validate(valid_article)
        assert result is None

    def test_invalid_url_rejected(self, validator, valid_article):
        """Un article avec une URL malformée doit être rejeté."""
        valid_article["url"] = "not-a-valid-url"
        result = validator.validate(valid_article)
        assert result is None

    def test_invalid_date_rejected(self, validator, valid_article):
        """Un article avec une date invalide doit être rejeté."""
        valid_article["published_at"] = "not-a-date"
        result = validator.validate(valid_article)
        assert result is None

    def test_relevance_score_added(self, validator, valid_article):
        """L'article validé doit avoir un relevance_score ajouté."""
        result = validator.validate(valid_article)
        assert "relevance_score" in result
        assert isinstance(result["relevance_score"], int)

    def test_high_risk_article_scores_higher(self, validator):
        """Un article avec plus de keywords doit avoir un score plus élevé."""
        low_risk = {
            "supplier_name": "TSMC",
            "title": "TSMC supplier delays shipment",
            "description": "Minor delay reported",
            "url": "https://example.com/low-risk",
            "published_at": "2026-05-01T10:00:00Z",
            "source": "Reuters",
            "collected_at": "2026-05-01T11:00:00Z",
        }
        high_risk = {
            "supplier_name": "TSMC",
            "title": "TSMC factory shutdown disruption supplier crisis bankruptcy risk",
            "description": "Major supply chain disruption affecting manufacturing",
            "url": "https://example.com/high-risk",
            "published_at": "2026-05-01T10:00:00Z",
            "source": "Reuters",
            "collected_at": "2026-05-01T11:00:00Z",
        }
        low_result = validator.validate(low_risk)
        high_result = validator.validate(high_risk)

        assert high_result["relevance_score"] > low_result["relevance_score"]

    def test_batch_validation_count(self, validator, valid_article, irrelevant_article):
        """validate_batch doit retourner uniquement les articles valides."""
        articles = [valid_article, irrelevant_article]
        result = validator.validate_batch(articles)
        assert len(result) == 1


class TestValidatorStats:

    def test_stats_track_rejections(self, validator, valid_article, irrelevant_article):
        """Les stats doivent tracker les rejets correctement."""
        validator.validate(valid_article)
        validator.validate(irrelevant_article)

        assert validator.stats["validated"] == 1
        assert validator.stats["rejected"] == 1
        assert "not_relevant" in validator.stats["reasons"]