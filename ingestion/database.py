from __future__ import annotations
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """
    Retourne une connexion PostgreSQL.
    Utilise les variables d'environnement du .env
    """
    host = os.getenv("DB_HOST", "localhost")
    connection_kwargs = {
        "port": os.getenv("DB_PORT", 5432),
        "dbname": os.getenv("DB_NAME", "sentinel"),
        "user": os.getenv("DB_USER", "sentinel_user"),
        "password": os.getenv("DB_PASSWORD", "sentinel_pass"),
    }

    try:
        return psycopg2.connect(host=host, **connection_kwargs)
    except psycopg2.OperationalError:
        if host == "postgres":
            return psycopg2.connect(host="localhost", **connection_kwargs)
        raise


def initialize_schema():
    """
    Crée les tables si elles n'existent pas encore.
    Idempotent : peut être appelé plusieurs fois sans erreur.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Table des fournisseurs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(255) UNIQUE NOT NULL,
            country     VARCHAR(100),
            sector      VARCHAR(100),
            created_at  TIMESTAMP DEFAULT NOW()
        );
    """)

    # Table des articles bruts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_articles (
            id               SERIAL PRIMARY KEY,
            supplier_name    VARCHAR(255) NOT NULL,
            title            TEXT NOT NULL,
            description      TEXT,
            url              TEXT UNIQUE NOT NULL,
            source           VARCHAR(255),
            published_at     TIMESTAMP,
            collected_at     TIMESTAMP DEFAULT NOW(),
            relevance_score  INTEGER DEFAULT 0,
            processed        BOOLEAN DEFAULT FALSE
        );
    """)

    # Index pour accélérer les requêtes fréquentes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_supplier
        ON raw_articles(supplier_name);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_published
        ON raw_articles(published_at DESC);
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("✓ Schema initialisé")


def insert_articles(articles: list[dict]) -> dict:
    """
    Insère une liste d'articles validés dans PostgreSQL.
    Idempotent : ignore les doublons via ON CONFLICT.

    Returns:
        dict avec le nombre d'insertions et de skips
    """
    conn = get_connection()
    cursor = conn.cursor()

    inserted = 0
    skipped = 0

    for article in articles:
        try:
            cursor.execute("""
                INSERT INTO raw_articles (
                    supplier_name,
                    title,
                    description,
                    url,
                    source,
                    published_at,
                    collected_at,
                    relevance_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                article["supplier_name"],
                article["title"],
                article.get("description", ""),
                article["url"],
                article.get("source", ""),
                article.get("published_at", ""),
                article.get("collected_at", ""),
                article.get("relevance_score", 0),
            ))

            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        except Exception as e:
            print(f"  ✗ Erreur insertion: {e}")
            conn.rollback()
            continue

    conn.commit()
    cursor.close()
    conn.close()

    return {"inserted": inserted, "skipped": skipped}


def get_recent_articles(supplier_name: str = None, limit: int = 10) -> list[dict]:
    """
    Récupère les articles récents depuis la DB.
    Si supplier_name est None, retourne tous les fournisseurs.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if supplier_name:
        cursor.execute("""
            SELECT * FROM raw_articles
            WHERE supplier_name = %s
            ORDER BY published_at DESC
            LIMIT %s
        """, (supplier_name, limit))
    else:
        cursor.execute("""
            SELECT * FROM raw_articles
            ORDER BY published_at DESC
            LIMIT %s
        """, (limit,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(row) for row in rows]