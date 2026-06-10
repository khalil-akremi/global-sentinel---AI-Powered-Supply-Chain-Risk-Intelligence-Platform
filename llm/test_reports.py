from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env.local"), override=True)

from llm.report_generator import (
    generate_risk_report,
    generate_alerts_reports,
    call_llm,
    parse_llm_response,
    langfuse,
    LANGFUSE_ENABLED,
)
from llm.prompt_templates import SYSTEM_PROMPT, build_risk_report_prompt

# ── Test raw response ──
user_prompt = build_risk_report_prompt(
    supplier_name="Foxconn",
    risk_score=65.3,
    risk_level="HIGH",
    features={
        "neg_article_cnt_7d": 2,
        "neg_article_cnt_30d": 5,
        "avg_relevance_score_7d": 1.5,
        "article_velocity_7d": 1.8,
        "commodity_price_change_7d": 0.22,
        "commodity_volatility_7d": 0.12,
    },
    recent_articles=[],
)

raw = call_llm(SYSTEM_PROMPT, user_prompt)
print("RAW RESPONSE:")
print(repr(raw))

# ── Test rapport Foxconn ──
print("\n── Test rapport Foxconn ──\n")
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

# ── Rapports d'alerte ──
print("\n── Rapports d'alerte (score >= 60) ──\n")
alerts = generate_alerts_reports(min_score=60.0)
print(f"\nTotal rapports générés : {len(alerts)}")

# ── Flush Langfuse ──
if LANGFUSE_ENABLED:
    langfuse.flush()
    print("✓ Traces Langfuse envoyées")