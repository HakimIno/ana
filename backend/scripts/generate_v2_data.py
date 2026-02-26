import polars as pl
from datetime import datetime, timedelta
import random

# Configuration
BRANCHES = [
    "Siam", "Silom", "Thonglor", "Ari", "Bang Na", 
    "Ladprao", "Pinklao", "Rama 2", "Rama 3", "Rama 9",
    "Rangsit", "Kanlapaphruek", "Victory Monument", "On Nut", "Bang Khae",
    "Nonthaburi", "Min Buri", "Samut Prakan", "Pathum Thani", "Ratchada"
]
CATEGORIES = ["Standard Buffet", "Premium Buffet", "A La Carte"]
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 12, 31)

def generate_sales():
    data = []
    current_date = START_DATE
    while current_date <= END_DATE:
        for branch in BRANCHES:
            for cat in CATEGORIES:
                base_customers = random.randint(30, 150)
                if branch in ["Siam", "Victory Monument", "Rama 9"]:
                    base_customers += 50
                
                customers = base_customers
                if current_date.weekday() >= 5:
                    customers = int(customers * 1.5)
                
                price_per_head = {"Standard Buffet": 219, "Premium Buffet": 439, "A La Carte": 150}[cat]
                revenue = customers * (price_per_head + random.randint(-20, 50))
                cogs_pct = random.uniform(0.4, 0.6)
                cogs = revenue * cogs_pct
                profit = revenue - cogs
                
                data.append({
                    "Date": current_date.strftime("%Y-%m-%d"),
                    "Branch": branch,
                    "Category": cat,
                    "Customers": customers,
                    "Revenue": round(float(revenue), 2),
                    "COGS": round(float(cogs), 2),
                    "Profit": round(float(profit), 2)
                })
        current_date += timedelta(days=1)
    
    df = pl.DataFrame(data)
    df.write_csv("uploads/teenoi_sales_v2.csv")
    print(f"Generated {len(df)} sales records.")

def generate_staff():
    data = []
    staff_id = 1001
    for branch in BRANCHES:
        num_staff = random.randint(15, 30)
        for _ in range(num_staff):
            salary = random.randint(15000, 25000)
            ot = random.randint(0, 40)
            score = round(random.uniform(3.0, 5.0), 1)
            data.append({
                "Staff_ID": f"ST{staff_id}",
                "Branch": branch,
                "Monthly_Salary": salary,
                "Overtime_Hours": ot,
                "Performance_Score": score,
                "Training_Completed": str(random.choice([True, False]))
            })
            staff_id += 1
    
    df = pl.DataFrame(data)
    df.write_csv("uploads/teenoi_staff_v2.csv")
    print(f"Generated {len(df)} staff records.")

def generate_feedback():
    data = []
    current_date = START_DATE
    while current_date <= END_DATE:
        if random.random() < 0.2:
            for branch in BRANCHES:
                for cat in CATEGORIES:
                    rating = random.randint(1, 5)
                    data.append({
                        "Date": current_date.strftime("%Y-%m-%d"),
                        "Branch": branch,
                        "Category": cat,
                        "Rating": rating,
                        "Taste_Score": round(random.uniform(1, 5), 1),
                        "Service_Score": round(random.uniform(1, 5), 1),
                        "Value_Score": round(random.uniform(1, 5), 1),
                        "Recommend": random.choice(["Yes", "No"])
                    })
        current_date += timedelta(days=1)
    
    df = pl.DataFrame(data)
    df.write_csv("uploads/teenoi_feedback_v2.csv")
    print(f"Generated {len(df)} feedback records.")

if __name__ == "__main__":
    generate_sales()
    generate_staff()
    generate_feedback()
