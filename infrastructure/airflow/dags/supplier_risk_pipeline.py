from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# ── Default arguments appliqués à toutes les tâches ──
default_args = {
    "owner": "sentinel",
    "retries": 3,                           # retry 3 fois si échec
    "retry_delay": timedelta(minutes=5),    # attendre 5 min entre chaque retry
    "email_on_failure": False,
}

# ── Définition du DAG ──
dag = DAG(
    dag_id="supplier_risk_pipeline",
    description="Collecte et stocke les news fournisseurs toutes les heures",
    default_args=default_args,
    schedule_interval="0 * * * *",  # cron : toutes les heures pile
    start_date=datetime(2026, 1, 1),
    catchup=False,                  # ne pas rattraper les runs passés
    tags=["ingestion", "suppliers"],
)


# ── Fonctions exécutées par chaque tâche ──

def collect_news(**context):
    """
    Tâche 1 : Collecte les news depuis NewsAPI.
    Utilise XCom pour passer les données à la tâche suivante.
    """
    from ingestion.news_collector import NewsCollector

    collector = NewsCollector()

    # Liste des fournisseurs à surveiller
    # Plus tard : récupéré depuis la DB dynamiquement
    suppliers = ["Samsung", "TSMC", "Tesla", "Foxconn", "BASF"]

    raw_articles = collector.fetch_multiple_suppliers(suppliers)

    print(f"Collectés : {len(raw_articles)} articles bruts")

    # XCom : mécanisme Airflow pour passer des données entre tâches
    context["ti"].xcom_push(key="raw_articles", value=raw_articles)

    return len(raw_articles)


def validate_articles(**context):
    """
    Tâche 2 : Valide et filtre les articles collectés.
    Récupère les données de la tâche précédente via XCom.
    """
    from ingestion.data_validator import ArticleValidator

    # Récupère les articles de la tâche précédente
    ti = context["ti"]
    raw_articles = ti.xcom_pull(task_ids="collect_news", key="raw_articles")

    if not raw_articles:
        print("Aucun article à valider")
        ti.xcom_push(key="validated_articles", value=[])
        return 0

    validator = ArticleValidator(min_relevance_score=1)
    validated = validator.validate_batch(raw_articles)

    print(f"Validés : {len(validated)}/{len(raw_articles)} articles")

    ti.xcom_push(key="validated_articles", value=validated)

    return len(validated)


def store_articles(**context):
    """
    Tâche 3 : Stocke les articles validés dans PostgreSQL.
    """
    from ingestion.database import initialize_schema, insert_articles

    ti = context["ti"]
    validated_articles = ti.xcom_pull(
        task_ids="validate_articles",
        key="validated_articles"
    )

    if not validated_articles:
        print("Aucun article à stocker")
        return 0

    initialize_schema()
    result = insert_articles(validated_articles)

    print(f"Insérés : {result['inserted']} | Skippés : {result['skipped']}")

    return result["inserted"]


# ── Déclaration des tâches ──

task_collect = PythonOperator(
    task_id="collect_news",
    python_callable=collect_news,
    dag=dag,
)

task_validate = PythonOperator(
    task_id="validate_articles",
    python_callable=validate_articles,
    dag=dag,
)

task_store = PythonOperator(
    task_id="store_articles",
    python_callable=store_articles,
    dag=dag,
)

# ── Définition de l'ordre d'exécution ──
task_collect >> task_validate >> task_store