import os
from pathlib import Path

MEMORY_DIR = Path("j:/Mark-LV/memory")

def memory_search_action(parameters: dict, player=None, session_memory=None) -> str:
    query = parameters.get("query", "").lower()
    
    if not MEMORY_DIR.exists():
        return "No memory database exists yet, sir."
        
    results = []
    for md_file in MEMORY_DIR.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if query in content.lower() or query in md_file.name.lower():
                idx = content.lower().find(query)
                snippet = content[max(0, idx-50):min(len(content), idx+50)].replace('\n', ' ')
                results.append(f"- {md_file.name}: ...{snippet}...")
        except Exception:
            pass
            
    if not results:
        return f"Sir, I couldn't find any memories matching '{query}'."
        
    return "Found these memories:\n" + "\n".join(results)

TOOL = {
    "name": "memory_search",
    "description": "Searches long-term memory markdown files for a keyword.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "Keyword or phrase to search"}
        },
        "required": ["query"]
    },
    "handler": memory_search_action,
}
