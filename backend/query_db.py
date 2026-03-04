import sqlite3
import json

db = sqlite3.connect("chat_memory.db")
cursor = db.cursor()
cursor.execute("SELECT session_id, role, content, data FROM chat_messages ORDER BY timestamp DESC LIMIT 40")
rows = cursor.fetchall()
for r in rows:
    session_id, role, content, data = r
    if "39,234,600" in content or "39234600" in content or "35" in content or "35774107" in content or "35,774,107" in content or "2025" in content:
        print("====== MESSAGE ======")
        print(f"Role: {role}")
        print(f"Content: {content[:1000]}")
        
        if data:
            try:
                data_json = json.loads(data)
                if data_json.get("python_code") or data_json.get("thought"):
                    t = data_json.get("thought")
                    print(f"Thought: {t}")
                    print("--- Python Code ---")
                    print(data_json.get("python_code"))
            except Exception as e:
                print(e)
        print("=====================\n")
