import asyncio
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from openai import OpenAI
from modules.llm.analyst_agent import AnalystAgent
from config import settings

async def main():
    class MockRetriever:
        def get_context(self, *args, **kwargs):
            return "No context"
    
    # Force use of OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )
    
    # We pass client and model name
    agent = AnalystAgent(client=client, retriever=MockRetriever(), model_name="anthropic/claude-3-5-haiku:beta")
    query = "สรุปกำไรขาดทุนของอพาร์ทเม้นท์ทุกสาขาในปี 2025"
    filename = "apt_properties.csv, apt_expenses.csv, apt_rent_ledger.csv"
    
    print(f"Testing analyze_stream with query: {query}")
    try:
        async for event in agent.analyze_stream(query, filename=filename):
            print(event)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
