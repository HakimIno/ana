import csv
import random
from datetime import datetime, timedelta

def generate_complex_mock_data(filename="complex_financial_data.csv", num_rows=1000):
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

    headers = [
        "TransactionID", "Month", "Revenue", "Quantity", "Category", 
        "SubCategory", "Region", "Department", "Status", "Notes"
    ]

    # Generate months for the last 2 years
    base_date = datetime(2023, 1, 1)
    available_months = [(base_date + timedelta(days=31*i)).strftime("%Y-%m") for i in range(24)]
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        
        for i in range(1, num_rows + 1):
            category = random.choice(categories)
            subcategory = random.choice(subcategories[category])
            revenue = round(random.uniform(100.0, 15000.0), 2)
            quantity = random.randint(1, 500)
            month = random.choice(available_months)
            
            # Creating complex notes for semantic testing
            notes = [
                f"Project {subcategory} in {random.choice(regions)} via {random.choice(suppliers)}",
                f"Wholesale {category} replenishment from {random.choice(suppliers)}",
                f"Discounted {subcategory} promotional event",
                f"Standard {category} maintenance fee for {random.choice(suppliers)}",
                f"Bulk order for {random.choice(departments)}"
            ]
            
            row = [
                f"TXN-{20000 + i}",
                month,
                revenue,
                quantity,
                category,
                subcategory,
                random.choice(regions),
                random.choice(departments),
                random.choice(status_options),
                random.choice(notes)
            ]
            writer.writerow(row)
            
    print(f"✅ Generated {num_rows} rows of complex financial data in '{filename}'")

if __name__ == "__main__":
    generate_complex_mock_data()
