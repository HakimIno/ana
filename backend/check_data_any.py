import csv
from collections import defaultdict
from datetime import datetime

properties = {}
with open('/Users/weerachit/Documents/ai-analyst/backend/uploads/datasets/apt_properties.csv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        properties[row['property_id']] = row['property_name']

expenses = defaultdict(float)
with open('/Users/weerachit/Documents/ai-analyst/backend/uploads/datasets/apt_expenses.csv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dt = datetime.strptime(row['date'], '%Y-%m-%d')
        
            expenses[row['property_id']] += float(row['amount'])

revenue = defaultdict(float)
with open('/Users/weerachit/Documents/ai-analyst/backend/uploads/datasets/apt_rent_ledger.csv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dt = datetime.strptime(row['date'], '%Y-%m-%d')
        if dt.year == 2025 :
            revenue[row['property_id']] += float(row['total_paid'])

results = []
for pid, pname in properties.items():
    rev = revenue.get(pid, 0.0)
    exp = expenses.get(pid, 0.0)
    prof = rev - exp
    results.append({
        'name': pname,
        'rev': rev,
        'exp': exp,
        'prof': prof
    })

results.sort(key=lambda x: x['prof'], reverse=True)

total_rev = 0
total_exp = 0
total_prof = 0
for r in results:
    print(f"{r['name']} | Rev: {r['rev']:.2f} | Exp: {r['exp']:.2f} | Profit: {r['prof']:.2f}")
    total_rev += r['rev']
    total_exp += r['exp']
    total_prof += r['prof']

print("--- Totals ---")
print(f"Total Rev: {total_rev:.2f}")
print(f"Total Exp: {total_exp:.2f}")
print(f"Total Profit: {total_prof:.2f}")
