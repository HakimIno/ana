import polars as pl
import numpy as np
from datetime import datetime, timedelta
import os

def generate_shabu_chain_data():
    np.random.seed(42)
    os.makedirs("uploads", exist_ok=True)
    
    branches = ['Ari', 'Siam', 'Thonglor', 'Silom', 'Bang Na']
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2026, 12, 31)
    delta = end_date - start_date
    days = delta.days + 1
    
    # --- 1. Sales Data ---
    sales_records = []
    for d in range(days):
        current_date = start_date + timedelta(days=d)
        year = current_date.year
        month = current_date.month
        is_weekend = current_date.weekday() >= 5
        
        for branch in branches:
            # Skip branches not yet opened
            if branch == 'Silom' and year < 2024: continue
            if branch == 'Bang Na' and year < 2025: continue
            
            # Base daily customers
            base_customers = 80 if branch in ['Siam', 'Thonglor'] else 50
            if is_weekend: base_customers *= 1.8
            
            # Seasonality (Dec/Jan peak)
            if month in [12, 1]: base_customers *= 1.3
            
            customers = int(base_customers + np.random.normal(0, 10))
            customers = max(10, customers)
            
            # Revenue calculation (Avg 450 - 600 THB per head)
            avg_ticket = np.random.uniform(450, 650)
            revenue = customers * avg_ticket
            
            # COGS (Food cost ~35-45%)
            # EVENT: Pork price spike in 2024
            food_cost_pct = np.random.uniform(0.35, 0.42)
            if year == 2024: food_cost_pct += 0.05 
            
            cogs = revenue * food_cost_pct
            
            sales_records.append({
                'Date': current_date.strftime('%Y-%m-%d'),
                'Branch': branch,
                'Customers': customers,
                'Revenue': round(revenue, 2),
                'COGS': round(cogs, 2),
                'Profit': round(revenue - cogs, 2),
                'Category': np.random.choice(['Standard Buffet', 'Premium Buffet', 'A La Carte'], p=[0.6, 0.3, 0.1])
            })
            
    pl.DataFrame(sales_records).write_csv("uploads/shabu_sales_2023_2026.csv")
    print("Generated: uploads/shabu_sales_2023_2026.csv")

    # --- 2. Inventory & Supplies ---
    items = ['Pork Belly', 'Sliced Beef', 'River Prawn', 'Vegetable Set', 'Dipping Sauce']
    suppliers = ['FreshCo', 'Betagro', 'Local Market', 'CP Food']
    
    inventory_records = []
    for branch in branches:
        for item in items:
            unit_price = np.random.uniform(100, 400)
            waste_pct = np.random.uniform(0.02, 0.08)
            # Thonglor has higher waste due to premium standards
            if branch == 'Thonglor': waste_pct += 0.03
            
            inventory_records.append({
                'Branch': branch,
                'Item': item,
                'Supplier': np.random.choice(suppliers),
                'Unit_Price': round(unit_price, 2),
                'Waste_KG': round(np.random.uniform(5, 20), 2),
                'Waste_Rate': round(waste_pct, 4),
                'Last_Restock': (end_date - timedelta(days=np.random.randint(0, 7))).strftime('%Y-%m-%d')
            })
            
    pl.DataFrame(inventory_records).write_csv("uploads/shabu_inventory_supplies.csv")
    print("Generated: uploads/shabu_inventory_supplies.csv")

    # --- 3. Staff Performance ---
    roles = ['Manager', 'Chef', 'Server', 'Cleaner']
    staff_records = []
    staff_count = 0
    for branch in branches:
        # 8-15 staff per branch
        n_staff = np.random.randint(8, 16)
        for _ in range(n_staff):
            staff_count += 1
            role = np.random.choice(roles, p=[0.1, 0.2, 0.5, 0.2])
            salary = {'Manager': 45000, 'Chef': 35000, 'Server': 18000, 'Cleaner': 15000}[role]
            salary += np.random.normal(0, 2000)
            
            perf_score = np.random.uniform(60, 95)
            # Siam branch staff are more stressed/lower score due to high volume
            if branch == 'Siam': perf_score -= 5
            
            staff_records.append({
                'Staff_ID': f'STF-{staff_count:03d}',
                'Branch': branch,
                'Role': role,
                'Monthly_Salary': round(salary, 2),
                'Performance_Score': round(perf_score, 1),
                'Leaves_Taken': np.random.randint(0, 5),
                'Overtime_Hours': np.random.randint(0, 40)
            })
            
    pl.DataFrame(staff_records).write_csv("uploads/shabu_staff_performance.csv")
    print("Generated: uploads/shabu_staff_performance.csv")

    # --- 4. Customer Feedback ---
    feedback_records = []
    for branch in branches:
        # ~200 feedback entries per branch
        for _ in range(200):
            rating = np.random.randint(1, 6)
            # Siam has more complaints about waiting time
            if branch == 'Siam' and np.random.rand() < 0.3:
                rating = min(rating, 3)
                
            feedback_records.append({
                'Branch': branch,
                'Rating': rating,
                'Taste_Score': np.random.randint(3, 6),
                'Service_Score': np.random.randint(2, 6),
                'Value_Score': np.random.randint(3, 6),
                'Recommend': 'Yes' if rating >= 4 else 'No'
            })
            
    pl.DataFrame(feedback_records).write_csv("uploads/shabu_customer_feedback.csv")
    print("Generated: uploads/shabu_customer_feedback.csv")

if __name__ == "__main__":
    generate_shabu_chain_data()
