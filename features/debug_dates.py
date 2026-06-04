# debug_dates.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ingestion.database import get_connection
from datetime import datetime, timedelta

conn = get_connection()
cursor = conn.cursor()

# Vérifier les dates des articles Samsung en DB
cursor.execute("""
    SELECT title, published_at, relevance_score
    FROM raw_articles
    WHERE supplier_name = 'Samsung'
    ORDER BY published_at DESC
""")

rows = cursor.fetchall()
print("Articles Samsung en DB :")
for row in rows:
    print(f"  published_at={row[1]} | score={row[2]} | {row[0][:50]}")

# Vérifier ce que la requête features retourne
day_7 = datetime.now() - timedelta(days=7)
print(f"\nDate cutoff 7d : {day_7}")

cursor.execute("""
    SELECT COUNT(*)
    FROM raw_articles
    WHERE supplier_name = 'Samsung'
      AND published_at >= %s
      AND relevance_score >= 2
""", (day_7,))
print(f"Articles Samsung score>=2 dans 7 derniers jours : {cursor.fetchone()[0]}")

cursor.close()
conn.close()