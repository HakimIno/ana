import asyncio
import sys

from modules.llm.analyst_agent import AnalystAgent
from config import settings

async def main():
    class MockRetriever:
        def get_context(self, *args, **kwargs):
            return "No context"
    
    agent = AnalystAgent(retriever=MockRetriever())
    query = "สรุปกำไรขาดทุนของอพาร์ทเม้นท์ทุกสาขาในปี 2025"
    filename = "apt_properties.csv, apt_expenses.csv, apt_rent_ledger.csv"
    
    # Manually reproduce the context gathering steps
    rag_context = "No context"
    metrics_context = agent._prepare_metrics_context(None, filename=filename, dfs=None, include_samples=True)
    
    from modules.storage.file_manager import FileManager
    from modules.data.orchestrator import DataOrchestrator
    
    file_manager = FileManager()
    orchestrator = DataOrchestrator(session_id="test")
    
    files_to_ingest = []
    for f in filename.split(","):
        try:
            resolved = file_manager.get_file_path(f.strip())
            files_to_ingest.append(str(resolved))
        except:
            pass
            
    orchestrator.ingest_files(files_to_ingest)
    db_schema = orchestrator.get_schema_summary()
    
    prompt = agent._build_prompt(query, "test", filename, metrics_context, rag_context, None)
    prompt += f"\n\nDATABASE_SCHEMA:\n{db_schema}\n"
    
    print("\n========= METRICS CONTEXT =========")
    print(metrics_context)
    
    print("\n========= SYSTEM PROMPT =========")
    from modules.llm.prompts import ANALYST_SYSTEM_PROMPT
    print(ANALYST_SYSTEM_PROMPT[:500] + "...")
    
    print("\n========= USER PROMPT =========")
    print(prompt)

if __name__ == "__main__":
    asyncio.run(main())
