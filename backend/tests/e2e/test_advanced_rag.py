import httpx
import pytest
import uuid

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_session_memory_persistence():
    """
    Test that the AI remembers previous questions in the same session.
    """
    session_id = f"test-session-{uuid.uuid4()}"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. First question: Establish context
        q1 = "สวัสดีครับ ผมชื่อ สมชาย เป็นเจ้าของธุรกิจขายเครื่องดื่ม"
        res1 = await client.post(f"{BASE_URL}/query", json={
            "question": q1,
            "session_id": session_id
        })
        assert res1.status_code == 200
        print(f"\nQ1: {q1}")
        print(f"A1: {res1.json()['answer'][:50]}...")

        # 2. Second question: Follow up (requires memory)
        q2 = "คุณจำได้ไหมว่าผมชื่ออะไรและทำธุรกิจอะไร?"
        res2 = await client.post(f"{BASE_URL}/query", json={
            "question": q2,
            "session_id": session_id
        })
        assert res2.status_code == 200
        answer = res2.json()['answer']
        print(f"Q2: {q2}")
        print(f"A2: {answer}")
        
        # Verify memory
        assert "สมชาย" in answer
        assert "เครื่องดื่ม" in answer or "ธุรกิจ" in answer
        print("✅ Session Memory verified!")

@pytest.mark.asyncio
async def test_hybrid_search_accuracy():
    """
    Test that Hybrid search works by asking about specific text that 
    might be better found via keyword (sparse) vs semantic (dense).
    """
    # Assuming 'Equipment' or specific categories are in the sample data
    async with httpx.AsyncClient(timeout=60.0) as client:
        query = "ขอดูข้อมูลเฉพาะหมวดหมู่ 'Beverages' หน่อยครับ"
        res = await client.post(f"{BASE_URL}/query", json={
            "question": query
        })
        assert res.status_code == 200
        analysis = res.json()
        
        # Check if the AI correctly focused on Beverages
        metrics_str = str(analysis.get("key_metrics", "")).lower()
        answer_str = str(analysis.get("answer", "")).lower()
        assert "beverages" in metrics_str or "เครื่องดื่ม" in answer_str or "beverages" in answer_str
        print("✅ Hybrid Search (Keyword focus) verified for 'Beverages'")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
