import os
import datetime
from pathlib import Path

MEMORY_DIR = Path("j:/Mark-LV/memory")

def memory_write_action(parameters: dict, player=None, session_memory=None) -> str:
    title = parameters.get("title")
    content = parameters.get("content")
    
    if not title or not content:
        return "Sir, I need both a title and content to save a memory."
    
    title = title.replace("/", "_").replace("\\", "_").replace(" ", "_")
    if not title.endswith(".md"):
        title += ".md"
        
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    file_path = MEMORY_DIR / title
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    msg = f"Memory saved as {title}."
    print(f"[Memory Write] {msg}")
    return msg

TOOL = {
    "name": "memory_write",
    "description": "Writes or updates a long-term memory markdown note.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING", "description": "The title or filename of the memory note"},
            "content": {"type": "STRING", "description": "The full markdown content to save"}
        },
        "required": ["title", "content"]
    },
    "handler": memory_write_action,
}
