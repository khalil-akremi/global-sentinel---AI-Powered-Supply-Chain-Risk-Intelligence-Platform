from __future__ import annotations
import os
import sys
import json
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_local = os.path.join(ROOT_DIR, ".env.local")
env_default = os.path.join(ROOT_DIR, ".env")
load_dotenv(env_local if os.path.exists(env_local) else env_default, override=True)

from llm.prompt_templates import SYSTEM_PROMPT, build_risk_report_prompt
from features.feature_store import get_latest_features
from ingestion.database import get_recent_articles, get_latest_risk_scores


# Langfuse setup — optionnel, graceful degradation si pas configuré
try:
    from langfuse import Langfuse
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    )
    LANGFUSE_ENABLED = True
    print("✓ Langfuse connecté")
except Exception:
    LANGFUSE_ENABLED = False
    print("⚠ Langfuse désactivé — tracing non disponible")


def call_llm(system_prompt: str, user_prompt: str, trace_name: str = "risk_report") -> str:
    """
    Appelle OpenRouter et retourne la réponse texte.
    Trace l'appel dans Langfuse si disponible.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY manquante dans .env")

    # Langfuse trace
    trace = None
    generation = None
    if LANGFUSE_ENABLED:
        trace = langfuse.trace(
            name=trace_name,
            metadata={"timestamp": datetime.now().isoformat()}
        )
        generation = trace.generation(
            name="openrouter_call",
            model="mistralai/mistral-nemo",
            input={"system": system_prompt, "user": user_prompt},
        )

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistralai/mistral-nemo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                "temperature": 0.3,    # bas = plus déterministe
                "max_tokens": 1500,
            },
            timeout=30,
        )
        response.raise_for_status()
        raw_json = response.json()
        print("USAGE:", raw_json.get("usage"))
        print("FINISH REASON:", raw_json["choices"][0].get("finish_reason"))
        content = raw_json["choices"][0]["message"]["content"]

        # Log la réponse dans Langfuse
        if generation:
            generation.end(output=content)

        return content

    except Exception as e:
        if generation:
            generation.end(output=str(e), level="ERROR")
        raise


def parse_llm_response(raw_response: str) -> dict:
    """
    Parse la réponse JSON du LLM.
    Robuste aux backticks markdown et texte autour du JSON.
    """
    # Nettoie les backticks markdown
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Enlève première ligne (```json) et dernière (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    # Cherche le JSON
    start = cleaned.find("{")
    end   = cleaned.rfind("}") + 1

    if start == -1 or end == 0:
        return {
            "executive_summary": raw_response,
            "risk_drivers": [],
            "recommendations": [],
            "monitoring_points": [],
        }

    try:
        return json.loads(cleaned[start:end])
    except json.JSONDecodeError:
        return {
            "executive_summary": cleaned,
            "risk_drivers": [],
            "recommendations": [],
            "monitoring_points": [],
        }


def generate_risk_report(
    supplier_name: str,
    risk_score: float,
    risk_level: str,
) -> dict:
    """
    Génère un rapport de risque complet pour un fournisseur.

    Returns:
        Dict avec le rapport structuré + metadata
    """
    # Récupère les features depuis le feature store
    features = get_latest_features(supplier_name)

    # Récupère les articles récents
    recent_articles = get_recent_articles(
        supplier_name=supplier_name,
        limit=5
    )

    # Construit le prompt
    user_prompt = build_risk_report_prompt(
        supplier_name=supplier_name,
        risk_score=risk_score,
        risk_level=risk_level,
        features=features,
        recent_articles=recent_articles,
    )

    # Appelle le LLM
    raw_response = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        trace_name=f"risk_report_{supplier_name}",
    )

    # Parse la réponse
    report = parse_llm_response(raw_response)

    return {
        "supplier_name":    supplier_name,
        "risk_score":       risk_score,
        "risk_level":       risk_level,
        "report":           report,
        "generated_at":     datetime.now().isoformat(),
    }


def generate_alerts_reports(min_score: float = 60.0) -> list[dict]:
    """
    Génère des rapports uniquement pour les fournisseurs
    dont le score dépasse le seuil d'alerte.
    """
    scores = get_latest_risk_scores()
    alerts = [s for s in scores if s["risk_score"] >= min_score]

    if not alerts:
        print("✓ Aucune alerte — tous les fournisseurs sont dans les seuils normaux")
        return []

    print(f"⚠️  {len(alerts)} fournisseur(s) en alerte — génération des rapports...")

    reports = []
    for alert in alerts:
        print(f"\n  Génération rapport pour {alert['supplier_name']}...")
        try:
            report = generate_risk_report(
                supplier_name=alert["supplier_name"],
                risk_score=alert["risk_score"],
                risk_level=alert["risk_level"],
            )
            reports.append(report)
            print(f"  ✓ Rapport généré pour {alert['supplier_name']}")
        except Exception as e:
            print(f"  ✗ Erreur pour {alert['supplier_name']}: {e}")

    return reports