# Unsloth Decision Model ใน Mark-LV — รายงานวิจัยและคู่มือใช้งาน

> ที่มา: [unsloth.ai/docs — Train your own Decision Model](https://unsloth.ai/docs/basics/train-your-own-decision-model-with-unsloth) และ [github.com/unslothai/unsloth](https://github.com/unslothai/unsloth)

## 1. Decision Model คืออะไร

LLM ที่ fine-tune ด้วย LoRA แล้วใส่ **classification head (Clef)** ต่อท้าย จึงไม่ได้ "พิมพ์คำตอบ" แต่**ให้คะแนนตัวเลือก (calibrated probability) แล้วคืนค่า (label, probability)**

- **ผลที่วัดได้จาก benchmark ของ Unsloth:** typed-decisions accuracy 36%→73% (0.8B), 33%→78% (2B) — จากเดิมที่ LLM ตอบแบบสุ่ม (chance level)
- **โมเดลที่เหมาะกับเรา:** `unsloth/Qwen3.5-0.8B` (VRAM ~4GB, เทรน ~42 นาที) หรือ `unsloth/Qwen3.5-2B` (~8GB, ~81%)
- **Dataset ฝึก:** `LocalLLaMA/typed-decisions` (12 sources) หรือ **JSONL ของแอปเราเอง** (ดูข้อ 4)

## 2. สถาปัตยกรรมที่ต่อยอดเข้า Mark-LV

```
src/services/decision_model.py        ← บริการ infer (4 rungs)
src/helpers/train_decision_model.py   ← สคริปต์เทรน (WSL2 + CUDA)
src/helpers/decision_data_export.py   ← แปลง log คำสั่ง→action เป็น training rows
tests/test_decision_model.py          ← 29 unit tests (ไม่ต้องใช้ GPU)
```

ลำดับการตัดสินใจ (`decide()`):

| Rung | ที่มา | เงื่อนไข |
|---|---|---|
| 1. `local` | โมเดลบนเครื่องนี้ (4-bit) | `DECISION_MODEL_PATH` + `unsloth` installed |
| 2. `studio` | `unsloth studio` HTTP | `UNSLOTH_DECISION_URL` |
| 3. `gemini` | `core.gemini` FAST ladder (ของเดิม) | มี API key |
| 4. `heuristic` | keyword overlap — ไม่มี model ไม่มี network | เสมอ |

ทุก rung คืน shape เดียวกัน:

```json
{
  "answers": {"team": {"answer": "billing", "probabilities": {"billing": 0.91, "technical": 0.05, "sales": 0.04}}},
  "source": "local",
  "confidence": 0.91,
  "needs_fallback": false
}
```

`needs_fallback=true` เมื่อ `confidence < DECISION_MIN_CONFIDENCE` (default 0.55) — ให้ caller โยนกลับ Gemini Live ตามเดิม

## 3. ติดตั้ง + เทรน (WSL2)

```powershell
wsl
cd /mnt/j/Mark-LV
pip install unsloth
```

Smoke test (~1 นาที):

```bash
python src/helpers/train_decision_model.py --max-steps 60 --output-dir /tmp/dec-smoke
```

เทรนจริงบน typed-decisions:

```bash
python src/helpers/train_decision_model.py \
    --model unsloth/Qwen3.5-0.8B --epochs 2 --lr 2e-4 --lora-rank 16 \
    --output-dir models/marklv-decision-router
```

ได้ `models/marklv-decision-router/merged` → ตั้งใน `.env` (master) ที่ Windows เข้าถึงผ่าน `\\wsl$\...` หรือก๊อปออกมานอก WSL

## 4. เก็บข้อมูล train จากการใช้งานจริง (collect→train loop)

```python
from src.helpers.decision_data_export import record_decision
record_decision("logs/routing.jsonl", "เปิด chrome", "open_app", confidence=0.9)
```

แล้วแปลงเป็น training rows:

```bash
python -m src.helpers.decision_data_export \
    --input logs/routing.jsonl --output data/router_rows.jsonl
python src/helpers/train_decision_model.py --dataset data/router_rows.jsonl --epochs 3
```

rows schema (`typed-decisions`): `id, workflow, split, state{"task":…}, questions{action:choice…}, action__label, action__probabilities`

## 5. Config (master `.env`)

```ini
DECISION_MODEL_PATH=J:\Mark-LV\models\marklv-decision-router\merged
UNSLOTH_DECISION_URL=http://localhost:8888   # ถ้ารัน unsloth studio ใน WSL2
DECISION_MIN_CONFIDENCE=0.55
```

## 6. หมายเหตุ/ข้อจำกัด

- `requirements.txt` **ไม่**เพิ่ม `unsloth`/`torch` (หนักหลาย GB) — ติดตั้งเองใน WSL2
- บน Windows native ให้ใช้ rung studio หรือ heuristic; local rung ต้องผ่าน WSL2
- `core/gemini.py` แก้บั๊กเดิม 1 บรรทัด: เพิ่ม `import os` ที่หายไปใน `api_key()` (ทำให้ทุก call ที่ไม่ได้ส่ง key เฉพาะ crash ด้วย NameError)
- ยังไม่ได้ wire เข้า `main.py` — เรียก `route_action()` จาก plugin หรือเพิ่ม in `main.py` ภายหลังเมื่อมี decision log สะสมพอ (~200+ แถว)
