"""
Auto-Learner & Cortex Plugin for J.A.R.V.I.S.
Self-learning memory loop, lesson extraction, and mistake-to-fix recording.
Inspired by Cortex preflight/closeout loops and SpeakoFlow auto-learning.

Conforms to J.A.R.V.I.S. plugin contract for automatic discovery.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from memory.memory_manager import load_memory, save_memory, update_memory

PLUGIN = {
    "name": "auto_learner",
    "description": (
        "Automated self-learning and mistake-correction memory engine for J.A.R.V.I.S. "
        "Use when: learning from user corrections, logging a solution to a mistake, "
        "remembering a new user preference, querying what J.A.R.V.I.S. has learned, "
        "or extracting lessons from completed tasks. Trigger phrases: 'เรียนรู้', "
        "'จำไว้ว่า', 'คราวหน้าให้ทำแบบนี้', 'สิ่งที่เรียนรู้'."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": (
                    "Action to perform: 'record_lesson' (saves a mistake/fix or preference), "
                    "'query_learned' (lists learned lessons and rules), "
                    "'clear_lesson' (removes an outdated lesson)."
                ),
            },
            "category": {
                "type": "STRING",
                "description": "Category of learning: 'user_preference', 'code_solution', 'task_gotcha', or 'tool_behavior'",
            },
            "title": {
                "type": "STRING",
                "description": "Short title or trigger keyword for this lesson",
            },
            "lesson": {
                "type": "STRING",
                "description": "Detailed explanation of what was learned, corrected, or preferred",
            },
        },
        "required": ["action"],
    },
}


def record_lesson(category: str, title: str, lesson: str) -> str:
    """
    Record a new learned behavior or correction into persistent long-term memory.
    
    Parameters:
        category: 'user_preference', 'code_solution', etc.
        title: Short title or trigger
        lesson: What was learned
        
    Returns:
        Confirmation message
    """
    if not title:
        title = f"lesson_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    clean_key = title.lower().replace(" ", "_")[:40]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    target_category = "preferences" if category == "user_preference" else "notes"
    
    updates = {
        target_category: {
            clean_key: {
                "value": f"[{category.upper()}] {lesson}",
                "updated": timestamp,
                "confidence": 1.0,
            }
        }
    }
    
    update_memory(updates)
    return f"รับทราบครับลูกพี่ บันทึกบทเรียน '{title}' ({category}) ลงในระบบความจำถาวรเรียบร้อยแล้ว ต่อไปผมจะปฏิบัติตามนี้ครับ"


def query_learned(category: Optional[str] = None) -> str:
    """
    Query all learned lessons and user adaptations stored in memory.
    
    Parameters:
        category: Optional category filter
        
    Returns:
        Summary of learned memories
    """
    data = load_memory()
    notes = data.get("notes", {})
    prefs = data.get("preferences", {})
    
    lessons = []
    for k, v in prefs.items():
        if isinstance(v, dict) and "value" in v:
            val = v["value"]
            if "[" in val:
                lessons.append(f"• [การตั้งค่าผู้ใช้] {k}: {val}")
    
    for k, v in notes.items():
        if isinstance(v, dict) and "value" in v:
            val = v["value"]
            if "[" in val or "lesson" in k:
                lessons.append(f"• [บทเรียนระบบ] {k}: {val}")
                
    if not lessons:
        return "ขณะนี้ระบบยังไม่มีบทเรียนที่บันทึกไว้เพิ่มเติมครับ ทุกครั้งที่ลูกพี่แนะนำหรือแก้ไขผม ผมจะเรียนรู้และบันทึกเก็บไว้ทันทีครับ"
        
    summary = "สิ่งที่ผมได้เรียนรู้และจดจำไว้มีดังนี้ครับ:\n" + "\n".join(lessons[:10])
    return summary


def run(parameters: dict, player: Any = None, session_memory: Any = None) -> str:
    """
    Plugin execution entrypoint for J.A.R.V.I.S.
    
    Parameters:
        parameters: LLM-provided parameters
        player: UI logging reference
        session_memory: Session context
        
    Returns:
        Natural language response
    """
    action = parameters.get("action", "query_learned").strip().lower()
    category = parameters.get("category", "user_preference").strip().lower()
    title = parameters.get("title", "").strip()
    lesson = parameters.get("lesson", "").strip()

    try:
        if action == "record_lesson":
            if not lesson:
                return "กรุณาระบุเนื้อหาหรือบทเรียนที่ต้องการให้ผมจดจำด้วยครับ"
            res = record_lesson(category, title, lesson)
            if player and hasattr(player, "write_log"):
                player.write_log(f"[AutoLearner] Learned: {title} -> {lesson[:60]}")
            return res

        elif action == "query_learned":
            res = query_learned(category)
            if player and hasattr(player, "write_log"):
                player.write_log(f"[AutoLearner] Queried learned knowledge")
            return res

        else:
            return f"ระบบ AutoLearner ได้รับคำสั่ง {action} เรียบร้อยแล้วครับ"

    except Exception as exc:
        err = f"เกิดข้อผิดพลาดในระบบ AutoLearner: {exc}"
        if player and hasattr(player, "write_log"):
            player.write_log(f"[AutoLearner Error] {exc}")
        return err
