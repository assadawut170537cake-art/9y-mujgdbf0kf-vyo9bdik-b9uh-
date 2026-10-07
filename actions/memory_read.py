from pathlib import Path

MEMORY_DIR = Path("j:/Mark-LV/memory")

def memory_read_action(parameters: dict, player=None, session_memory=None) -> str:
    title = parameters.get("title")
    if not title:
        return "Sir, please provide the title of the memory note to read."
        
    title = title.replace("/", "_").replace("\\", "_").replace(" ", "_")
    if not title.endswith(".md"):
        title += ".md"
        
    file_path = MEMORY_DIR / title
    if not file_path.exists():
        return f"Sir, I could not find a memory note named {title}."
        
    try:
        content = file_path.read_text(encoding="utf-8")
        return f"Content of {title}:\n{content}"
    except Exception as e:
        return f"Error reading memory note: {e}"

TOOL = {
    "name": "memory_read",
    "description": "Reads the full content of a long-term memory markdown note.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING", "description": "The title or filename of the memory note"}
        },
        "required": ["title"]
    },
    "handler": memory_read_action,
}
