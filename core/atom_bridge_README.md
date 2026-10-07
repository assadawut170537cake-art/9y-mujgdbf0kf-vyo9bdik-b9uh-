# atom_bridge.py — Mark LV ↔ Atom Bridge

Module เชื่อมต่อ Mark LV (PC) กับ Atom (Android) ทำหน้าที่เป็น API server สำหรับ Atom เรียกใช้ และ sync ข้อมูลผ่าน Google Drive

## Features
- FastAPI REST API สำหรับ Atom client
- WebSocket สำหรับ real-time updates
- Memory sync ผ่าน Google Drive
- Client functions สำหรับ Mark LV เรียก Atom

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | ตรวจสอบสถานะ |
| GET | /status | ดูสถานะ connections |
| POST | /command | รับ command จาก Atom |
| GET | /result/:id | ดูผลลัพธ์ของ command |
| WS | /ws | real-time updates |
| POST | /sync/memory | sync memory |

## Usage
```python
from core.atom_bridge import create_api_server, start_api_server
from core.atom_bridge import sync_memory_to_cloud, sync_memory_from_cloud
from core.atom_bridge import send_command_to_atom, fetch_atom_status

# เริ่ม API server
start_api_server()

# Sync memory
sync_memory_to_cloud({"key": "value"})
downloaded = sync_memory_from_cloud()

# เรียก Atom
result = await send_command_to_atom({"action": "test"})
status = await fetch_atom_status()
```
