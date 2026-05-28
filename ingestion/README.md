# Global Sentinel 🛡️

> AI-Powered Supply Chain Risk Intelligence Platform

Real-time monitoring of supplier risk using news signals, commodity prices,
and economic indicators — with automated ML scoring and LLM-generated alerts.

## The Problem

Companies discover supplier failures too late. By the time a bankruptcy,
geopolitical disruption, or production delay becomes visible, the damage
is done. Global Sentinel detects early warning signals before they escalate.

## Architecture
## Tech Stack

| Layer | Tools |
|---|---|
| Data Ingestion | Python, NewsAPI, Yahoo Finance |
| Orchestration | Apache Airflow |
| Feature Store | Feast + PostgreSQL |
| ML Model | XGBoost + scikit-learn |
| LLM Reporting | OpenRouter (Mistral) + Langfuse |
| Dashboard | Grafana |
| Infrastructure | Docker, Kubernetes, Digital Ocean |
| CI/CD | GitHub Actions |

## Project Status

| Phase | Status | Description |
|---|---|---|
| Phase 1 — Data Pipeline | 🟡 In Progress | News collection + validation |
| Phase 2 — Feature Store | ⬜ Planned | Feature engineering + Feast |
| Phase 3 — ML Model | ⬜ Planned | Risk scoring model |
| Phase 4 — LLM Layer | ⬜ Planned | Alert report generation |
| Phase 5 — Dashboard | ⬜ Planned | Grafana real-time viz |
| Phase 6 — Infrastructure | ⬜ Planned | K8s + CI/CD |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/TON_USERNAME/global-sentinel.git
cd global-sentinel

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Start PostgreSQL
docker-compose -f infrastructure/docker-compose.dev.yml up -d

# 5. Test news collection
cd ingestion && python test_manual.py
```

