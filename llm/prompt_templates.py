from __future__ import annotations


SYSTEM_PROMPT = """You are a supply chain risk analyst. Your role is to generate 
clear, actionable risk alert reports for procurement and operations teams.

CRITICAL: Respond ONLY with raw JSON. No markdown, no backticks, no ```json wrapper.
Start your response directly with { and end with }.

Always respond in the following exact JSON format:
{
  "executive_summary": "2-3 sentence summary of the risk situation",
  "risk_drivers": ["driver 1", "driver 2", "driver 3"],
  "recommendations": ["action 1", "action 2", "action 3"],
  "monitoring_points": ["point 1", "point 2"]
}

Be specific, factual, and actionable. Never invent data not provided to you."""


def build_risk_report_prompt(
    supplier_name: str,
    risk_score: float,
    risk_level: str,
    features: dict,
    recent_articles: list[dict],
) -> str:
    """
    Construit le prompt utilisateur avec toutes les données du fournisseur.
    """

    # Formate les articles récents
    articles_text = ""
    if recent_articles:
        articles_text = "\n".join([
            f"- [{a.get('published_at', 'N/A')}] {a.get('title', '')} "
            f"(relevance: {a.get('relevance_score', 0)})"
            for a in recent_articles[:5]  # max 5 articles
        ])
    else:
        articles_text = "No recent articles found."

    prompt = f"""Generate a risk alert report for the following supplier:

SUPPLIER: {supplier_name}
RISK SCORE: {risk_score}/100
RISK LEVEL: {risk_level}

QUANTITATIVE SIGNALS:
- Negative articles (last 7 days): {features.get('neg_article_cnt_7d', 0):.0f}
- Negative articles (last 30 days): {features.get('neg_article_cnt_30d', 0):.0f}
- Average relevance score (7d): {features.get('avg_relevance_score_7d', 0):.2f}
- Article velocity (this week vs last week): {features.get('article_velocity_7d', 1):.2f}x
- Commodity price change (7d): {features.get('commodity_price_change_7d', 0)*100:.1f}%
- Commodity volatility (7d): {features.get('commodity_volatility_7d', 0)*100:.1f}%

RECENT NEWS ARTICLES:
{articles_text}

Generate a concise, actionable risk report in the specified JSON format."""

    return prompt