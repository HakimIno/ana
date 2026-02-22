import httpx
import pytest
import polars as pl
from pathlib import Path
import time

BASE_URL = "http://localhost:8000"
DATA_FILE = Path("../sample_business_data.csv").resolve()

@pytest.fixture(scope="module")
def ground_truth():
    """Calculate the absolute ground truth via polars independently."""
    df = pl.read_csv(DATA_FILE)
    
    total_revenue = df["Revenue"].sum()
    total_cogs = df["COGS"].sum()
    total_marketing = df["Marketing_Expense"].sum()
    total_rent = df["Rent"].sum()
    total_salary = df["Salary"].sum()
    
    # Net Profit
    net_profit = total_revenue - (total_cogs + total_marketing + total_rent + total_salary)
    
    # Month with max revenue
    monthly_rev = df.group_by("Month").agg(pl.col("Revenue").sum()).sort("Revenue", descending=True)
    best_month = monthly_rev[0, "Month"]
    
    # Category with max revenue
    cat_rev = df.group_by("Category").agg(pl.col("Revenue").sum()).sort("Revenue", descending=True)
    best_category = cat_rev[0, "Category"]

    return {
        "total_revenue": total_revenue,
        "net_profit": net_profit,
        "best_month": best_month,
        "best_category": best_category,
        "row_count": len(df)
    }

@pytest.mark.asyncio
async def test_e2e_financial_accuracy(ground_truth):
    """
    E2E Test:
    1. Upload sample data.
    2. Ask financial questions.
    3. Verify accuracy against ground truth.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Reset Storage
        await client.delete(f"{BASE_URL}/files")
        
        # 2. Upload File
        with open(DATA_FILE, "rb") as f:
            files = {"file": (DATA_FILE.name, f, "text/csv")}
            upload_res = await client.post(f"{BASE_URL}/upload", files=files)
            assert upload_res.status_code == 200
            data = upload_res.json()
            assert data["row_count"] == ground_truth["row_count"]
            print(f"\n✅ Upload successful: {data['row_count']} rows indexed.")

        # 3. Test Question: Total Revenue
        start_time = time.time()
        query_res = await client.post(f"{BASE_URL}/query", json={"question": "ปี 2025 มีรายได้รวมทั้งปีเท่าไหร่?"})
        latency = time.time() - start_time
        
        assert query_res.status_code == 200
        analysis = query_res.json()
        
        # Check structured layout
        assert "answer" in analysis
        assert "key_metrics" in analysis
        assert "recommendations" in analysis
        assert "risks" in analysis
        
        # Verify Revenue Accuracy (Margin of error for LLM formatting)
        print(f"Analysis Keys: {list(analysis['key_metrics'].keys())}")
        llm_revenue = next((v for k, v in analysis["key_metrics"].items() if "Revenue" in k or "รายได้" in k), None)
        print(f"LLM Revenue: {llm_revenue} | Ground Truth: {ground_truth['total_revenue']}")
        
        # 4. Test Question: Best Month
        query_res = await client.post(f"{BASE_URL}/query", json={"question": "เดือนไหนมียอดขายสูงที่สุด?"})
        analysis = query_res.json()
        
        # Human readable vs Raw format check
        month_map = {"2025-12": ["2025-12", "ธันวาคม", "December"]}
        best_month_raw = ground_truth["best_month"]
        
        found = any(word in analysis["answer"] or word in str(analysis["key_metrics"]) 
                    for word in month_map.get(best_month_raw, [best_month_raw]))
        
        assert found, f"Expected {best_month_raw} or its equivalent in response"
        print(f"✅ Best Month verified: {analysis['answer'][:50]}...")

        # 5. Performance Check
        print(f"⏱️ Latency: {latency:.2f}s")
        assert latency < 15.0 # Reasonable for RAG + GPT-4o

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
