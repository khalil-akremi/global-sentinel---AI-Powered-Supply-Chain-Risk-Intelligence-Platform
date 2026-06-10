from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from llm.report_generator import generate_risk_report, generate_alerts_reports
import json
from dotenv import load_dotenv
from llm.report_generator import call_llm, parse_llm_response
from llm.prompt_templates import SYSTEM_PROMPT, build_risk_report_prompt

# Test raw response
user_prompt = build_risk_report_prompt(
    supplier_name="Foxconn",
    risk_score=65.3,
    risk_level="HIGH",
    features={"neg_article_cnt_7d": 2, "neg_article_cnt_30d": 5,
              "avg_relevance_score_7d": 1.5, "article_velocity_7d": 1.8,
              "commodity_price_change_7d": 0.22, "commodity_volatility_7d": 0.12},
    recent_articles=[],
)

raw = call_llm(SYSTEM_PROMPT, user_prompt)
print("RAW RESPONSE:")
print(repr(raw))

# Parse the raw response
parsed = parse_llm_response(raw)
print("\nPARSED RESPONSE:")
print(json.dumps(parsed, indent=2))

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_local = os.path.join(ROOT_DIR, ".env.local")
load_dotenv(env_local, override=True)

print("OPENROUTER_API_KEY:", os.getenv("OPENROUTER_API_KEY", "NOT FOUND"))
print("LANGFUSE_PUBLIC_KEY:", os.getenv("LANGFUSE_PUBLIC_KEY", "NOT FOUND"))

# Test 1 — rapport pour Foxconn (HIGH RISK)
print("── Test rapport Foxconn ──\n")
report = generate_risk_report(
    supplier_name="Foxconn",
    risk_score=65.3,
    risk_level="HIGH",
)

print(f"Fournisseur : {report['supplier_name']}")
print(f"Score       : {report['risk_score']}")
print(f"Niveau      : {report['risk_level']}")
print(f"\nRapport :")
print(json.dumps(report["report"], indent=2))

# Test 2 — génère tous les rapports d'alerte
print("\n── Rapports d'alerte (score >= 60) ──\n")
alerts = generate_alerts_reports(min_score=60.0)
print(f"\nTotal rapports générés : {len(alerts)}")