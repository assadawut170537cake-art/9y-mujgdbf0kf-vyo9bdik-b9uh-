# รายงานการย้าย ATOM เข้า Mark-LV — รวมศูนย์เป็นระบบเดียว

วันที่: 9 ตุลาคม 2569 (2026-10-09) · อนุมัติโดย: ลูกพี่ · ผู้ดำเนินการ: ULTRON

## 1. คำตัดสินใจของลูกพี่ (บันทึกถาวร)

- ยึด **JARVIS เป็นสมองหลัก (ฝั่ง PC)** เดียวกันทั้งระบบ
- **ATOM = แอป Android (ฝั่งมือถือ)** ที่ใช้ **คอร์เดียวกัน** กับ JARVIS — ตัวเดียวกัน 2 ชื่อ 2 สถานที่
- ทุกอย่างรวมอยู่ในโฟลเดอร์เดียวคือ **`J:\Mark-LV`** (ชื่อเรียกขาน: Mark 55)

## 2. หลักฐานว่า "สาย Flutter" คือตัวล่าสุด

| สาย | หลักฐาน | ผล |
|---|---|---|
| `apps\flutter` (Dart) | ไฟล์ `.dart` ล่าสุด **6 ต.ค. 20:46** (home_screen, memory_save_button, pipeline_coordinator) | 🟢 ย้ายเข้า Mark-LV |
| `ATOM_MOBILE` (Kotlin KMP) | `.kt/.kts` ล่าสุด 5 ต.ค. 08:02 · ขนาด 103 MB เป็น `build/` + `.transforms` ขยะทั้ง job | 🟡 ไม่ย้าย (หยุดนานกว่า) |

## 3. โครงสร้างหลังย้าย (โครงจริง ไม่ใช่คำพูด)

```
Mark-LV/
├── apps/
│   ├── flutter/          ← แอป ATOM (432 ไฟล์ซอร์ส · คัด .dart_tool/build/.idea/*.log ออก)
│   └── releases/         ← ATOM-v1.0.apk (50MB) + FRIDAY-v1.0.apk (26MB)
├── core/
│   ├── atom_bridge.py    ← [แก้] hardcode Path("J:/อะตอม") 2 จุด → SYNC_DIR
│   ├── atom_core_main.py ← เดิม J:\อะตอม\main.py (cloud-core entry)
│   └── atom_database.py  ← เดิม J:\อะตอม\database.py
├── sync/
│   ├── gdrive_vault.py   ← ย้ายจาก J:\อะตอม
│   └── atom_bridge_README.md  (มีอยู่เดิมก่อนย้าย)
├── docs/
│   ├── ATOM_BLUEPRINT.md     ← Master Blueprint v7.0 (Tri-Core + Security Laws 13 ข้อ)
│   ├── ATOM_CORE_CONTEXT.md
│   ├── ATOM_MEMORY_RUNBOOK.md
│   ├── MIGRATION_README.md
│   ├── README_RUNBOOK.md
│   └── agents/  atom.md · friday.md · ultron.md   ← Persona แยกไฟล์ตามกฎข้อ 8
├── tools/                ← classify_project · extract_clip_frames · finish_migration · organize_project · verify_project
├── deployment/atom/      ← atom-core.service · setup_ingress.sh · ollama-hybrid-config.ps1 · requirements.txt · pc_worker.py · ultron_daemon.py
└── config/atom_bridge.json  ← สร้างใหม่
```

## 4. สิ่งที่ตรวจแล้ว (มีหลักฐาน ไม่เดา)

- `python -m py_compile` ผ่านทั้ง 6 ไฟล์ (exit=0)
- grep dart ทั้ง `apps\flutter\lib` หา `J:\` / `J:/` → **0 ผลลัพธ์** (ไม่มี hardcode path ค้าง)
- `config.dart` → base URL = `https://assadawut-jarvis.online` (override ได้ในแอปผ่าน prefs `atom_base_url`) — ถ้าอยากคุยบริดจ์ในเครือข่ายเดียว ตั้งเป็น `http://<IP-PC>:8765`
- `atom_bridge.py` เสิร์ฟ API `:8765` มี `/health` `/status` `/command` `/result/{id}` `/ws` `/sync/memory` — มือถือเรียกสมอง PC ทางนี้
- ความลับ: `secrets.json` กันไม่ให้ขึ้น git ทั้งใน `apps/flutter/.gitignore` และ `.git/info/exclude` (local-only)
- ต้นทาง **ไม่ถูกลบ/ย้ายแม้แต่ไฟล์เดียว** — copy ล้วน ๆ ย้อนกลับได้ตลอด

## 5. ที่ยังไม่ทำ (รอคำสั่งลูกพี่ ถือว่าเป็นงานถัดไป ไม่กล้าเพิ่งแตะ)

1. แท็กโฟลเดอร์ต้นทางเป็น `_ARCHIVED` (J:\อะตอม · J:\โปรเจคอะตอม · J:\ATOM_MOBILE · J:\ATOM_SYSTEM · J:\ATOM_PC_WORKER)
2. เปิด `gdrive_enabled` — ตอนนี้ `false` ตั้งใจ (ต้องมี credential ก่อน และลูกพี่ต้องสั่ง)
3. commit รายการนี้เป็น git checkpoint ของ Mark-LV
4. Supermemory adapter สำหรับ Mark-LV ยังไม่มี — tools 5 ไฟล์ที่ย้ายมาเป็นเครื่องมือจัดระเบียบโปรเจค **ไม่ใช่** sync adapter อย่าสับสน
