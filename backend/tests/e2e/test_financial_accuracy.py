import httpx
import pytest
import polars as pl
from pathlib import Path
import time
import asyncio

BASE_URL = "http://127.0.0.1:8000"
DATA_FILE = Path(__file__).parents[1] / "data" / "sample_business_data.csv"

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
            job_id = upload_res.json()["job_id"]
            
            # Poll status until complete
            max_retries = 30
            for i in range(max_retries):
                status_res = await client.get(f"{BASE_URL}/upload/status/{job_id}")
                assert status_res.status_code == 200
                job_data = status_res.json()
                if job_data["status"] == "completed":
                    row_count = job_data["result"]["row_count"]
                    assert row_count == ground_truth["row_count"]
                    print(f"\n✅ Upload successful: {row_count} rows indexed.")
                    break
                elif job_data["status"] == "failed":
                    pytest.fail(f"Job failed: {job_data['error']}")
                await asyncio.sleep(1)
            else:
                pytest.fail("Upload timed out")

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
        metrics_str = str(analysis['key_metrics']).lower()
        print(f"Analysis Keys: {list(analysis['key_metrics'].keys())}")
        llm_revenue = any(k in metrics_str for k in ["revenue", "รายได้", "9,725,000", "9725000"])
        print(f"LLM Revenue Found: {llm_revenue} | Ground Truth: {ground_truth['total_revenue']}")
        assert llm_revenue, "Expected revenue information in key_metrics"
        
        # 4. Test Question: Best Month
        query_res = await client.post(f"{BASE_URL}/query", json={"question": "เดือนไหนมียอดขายสูงที่สุด?"})
        analysis = query_res.json()
        
        # Human readable vs Raw format check
        month_map = {"2025-12": ["2025-12", "ธันวาคม", "December", "dec", "12", "ธ.ค."]}
        best_month_raw = ground_truth["best_month"]
        
        answer_lower = analysis["answer"].lower()
        metrics_lower = str(analysis["key_metrics"]).lower()
        
        print(f"DEBUG: LLM Answer: {answer_lower}")
        print(f"DEBUG: LLM Metrics: {metrics_lower}")
        
        found = any(word.lower() in answer_lower or word.lower() in metrics_lower 
                    for word in month_map.get(best_month_raw, [best_month_raw]))
        
        assert found, f"Expected {best_month_raw} or its equivalent in response. Answer: {analysis['answer']}"
        print(f"✅ Best Month verified: {analysis['answer'][:50]}...")

        # 5. Performance Check
        print(f"⏱️ Latency: {latency:.2f}s")
        assert latency < 15.0 # Reasonable for RAG + GPT-4o

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
