import polars as pl
import numpy as np
from datetime import datetime, timedelta

def generate_hr_data(n_employees=1000):
    np.random.seed(42)
    
    departments = ['R&D', 'Sales', 'Marketing', 'Engineering', 'HR', 'Finance', 'Customer Support']
    roles = ['Junior', 'Senior', 'Lead', 'Manager', 'Director']
    locations = ['Bangkok', 'Singapore', 'Tokyo', 'London', 'New York']
    performance_ratings = [1, 2, 3, 4, 5] # 5 is best
    
    data = []
    start_date = datetime(2022, 1, 1)
    
    for i in range(n_employees):
        dept = np.random.choice(departments)
        role = np.random.choice(roles)
        loc = np.random.choice(locations)
        
        # Salary logic based on role and dept
        base_salary = {
            'Junior': 30000,
            'Senior': 70000,
            'Lead': 100000,
            'Manager': 150000,
            'Director': 250000
        }[role]
        
        # Add some variance and dept multiplier
        multiplier = 1.2 if dept in ['Engineering', 'R&D'] else 1.0
        salary = base_salary * multiplier + np.random.normal(0, 5000)
        
        # Tenure and Performance
        hire_date = start_date + timedelta(days=np.random.randint(0, 1000))
        performance = np.random.choice(performance_ratings, p=[0.05, 0.15, 0.5, 0.2, 0.1])
        
        # Churn probability (higher for low performance)
        churn_prob = 0.4 if performance <= 2 else 0.05
        is_active = np.random.choice(['Active', 'Resigned'], p=[1-churn_prob, churn_prob])
        
        data.append({
            'Employee_ID': f'EMP-{i+1000}',
            'Name': f'Employee_{i}',
            'Department': dept,
            'Role': role,
            'Location': loc,
            'Salary_Monthly': round(salary, 2),
            'Hire_Date': hire_date.strftime('%Y-%m-%d'),
            'Performance_Rating': performance,
            'Status': is_active,
            'Training_Hours': np.random.randint(0, 100),
            'Engagement_Score': round(np.random.uniform(1, 10), 1)
        })
    
    df = pl.DataFrame(data)
    output_path = "uploads/hr_analytics_data.csv"
    df.write_csv(output_path)
    print(f"Generated HR Data at: {output_path}")

if __name__ == "__main__":
    generate_hr_data()
