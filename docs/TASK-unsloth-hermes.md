# TASK BRIEF — Unsloth Decision Model: ส่วนที่เหลือ (ส่งต่อให้ Hermes)

_Issued 2026-10-10 by **Cline** on behalf of **อัษฎาวุธ เมืองซอง (ลูกพี่)**_
_Recipient: **Hermes (คริกชี่)** — local steward agent_

## 1. ทำเสร็จแล้ว (ห้ามแก้ซ้ำ 除非 มีบั๊ก)

| ไฟล์ | สถานะ |
|---|---|
| `src/services/decision_model.py` | ✅ `decide()`/`route_action()` + fallback ladder 4 rungs — tests ผ่าน 29/29 |
| `src/helpers/train_decision_model.py` | ✅ สคริปต์เทรน (ยังไม่ได้รันบน WSL2 — ต้องการ GPU) |
| `src/helpers/decision_data_export.py` | ✅ แปลง log → typed-decisions JSONL |
| `tests/test_decision_model.py` | ✅ `python tests/test_decision_model.py` = 0 failures |
| `docs/unsloth-decision-model.md` | ✅ คู่มือไทยครบ |
| `core/gemini.py` | ✅ แก้บั๊กเดิม: เพิ่ม `import os` ที่หายไปใน `api_key()` |

วิธีเช็ค: `python tests/test_decision_model.py` → ต้องได้ `0 failure(s)`

## 2. งานที่เหลือ (ทำตามลำดับ)

### 2.1 Smoke-test การเทรนใน WSL2 (~5 นาที)
```powershell
wsl -e bash -lc "cd /mnt/j/Mark-LV && pip install unsloth 2>/dev/null | tail -1 && python src/helpers/train_decision_model.py --max-steps 60 --output-dir /tmp/dec-smoke"
```
- ถ้า `unsloth` ลงไม่ได้/CUDA ไม่เห็น → บันทึกผลลง `docs/unsloth-decision-model.md` แล้วข้ามไป 2.4
- ถ้าผ่าน → เทรนจริง: `--model unsloth/Qwen3.5-0.8B --epochs 2 --output-dir models/marklv-decision-router` (~42 นาที, ทำเป็น background แล้วรายงานลูกพี่)

### 2.2 ตั้งค่า master `.env` (ห้าม commit ค่าใด ๆ)
เพิ่มบล็อกนี้ (ค่า path ปรับตามผล 2.1):
```ini
# ── Unsloth Decision Model ─────────────────────────────
DECISION_MODEL_PATH=J:\Mark-LV\models\marklv-decision-router\merged
# UNSLOTH_DECISION_URL=http://localhost:8888   # ถ้ารัน unsloth studio ใน WSL2
DECISION_MIN_CONFIDENCE=0.55
```

### 2.3 Wire เข้า `main.py` (permission ได้รับแล้วจากลูกพี่)
เพิ่ม import + เรียก `route_action()` เป็น pre-check ก่อน Gemini Live เลือก tool:
- actions list เอาจาก `ActionRegistry` ที่ `discover_actions()` สร้างอยู่แล้ว: `[(r.name, r.description) for r in registry._all_records if r.valid]`
- ถ้า `result["action"]` ไม่ None → execute เลย + `record_decision("logs/routing.jsonl", command, action, confidence)`
- ถ้า None → ปล่อยให้ Gemini Live ตัดสินใจตามเดิม (ห้ามลบของเดิม)
- Wrap ทุกอย่างใน try/except — decision model ห้ามทำให้เซสชันหลักพังเด็ดขาด

### 2.4 รายงาน
สรุปผลทั้งหมด (trainer ทำงานไหม, VRAM, accuracy จาก metrics.json, จำนวน routing rows ที่เก็บได้) ลง `docs/unsloth-decision-model.md` section 7

## 3. ขอบเขตและกติกา (ห้ามละเมิด)
- แก้ได้เฉพาะ: `src/`, `tests/`, `docs/`, `models/` (เพิ่มใหม่), `main.py` (ข้อ 2.3 เท่านั้น), `.env` (เพิ่มบล็อก 2.2 เท่านั้น)
- **ห้ามแตะ**: `src/config/keys/`, `database/migrations/`, `.env` เดิมที่มีอยู่, CI secrets
- `requirements.txt` ห้ามเพิ่ม `unsloth`/`torch` (หนักหลาย GB — opt-in เท่านั้น)
- ทุกฟังก์ชันใหม่ต้องมี docstring (Args/Returns) + try/except log prefix ตาม AGENTS.md
- รัน `python tests/test_decision_model.py` ซ้ำทุกครั้งก่อนรายงานว่าเสร็จ

## 4. อ้างอิง
- Docs: https://unsloth.ai/docs/basics/train-your-own-decision-model-with-unsloth
- Repo: https://github.com/unslothai/unsloth
- Dataset: `LocalLLaMA/typed-decisions` (schema อยู่ใน `src/helpers/decision_data_export.py` docstring)
