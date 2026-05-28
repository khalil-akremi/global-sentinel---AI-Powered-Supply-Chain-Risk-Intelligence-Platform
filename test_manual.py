from news_collector import NewsCollector
from data_validator import ArticleValidator
from database import initialize_schema, insert_articles, get_recent_articles

# Setup
initialize_schema()
collector = NewsCollector()
validator = ArticleValidator(min_relevance_score=1)

# Collect
suppliers = ["Samsung", "TSMC", "Tesla"]
print("── Collecte ──")
raw_articles = collector.fetch_multiple_suppliers(suppliers)

# Validate
print("\n── Validation ──")
validated_articles = validator.validate_batch(raw_articles)

# Store
print("\n── Stockage ──")
result = insert_articles(validated_articles)
print(f"Insérés  : {result['inserted']}")
print(f"Skippés  : {result['skipped']}")

# Verify — relance le script une 2e fois pour tester l'idempotence
print("\n── Vérification depuis la DB ──")
articles_db = get_recent_articles(limit=5)
print(f"Articles en DB : {len(articles_db)}")
for a in articles_db:
    print(f"  [{a['relevance_score']}] {a['supplier_name']} — {a['title'][:50]}")