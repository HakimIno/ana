import polars as pl
from modules.llm.code_interpreter import CodeInterpreter

def main():
    dfs = {
        'apt_properties': pl.read_csv('/Users/weerachit/Documents/ai-analyst/backend/uploads/datasets/apt_properties.csv'),
        'apt_expenses': pl.read_csv('/Users/weerachit/Documents/ai-analyst/backend/uploads/datasets/apt_expenses.csv'),
        'apt_rent_ledger': pl.read_csv('/Users/weerachit/Documents/ai-analyst/backend/uploads/datasets/apt_rent_ledger.csv')
    }
    
    code = """
import polars as pl
from datetime import datetime

# Filter data for year 2025
rent_2025 = dfs['apt_rent_ledger'].filter(
    (pl.col('date') >= "2025-01-01") & 
    (pl.col('date') <= "2025-12-31") & 
    (pl.col('payment_status') == 'Paid')
)

expenses_2025 = dfs['apt_expenses'].filter(
    (pl.col('date') >= "2025-01-01") & 
    (pl.col('date') <= "2025-12-31")
)

# calculate revenue
revenue_per_property = rent_2025.groupby('property_id').agg(
    pl.col('total_paid').sum().alias('total_revenue')
)

expenses_per_property = expenses_2025.groupby('property_id').agg(
    pl.col('amount').sum().alias('total_expenses')
)

# join
summary = dfs['apt_properties'].join(
    revenue_per_property, on='property_id', how='left'
).join(
    expenses_per_property, on='property_id', how='left'
).fill_null(0)

summary = summary.with_columns(
    (pl.col('total_revenue') - pl.col('total_expenses')).alias('profit')
)

for row in summary.to_dicts():
    print(row['property_name'], row['total_revenue'], row['total_expenses'], row['profit'])
"""

    interpreter = CodeInterpreter()
    res = interpreter.execute(code, dfs=dfs)
    print("SUCCESS:", res['success'])
    print("OUTPUT:", res['output'])
    print("ERROR:", res['error'])

if __name__ == "__main__":
    main()
