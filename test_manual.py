from news_collector import NewsCollector
from data_validator import ArticleValidator

collector = NewsCollector()
validator = ArticleValidator(min_relevance_score=1)

suppliers = ["Samsung", "TSMC", "tesla"]
raw_articles = collector.fetch_multiple_suppliers(suppliers)

print(f"\n── Validation ──")
validated_articles = validator.validate_batch(raw_articles)

print(f"\nArticles après validation : {len(validated_articles)}/{len(raw_articles)}")

if validated_articles:
    print("\nMeilleur article (relevance score le plus élevé) :")
    best = max(validated_articles, key=lambda x: x["relevance_score"])
    print(f"  Fournisseur : {best['supplier_name']}")
    print(f"  Titre       : {best['title']}")
    print(f"  Score       : {best['relevance_score']}")
    print(f"  Source      : {best['source']}")