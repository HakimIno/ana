import os
import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path so we can import config & modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings
from modules.storage.metadata_manager import MetadataManager

def generate():
    print("🏙️ Generating Apartment Business Mockup Data (2024-2026)...")
    
    datasets_dir = settings.DATASETS_DIR
    datasets_dir.mkdir(parents=True, exist_ok=True)
    
    cities = ["Bangkok", "Pattaya", "Phuket"]
    apt_names = [
        "Sukhumvit Sky Residency", "Lumpini Park View", "Thonglor Elite Suites",
        "Ari Garden Living", "Silom Central Stay", "Pattaya Beachfront Heights",
        "Walking Street Suites", "Jomtien Ocean Breeze", "Phuket Old Town Lofts",
        "Patong Paradise Apartments"
    ]
    city_map = {
        apt_names[0]: "Bangkok", apt_names[1]: "Bangkok", apt_names[2]: "Bangkok",
        apt_names[3]: "Bangkok", apt_names[4]: "Bangkok", apt_names[5]: "Pattaya",
        apt_names[6]: "Pattaya", apt_names[7]: "Pattaya", apt_names[8]: "Phuket",
        apt_names[9]: "Phuket"
    }
    
    # 1. Generate Properties
    properties = []
    for i, name in enumerate(apt_names):
        city = city_map[name]
        units = random.randint(30, 100)
        properties.append({
            "property_id": f"PRP-{i+1:03d}",
            "property_name": name,
            "city": city,
            "total_units": units,
            "amenities_score": round(random.uniform(3.5, 5.0), 1),
            "manager_name": random.choice(["Somchai", "Somsak", "Wichai", "Anucha", "Kanda"]),
            "established_year": random.randint(2010, 2022)
        })
        
    # 2. Generate Tenants (simplified)
    tenants = []
    tenant_names = ["Somboon", "Suda", "Naree", "Prasit", "Malee", "Surachai", "Ploy", "Aek", "Aom", "Golf", "Noi", "Nan"]
    last_names = ["Rakthai", "Deejai", "Saengthong", "Wongsuwan", "Kaewmanee", "Suksabuy"]
    
    tenant_counter = 1
    for prop in properties:
        num_tenants = int(prop["total_units"] * random.uniform(0.7, 0.95)) # 70-95% occupancy
        for u in range(1, num_tenants + 1):
            t_name = f"{random.choice(tenant_names)} {random.choice(last_names)}"
            status = random.choice(["Active", "Active", "Active", "Terminated"])
            base_rent = 8000 + (prop["amenities_score"] * 2000) + (random.randint(0, 5) * 500)
            
            tenants.append({
                "tenant_id": f"TEN-{tenant_counter:04d}",
                "property_id": prop["property_id"],
                "unit_no": f"U-{u:03d}",
                "tenant_name": t_name,
                "base_rent": base_rent,
                "lease_start": "2023-12-01",
                "lease_end": "2026-12-31" if status == "Active" else "2024-12-31",
                "status": status
            })
            tenant_counter += 1

    # 3. Generate Rent Ledger (Monthly 2024-2026)
    ledger = []
    months = []
    start_date = datetime(2024, 1, 1)
    for m in range(36): # 3 years
        months.append(start_date + timedelta(days=m*31))
        
    for month in months:
        for t in tenants:
            # Skip if lease terminated before this month
            lease_end = datetime.strptime(t["lease_end"], "%Y-%m-%d")
            if month > lease_end: continue
            
            water = 100 + random.randint(50, 200)
            elec = 500 + random.randint(200, 2500)
            parking = 0 if random.random() > 0.3 else 500
            
            ledger.append({
                "transaction_id": f"TRX-{len(ledger)+1:06d}",
                "date": month.strftime("%Y-%m-%d"),
                "property_id": t["property_id"],
                "tenant_id": t["tenant_id"],
                "rent_amount": t["base_rent"],
                "water_bill": water,
                "electricity_bill": elec,
                "parking_fee": parking,
                "total_paid": t["base_rent"] + water + elec + parking,
                "payment_status": "Paid" if random.random() > 0.05 else "Overdue"
            })

    # 4. Generate Expenses
    expenses = []
    expense_cats = ["Maintenance", "Staff Salaries", "Marketing", "Security", "Taxes"]
    for month in months:
        for prop in properties:
            for cat in expense_cats:
                amount = 5000 + (prop["total_units"] * random.randint(100, 300))
                if cat == "Marketing": amount = amount * 0.2
                if cat == "Taxes": amount = amount * 0.5 if month.month != 1 else amount * 3.0
                
                expenses.append({
                    "expense_id": f"EXP-{len(expenses)+1:05d}",
                    "date": month.strftime("%Y-%m-%d"),
                    "property_id": prop["property_id"],
                    "category": cat,
                    "amount": round(amount, 2),
                    "description": f"Monthly {cat} for {prop['property_name']}"
                })

    # Write files
    files = [
        ("apt_properties.csv", properties, ["property_id", "property_name", "city", "total_units", "amenities_score", "manager_name", "established_year"]),
        ("apt_tenants.csv", tenants, ["tenant_id", "property_id", "unit_no", "tenant_name", "base_rent", "lease_start", "lease_end", "status"]),
        ("apt_rent_ledger.csv", ledger, ["transaction_id", "date", "property_id", "tenant_id", "rent_amount", "water_bill", "electricity_bill", "parking_fee", "total_paid", "payment_status"]),
        ("apt_expenses.csv", expenses, ["expense_id", "date", "property_id", "category", "amount", "description"])
    ]
    
    mm = MetadataManager()
    
    for filename, data, fieldnames in files:
        path = datasets_dir / filename
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"✅ Created {filename} ({len(data)} rows)")
        
        # Meta dictionary mapping (Thai terms)
        thai_map = {
            "property_id": "รหัสอพาร์ทเม้นท์", "property_name": "ชื่ออพาร์ทเม้นท์", "city": "จังหวัด",
            "total_units": "จำนวนห้องทั้งหมด", "amenities_score": "คะแนนสิ่งอำนวยความสะดวก",
            "manager_name": "ชื่อผู้จัดการ", "established_year": "ปีที่ก่อตั้ง",
            "tenant_id": "รหัสผู้เช่า", "unit_no": "เลขห้อง", "tenant_name": "ชื่อผู้เช่า",
            "base_rent": "ค่าเช่าพื้นฐาน", "lease_start": "วันที่เริ่มสัญญา",
            "lease_end": "วันที่สิ้นสุดสัญญา", "status": "สถานะการเช่า",
            "transaction_id": "รหัสธุรกรรม", "date": "วันที่", "rent_amount": "ยอดค่าเช่า",
            "water_bill": "ค่าน้ำ", "electricity_bill": "ค่าไฟ", "parking_fee": "ค่าที่จอดรถ",
            "total_paid": "ยอดชำระรวม", "payment_status": "สถานะการชำระเงิน",
            "expense_id": "รหัสค่าใช้จ่าย", "category": "หมวดหมู่ค่าใช้จ่าย",
            "amount": "จำนวนเงิน", "description": "รายละเอียด"
        }
        
        # Save metadata metadata
        mm.save_dictionary(filename, {k: thai_map.get(k, k) for k in fieldnames})
        mm.save_group(filename, "Apartment Business")

    print("\n✨ All mockup data and metadata generated successfully!")

if __name__ == "__main__":
    generate()
