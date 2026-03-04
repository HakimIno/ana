import csv
from datetime import datetime
from collections import defaultdict

totals = defaultdict(float)

with open('/Users/weerachit/Documents/ai-analyst/backend/uploads/datasets/apt_rent_ledger.csv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dt = datetime.strptime(row['date'], '%Y-%m-%d')
        totals[f"{dt.year}_rent"] += float(row['rent_amount'])
        totals[f"{dt.year}_paid"] += float(row['total_paid'])

for k, v in dict(totals).items():
    print(f"{k}: {v}")
