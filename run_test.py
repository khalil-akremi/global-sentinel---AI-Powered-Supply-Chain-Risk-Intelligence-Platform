from models.scoring_pipeline import score_all_suppliers, get_risk_dashboard

suppliers = ['Samsung', 'TSMC', 'Tesla', 'Foxconn', 'BASF']

score_all_suppliers(suppliers)

dashboard = get_risk_dashboard()

print('── Dashboard ──')
print('Total     :', dashboard['total_suppliers'])
print('High Risk :', dashboard['high_risk_count'])
print('Medium    :', dashboard['medium_risk_count'])
print('Low Risk  :', dashboard['low_risk_count'])