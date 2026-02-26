import polars as pl
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Configuration
BRANCHES = [
    "Siam Square", "Liberty Plaza", "Victory Monument", "The Bright Rama 2", 
    "Esplanade Ratchada", "Major Pinklao", "The Paseo Kanlapaphruek", "MBK Center",
    "Union Mall", "Jas Village Amata", "Robinson Lifestyle Ratchapruek", "The Mall Bangkae",
    "Lotus Bang Na", "Central Westgate", "Future Park Rangsit", "Fashion Island",
    "Seacon Square", "Mega Bang Na", "The Mall Ngamwongwan", "Gateway Ekamai"
]
CATEGORIES = ["Standard Buffet", "Premium Buffet", "A La Carte"]
ORDER_TYPES = ["Dine-in", "Delivery"]
MEMBER_TYPES = ["Member", "Guest"]
ROLES = ["Manager", "Chef", "Kitchen Staff", "Server", "Cleaner"]

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 12, 31)

def generate_teenoi_mega():
    np.random.seed(42)
    os.makedirs("uploads/teenoi_mega", exist_ok=True)
    
    delta = END_DATE - START_DATE
    days = delta.days + 1
    
    # --- 1. Branch Registry (Metadata) ---
    print("Generating Branch Metadata...")
    branch_records = []
    for branch in BRANCHES:
        sq_m = np.random.randint(200, 500)
        rent = sq_m * np.random.randint(800, 1500)
        branch_records.append({
            "Branch": branch,
            "Location_Type": "Mall" if "Mall" in branch or "Center" in branch or "Square" in branch or "Plaza" in branch else "Stand-alone",
            "Square_Meters": sq_m,
            "Monthly_Rent": round(float(rent), 2),
            "Opening_Date": (START_DATE - timedelta(days=np.random.randint(365, 1000))).strftime("%Y-%m-%d")
        })
    pl.DataFrame(branch_records).write_csv("uploads/teenoi_mega/branches.csv")

    # --- 2. Inventory (Metadata) ---
    print("Generating Inventory Data...")
    items = ["Pork Belly", "Sliced Beef", "River Prawn", "Vegetable Set", "Dipping Sauce", "Shabu Soup"]
    suppliers = ["FreshCo", "Betagro", "Local Market", "CP Food"]
    inventory_records = []
    for branch in BRANCHES:
        for item in items:
            unit_price = np.random.uniform(100, 450)
            waste_rate = np.random.uniform(0.02, 0.07)
            if branch in ["Siam Square", "MBK Center"]:
                waste_rate += 0.03 # Busy branches have more waste
            inventory_records.append({
                "Branch": branch,
                "Item": item,
                "Supplier": np.random.choice(suppliers),
                "Cost_Per_Unit": round(float(unit_price), 2),
                "Waste_Rate": round(float(waste_rate), 4),
                "Reorder_Level_KG": np.random.randint(50, 200)
            })
    pl.DataFrame(inventory_records).write_csv("uploads/teenoi_mega/inventory.csv")

    # --- 3. Promotions (Metadata) ---
    print("Generating Promotions Data...")
    promo_names = ["Songkran Festival", "Student Discount", "Midnight Shabu", "Member Double Points", "Grand Opening"]
    promo_records = []
    current_date = START_DATE
    while current_date <= END_DATE:
        if random.random() < 0.05: # 5% chance of starting a promo on any day
            duration = random.randint(3, 15)
            promo = random.choice(promo_names)
            target = random.choice(BRANCHES + ["All"])
            promo_records.append({
                "Promo_Name": promo,
                "Start_Date": current_date.strftime("%Y-%m-%d"),
                "End_Date": (current_date + timedelta(days=duration)).strftime("%Y-%m-%d"),
                "Discount_Pct": random.choice([5, 10, 15, 20]),
                "Target_Branch": target
            })
            current_date += timedelta(days=duration + 5)
        else:
            current_date += timedelta(days=1)
    pl.DataFrame(promo_records).write_csv("uploads/teenoi_mega/promotions.csv")

    # --- 4. Sales Data (Detailed) ---
    print("Generating Sales Data...")
    sales_records = []
    for d in range(days):
        current_date = START_DATE + timedelta(days=d)
        is_weekend = current_date.weekday() >= 5
        month = current_date.month
        year = current_date.year
        
        # Check for active promos
        active_promos = [p for p in promo_records if p["Start_Date"] <= current_date.strftime("%Y-%m-%d") <= p["End_Date"]]
        
        for branch in BRANCHES:
            # Branch Opening Staggering
            if branch in ["Central Westgate", "Fashion Island"] and year < 2025:
                continue
            if branch in ["Mega Bang Na", "Gateway Ekamai"] and year < 2026:
                continue
            
            # Promo Impact
            branch_promo = [p for p in active_promos if p["Target_Branch"] in [branch, "All"]]
            demand_multiplier = 1.3 if branch_promo else 1.0

            for cat in CATEGORIES:
                for o_type in ORDER_TYPES:
                    for m_type in MEMBER_TYPES:
                        base = 20 if branch in ["Siam Square", "MBK Center"] else 12
                        if is_weekend:
                            base *= 2.2
                        base *= demand_multiplier
                        
                        customers = int(base + np.random.normal(0, 5))
                        customers = max(1, customers)
                        
                        price = {"Standard Buffet": 219, "Premium Buffet": 439, "A La Carte": 180}[cat]
                        if m_type == "Member":
                            price *= 0.95
                        if branch_promo:
                            price *= (1 - (branch_promo[0]["Discount_Pct"]/100))
                        
                        revenue = customers * price
                        cogs_base = 0.45 if cat != "A La Carte" else 0.35
                        if o_type == "Delivery":
                            cogs_base += 0.15
                        if year == 2025 and month in [5, 6]:
                            cogs_base += 0.08
                        
                        cogs = revenue * (cogs_base + np.random.uniform(-0.02, 0.04))
                        sales_records.append({
                            "Date": current_date.strftime("%Y-%m-%d"),
                            "Branch": branch,
                            "Category": cat,
                            "Order_Type": o_type,
                            "Member_Status": m_type,
                            "Customers": customers,
                            "Revenue": round(float(revenue), 2),
                            "COGS": round(float(cogs), 2),
                            "Profit": round(float(revenue - cogs), 2)
                        })
    pl.DataFrame(sales_records).write_csv("uploads/teenoi_mega/sales.csv")
    print(f"Generated {len(sales_records)} sales records.")

    # --- 5. Staff Data (Detailed) ---
    print("Generating Staff Data...")
    staff_records = []
    staff_id = 2000
    for branch in BRANCHES:
        n_staff = np.random.randint(20, 35)
        for _ in range(n_staff):
            staff_id += 1
            role = np.random.choice(ROLES, p=[0.05, 0.15, 0.3, 0.4, 0.1])
            salary = {"Manager": 55000, "Chef": 38000, "Kitchen Staff": 22000, "Server": 18000, "Cleaner": 15000}[role]
            salary += np.random.normal(0, 2500)
            ot_base = 35 if branch in ["Siam Square", "MBK Center"] else 15
            ot = max(0, int(ot_base + np.random.normal(0, 10)))
            perf_score = np.random.uniform(70, 98)
            if ot > 40:
                perf_score -= 8
            staff_records.append({
                "Staff_ID": f"TN-{staff_id}", "Branch": branch, "Role": role,
                "Monthly_Salary": round(float(salary), 2), "Overtime_Hours": ot,
                "Performance_Score": round(float(perf_score), 1), "Leave_Days": np.random.randint(0, 6)
            })
    pl.DataFrame(staff_records).write_csv("uploads/teenoi_mega/staff.csv")
    print(f"Generated {len(staff_records)} staff records.")

    # --- 6. Customer Feedback (Detailed) ---
    print("Generating Feedback Data...")
    feedback_records = []
    sampled_indices = random.sample(range(len(sales_records)), min(40000, int(len(sales_records) * 0.15)))
    for idx in sampled_indices:
        s = sales_records[idx]
        rating = np.random.randint(1, 6)
        branch_staff = [st for st in staff_records if st["Branch"] == s["Branch"]]
        avg_ot = sum(st["Overtime_Hours"] for st in branch_staff) / len(branch_staff)
        service_score = np.random.randint(3, 6)
        if avg_ot > 30:
            service_score = max(1, service_score - 1)
        feedback_records.append({
            "Date": s["Date"], "Branch": s["Branch"], "Category": s["Category"], "Rating": rating,
            "Taste_Score": np.random.randint(3, 6), "Service_Score": service_score,
            "Wait_Time_Score": np.random.randint(1, 4) if s["Branch"] in ["Siam Square", "MBK Center"] else np.random.randint(3, 6),
            "Recommend": "Yes" if rating >= 4 else "No"
        })
    pl.DataFrame(feedback_records).write_csv("uploads/teenoi_mega/feedback.csv")
    print(f"Generated {len(feedback_records)} feedback records.")

if __name__ == "__main__":
    generate_teenoi_mega()
