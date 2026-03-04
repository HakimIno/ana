import csv
from datetime import datetime
from collections import defaultdict

rev_rent = 0
rev_total = 0

with open('/Users/weerachit/Documents/ai-analyst/backend/uploads/datasets/apt_rent_ledger.csv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dt = datetime.strptime(row['date'], '%Y-%m-%d')
        if dt.year == 2025:
            rev_rent += float(row['rent_amount'])
            rev_total += float(row['total_paid'])

print(f"Total Rent Amount: {rev_rent}")
print(f"Total Paid: {rev_total}")
