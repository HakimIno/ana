import pytest
import os
import json
from unittest.mock import MagicMock, patch
from modules.llm.analyst_agent import AnalystAgent

class TestDataAgentFlow:
    @pytest.fixture
    def mock_llm_client(self):
        client = MagicMock()
        return client

    def test_full_analysis_with_duckdb(self, mock_llm_client, temp_csv_file):
        # Setup agent with mock LLM
        agent = AnalystAgent(client=mock_llm_client)
        
        table_name = os.path.splitext(os.path.basename(temp_csv_file))[0]
        
        # Turn 1 response (Python code)
        r1_content = json.dumps({"python_code": f"df = db.execute('SELECT SUM(Revenue) as total FROM {table_name}').pl()\nprint(f'TOTAL:{{df[\"total\"][0]:.0f}}')"})
        
        # Turn 2 response (Final answer)
        r2_content = json.dumps({"answer": "Final analysis: The total revenue is 455000.", "confidence_score": 0.95})

        # Mock _call_llm and CodeInterpreter.execute
        with patch.object(AnalystAgent, "_call_llm") as mock_call:
            mock_call.side_effect = [r1_content, r2_content]
            
            # CodeInterpreter.execute returns {'output': str, 'error': str, 'success': bool}
            mock_exec_result = {'output': 'TOTAL:455000', 'error': None, 'success': True}
            
            with patch("modules.llm.code_interpreter.CodeInterpreter.execute", return_value=mock_exec_result):
                with patch("os.path.exists", return_value=True):
                    with patch("modules.data.orchestrator.DataOrchestrator.ingest_files"):
                        # Run analysis with serializable data_context
                        response = agent.analyze(
                            "What is the total revenue?",
                            session_id="integration_test_final_robust",
                            filename=os.path.basename(temp_csv_file),
                            data_context=[{"Revenue": 455000}]
                        )
        
        # Check results
        assert "455000" in response.answer
        assert response.confidence_score >= 0.9
        assert mock_call.call_count == 2
