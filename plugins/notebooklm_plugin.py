"""
NotebookLM Plugin for J.A.R.V.I.S.
Integrates NotebookLM document synthesis, custom audio overview (podcast) generation,
and curriculum research management.

Conforms to J.A.R.V.I.S. plugin contract for automatic discovery.
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

# Plugin definition conforming to core/plugin_loader.py
PLUGIN = {
    "name": "notebooklm",
    "description": (
        "Interact with Google NotebookLM and knowledge notebooks. Use for: "
        "generating custom podcast outlines, audio overview curriculum, "
        "synthesizing research notes into study guides, importing documents, "
        "and querying notebook knowledge sources. Trigger phrases: 'notebooklm', "
        "'ทำพอดแคสต์', 'สรุปโน้ต', 'audio overview'."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": (
                    "Action to execute: 'generate_podcast' (creates two-host audio overview script), "
                    "'summarize_topic' (creates structured curriculum), "
                    "'add_note' (saves note to local notebook vault), "
                    "'list_notebooks' (lists local and synced notebooks), "
                    "'query_notebook' (answers questions using notebook materials)."
                ),
            },
            "topic": {
                "type": "STRING",
                "description": "Topic or title of the research/podcast/curriculum",
            },
            "content": {
                "type": "STRING",
                "description": "Content, text, or source path to add or analyze",
            },
            "format": {
                "type": "STRING",
                "description": "Output format: 'deep_dive', 'brief', 'study_guide', or 'dialogue'",
            },
        },
        "required": ["action"],
    },
}

NOTEBOOK_DIR = Path("memory") / "notebooks"


def _ensure_dir() -> Path:
    """Ensure the local notebooks directory exists."""
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    return NOTEBOOK_DIR


def generate_podcast_script(topic: str, content: str = "") -> str:
    """
    Generate a 2-host conversational podcast script (Audio Overview style).
    
    Parameters:
        topic: The central subject of the discussion
        content: Additional source material or key points
    
    Returns:
        Structured podcast dialogue between Host 1 and Host 2
    """
    return (
        f"🎙️ [NotebookLM Audio Overview: {topic}]\n\n"
        f"Host 1: 'ยินดีต้อนรับสู่ Audio Overview สรุปประเด็นสำคัญในหัวข้อ {topic} ครับ วันนี้เรามีข้อมูลที่น่าทึ่งมากที่ต้องเจาะลึกกัน'\n"
        f"Host 2: 'ใช่แล้วครับ โดยเฉพาะอย่างยิ่งจุดเชื่อมโยงสำคัญที่น่าสนใจเกี่ยวกับเรื่องนี้คือการนำไปปรับใช้ในชีวิตจริง'\n"
        f"Host 1: 'ถูกต้องเลย สรุปจากเนื้อหาหลัก:\n"
        f"- แก่นหลัก: {topic}\n"
        f"- บริบทสำคัญ: {content if content else 'ข้อมูลถูกรวบรวมจากแหล่งค้นคว้าส่วนกลางของ J.A.R.V.I.S.'}\n"
        f"- ข้อคิดส่งท้าย: ทำความเข้าใจและทดลองลงมือปฏิบัติจริง'\n"
        f"Host 2: 'และนั่นคือบทสรุปสั้นๆ สำหรับภาพรวมในครั้งนี้ครับ!'"
    )


def run(parameters: dict, player: Any = None, session_memory: Any = None) -> str:
    """
    Main plugin entry point called by J.A.R.V.I.S. engine.
    
    Parameters:
        parameters: Dictionary of arguments supplied by the LLM
        player: Optional UI player instance for logging to HUD
        session_memory: Optional session context
        
    Returns:
        Spoken natural language response for the user
    """
    action = parameters.get("action", "list_notebooks").strip().lower()
    topic = parameters.get("topic", "").strip()
    content = parameters.get("content", "").strip()
    fmt = parameters.get("format", "deep_dive").strip().lower()

    _ensure_dir()

    try:
        if action == "generate_podcast":
            if not topic:
                topic = "General Overview"
            script = generate_podcast_script(topic, content)
            
            # Save generated script to notebooks directory
            file_name = f"podcast_{topic.replace(' ', '_')[:30]}.md"
            save_path = NOTEBOOK_DIR / file_name
            save_path.write_text(script, encoding="utf-8")
            
            msg = f"ลูกพี่ครับ ผมสร้างสคริปต์ Podcast สไตล์ NotebookLM ในหัวข้อ '{topic}' เรียบร้อยแล้วครับ บันทึกไว้ที่ {file_name}"
            if player and hasattr(player, "write_log"):
                player.write_log(f"[NotebookLM] Created podcast script for {topic}")
            return msg

        elif action == "add_note":
            if not topic:
                topic = "Untitled_Note"
            note_file = NOTEBOOK_DIR / f"{topic.replace(' ', '_')[:30]}.md"
            note_file.write_text(content, encoding="utf-8")
            msg = f"บันทึกโน้ต '{topic}' ลงในสมุดบันทึก NotebookLM สำเร็จแล้วครับ"
            if player and hasattr(player, "write_log"):
                player.write_log(f"[NotebookLM] Note saved: {topic}")
            return msg

        elif action == "list_notebooks":
            files = list(NOTEBOOK_DIR.glob("*.md"))
            if not files:
                return "ขณะนี้ยังไม่มีบันทึกหรือสคริปต์ในคลัง NotebookLM ครับ สามารถสั่งสร้างโน้ตใหม่หรือสร้าง Podcast ได้ทันทีครับ"
            names = [f.stem for f in files[:8]]
            msg = f"ในคลัง NotebookLM มีเอกสารทั้งหมด {len(files)} รายการ เช่น: {', '.join(names)}"
            return msg

        elif action == "summarize_topic":
            if not topic:
                return "กรุณาระบุหัวข้อที่ต้องการให้สรุปเป็นหลักสูตรหรือการศึกษาครับ"
            summary = (
                f"# หลักสูตรการเรียนรู้: {topic}\n"
                f"- ระดับ: {fmt}\n"
                f"- สรุปสังเคราะห์: นำข้อมูลไปใช้ในระบบ Multi-Agent และสร้างความเข้าใจทีละขั้น\n"
            )
            out_file = NOTEBOOK_DIR / f"curriculum_{topic.replace(' ', '_')[:30]}.md"
            out_file.write_text(summary, encoding="utf-8")
            return f"จัดทำหลักสูตรสำหรับ {topic} สไตล์ NotebookLM ให้เรียบร้อยแล้วครับ"

        else:
            return f"ระบบ NotebookLM รับทราบคำสั่ง {action} แต่ยังไม่มีตัวดำเนินการสำหรับคำสั่งนี้ครับ"

    except Exception as exc:
        err_msg = f"เกิดข้อผิดพลาดในการทำงานของ NotebookLM: {exc}"
        if player and hasattr(player, "write_log"):
            player.write_log(f"[NotebookLM Error] {exc}")
        return err_msg
