from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.scoring_pipeline import score_all_suppliers, get_risk_dashboard

suppliers = ["Samsung", "TSMC", "Tesla", "Foxconn", "BASF"]
score_all_suppliers(suppliers)

print()
dashboard = get_risk_dashboard()
print("── Dashboard ──")
print(f"Total     : {dashboard['total_suppliers']}")
print(f"High Risk : {dashboard['high_risk_count']}")
print(f"Medium    : {dashboard['medium_risk_count']}")
print(f"Low Risk  : {dashboard['low_risk_count']}")