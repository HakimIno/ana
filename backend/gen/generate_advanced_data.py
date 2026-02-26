import csv
import random
from datetime import datetime, timedelta

def generate_advanced_mock_data(filename="advanced_financial_data_5000.csv", num_rows=5000):
    categories = ["Beverages", "Electronics", "Office Supplies", "Marketing", "Travel", "Software", "Consulting", "Hardware", "Human Resources", "Logistics"]
    subcategories = {
        "Beverages": ["Soft Drinks", "Mineral Water", "Coffee Beans", "Specialty Tea"],
        "Electronics": ["Monitors", "Laptops", "Keyboards", "Cables", "Power Adapters"],
        "Office Supplies": ["Paper", "Pens", "Ink Cartridges", "Notebooks", "Binders"],
        "Marketing": ["Digital Ads", "Print Media", "Social Media", "Event Sponsorship"],
        "Travel": ["Flights", "Hotel Bookings", "Car Rentals", "Meal Expenses"],
        "Software": ["SaaS Subscriptions", "Cloud Infrastructure", "Security Licenses", "Development Tools"],
        "Consulting": ["Legal Advice", "Financial Audit", "Business Strategy", "IT Support"],
        "Hardware": ["Servers", "Networking Gear", "Printers", "Storage Devices"],
        "Human Resources": ["Training Programs", "Recruitment Ads", "Employee Benefits", "Health Insurance"],
        "Logistics": ["Shipping Fees", "Warehouse Rent", "Packaging Materials", "Customs Duties"]
    }
    regions = ["East", "West", "North", "South", "Central", "Overseas"]
    status_options = ["Approved", "Pending", "Rejected", "Paid"]
    suppliers = [f"Supplier-{i}" for i in range(1, 51)]
    departments = ["Sales", "Engineering", "Finance", "Operations", "R&D", "Marketing", "Customer Support"]
    customer_types = ["B2B - Corporate", "B2B - SME", "B2C - Retail", "B2G - Government"]

    headers = [
        "TransactionID", "Date", "Month", "Year", "Category", 
        "SubCategory", "Region", "Department", "CustomerType", 
        "UnitPrice", "Quantity", "Revenue", "CostPerUnit", 
        "TotalCost", "Profit", "Status", "Notes"
    ]

    # Generate dates for the last 3 years
    start_date = datetime(2022, 1, 1)
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        
        for i in range(1, num_rows + 1):
            category = random.choice(categories)
            subcategory = random.choice(subcategories[category])
            
            # Realistic pricing based on category
            if category == "Software":
                unit_price = round(random.uniform(50.0, 500.0), 2)
                margin = random.uniform(0.7, 0.9)
            elif category == "Hardware":
                unit_price = round(random.uniform(200.0, 5000.0), 2)
                margin = random.uniform(0.1, 0.3)
            else:
                unit_price = round(random.uniform(10.0, 1000.0), 2)
                margin = random.uniform(0.2, 0.6)
            
            quantity = random.randint(1, 100)
            revenue = round(unit_price * quantity, 2)
            cost_per_unit = round(unit_price * (1 - margin), 2)
            total_cost = round(cost_per_unit * quantity, 2)
            profit = round(revenue - total_cost, 2)
            
            # Date distribution
            days_offset = random.randint(0, 365 * 3)
            current_date = start_date + timedelta(days=days_offset)
            
            # Complex notes
            notes = [
                f"Project {subcategory} in {random.choice(regions)} via {random.choice(suppliers)}",
                f"Wholesale {category} replenishment from {random.choice(suppliers)}. Efficiency is key.",
                f"Discounted {subcategory} promotional event. Quarter-end push.",
                f"Standard {category} maintenance fee for {random.choice(suppliers)}. Contract ID: {random.randint(1000, 9999)}",
                f"Bulk order for {random.choice(departments)}. Urgency: {random.choice(['Low', 'Medium', 'High'])}"
            ]
            
            row = [
                f"ADV-TXN-{10000 + i}",
                current_date.strftime("%Y-%m-%d"),
                current_date.strftime("%Y-%m"),
                current_date.year,
                category,
                subcategory,
                random.choice(regions),
                random.choice(departments),
                random.choice(customer_types),
                unit_price,
                quantity,
                revenue,
                cost_per_unit,
                total_cost,
                profit,
                random.choice(status_options),
                random.choice(notes)
            ]
            writer.writerow(row)
            
    print(f"✅ Generated {num_rows} rows of advanced financial data in '{filename}'")

if __name__ == "__main__":
    generate_advanced_mock_data()
