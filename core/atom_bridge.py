"""
Atom Bridge — เชื่อมต่อ Mark LV (PC) กับ Atom (Android)
ทำหน้าที่เป็น API server สำหรับ Atom เรียกใช้ และ sync ข้อมูลผ่าน Google Drive
"""
import asyncio
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── Config ──────────────────────────────────────────────────────────────────
BRIDGE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BRIDGE_DIR / "config" / "atom_bridge.json"
SYNC_DIR = BRIDGE_DIR / "sync"
SYNC_DIR.mkdir(exist_ok=True)

# ── State ───────────────────────────────────────────────────────────────────
_connected_clients: dict[str, dict] = {}
_sync_state: dict = {
    "last_sync": None,
    "pending_uploads": [],
    "pending_downloads": [],
}


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "atom_host": "0.0.0.0",
        "atom_port": 8765,
        "sync_interval": 30,
        "gdrive_enabled": False,
        "gdrive_folder": "MarkLV_Sync",
    }


def _save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ── Memory Sync ─────────────────────────────────────────────────────────────────────
def sync_memory_to_cloud(memory_data: dict) -> bool:
    """อัปเดต memory ไปยัง Google Drive (ถ้าเปิดใช้งาน)"""
    config = _load_config()
    if not config.get("gdrive_enabled"):
        return False

    try:
        # อ่าน gdrive_vault จาก Atom
        atom_dir = Path("J:/อะตอม")
        gdrive_script = atom_dir / "gdrive_vault.py"
        if not gdrive_script.exists():
            return False

        # ใช้ subprocess เรียก gdrive_vault
        import subprocess
        result = subprocess.run(
            ["python", str(gdrive_script), "upload", str(SYNC_DIR / "memory.json")],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[AtomBridge] Sync error: {e}")
        return False


def sync_memory_from_cloud() -> Optional[dict]:
    """ดาวน์โหลด memory จาก Google Drive"""
    config = _load_config()
    if not config.get("gdrive_enabled"):
        return None

    try:
        atom_dir = Path("J:/อะตอม")
        gdrive_script = atom_dir / "gdrive_vault.py"
        if not gdrive_script.exists():
            return None

        import subprocess
        result = subprocess.run(
            ["python", str(gdrive_script), "download", "memory.json", str(SYNC_DIR / "memory.json")],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and (SYNC_DIR / "memory.json").exists():
            with open(SYNC_DIR / "memory.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"[AtomBridge] Download error: {e}")
        return None


# ── API Server (สำหรับ Atom เรียก) ─────────────────────────────────────────
def create_api_server():
    """สร้าง FastAPI server สำหรับ Atom client"""
    try:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.responses import JSONResponse
        import uvicorn
    except ImportError:
        print("[AtomBridge] FastAPI not available — API server disabled")
        return None

    app = FastAPI(title="Mark LV Atom Bridge", version="1.0.0")

    @app.get("/health")
    async def health():
        return {"status": "ok", "timestamp": datetime.now().isoformat()}

    @app.get("/status")
    async def status():
        return {
            "connected_clients": len(_connected_clients),
            "last_sync": _sync_state["last_sync"],
            "pending_uploads": len(_sync_state["pending_uploads"]),
        }

    @app.post("/command")
    async def receive_command(cmd: dict):
        """รับ command จาก Atom"""
        cmd_id = hashlib.md5(f"{time.time()}{json.dumps(cmd)}".encode()).hexdigest()[:8]
        print(f"[AtomBridge] Command from Atom: {cmd.get('action', 'unknown')} (id={cmd_id})")

        # ส่ง command ไปยัง Mark LV main loop
        # (ต้องเชื่อมกับ main.py ผ่าน queue หรือ callback)
        _sync_state["pending_uploads"].append({
            "id": cmd_id,
            "command": cmd,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        })

        return {"id": cmd_id, "status": "received"}

    @app.get("/result/{cmd_id}")
    async def get_result(cmd_id: str):
        """Atom ผลลัพธ์ของ command"""
        for item in _sync_state["pending_uploads"]:
            if item["id"] == cmd_id:
                return item
        return {"error": "not found"}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket สำหรับ real-time updates"""
        await websocket.accept()
        client_id = f"client_{len(_connected_clients)}"
        _connected_clients[client_id] = {
            "websocket": websocket,
            "connected_at": datetime.now().isoformat()
        }
        print(f"[AtomBridge] WebSocket client connected: {client_id}")

        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                print(f"[AtomBridge] WS message: {msg.get('type', 'unknown')}")

                # ส่ง response กลับ
                await websocket.send_json({
                    "type": "ack",
                    "received": msg.get("type"),
                    "timestamp": datetime.now().isoformat()
                })
        except WebSocketDisconnect:
            print(f"[AtomBridge] WebSocket client disconnected: {client_id}")
            _connected_clients.pop(client_id, None)

    @app.post("/sync/memory")
    async def sync_memory(memory: dict):
        """รับ memory จาก Atom เพื่อ sync"""
        _sync_state["last_sync"] = datetime.now().isoformat()
        # บันทึกลงไฟล์
        sync_file = SYNC_DIR / "memory_from_atom.json"
        with open(sync_file, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
        return {"status": "synced", "timestamp": _sync_state["last_sync"]}

    return app


def start_api_server():
    """เริ่ม API server ใน background thread"""
    app = create_api_server()
    if app is None:
        return None

    config = _load_config()
    host = config.get("atom_host", "0.0.0.0")
    port = config.get("atom_port", 8765)

    import threading
    import uvicorn

    def run_server():
        uvicorn.run(app, host=host, port=port, log_level="warning")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print(f"[AtomBridge] API server started on {host}:{port}")
    return server_thread


# ── Client (สำหรับ Mark LV เรียก Atom) ─────────────────────────────────────
async def send_command_to_atom(command: dict, timeout: float = 30.0) -> dict:
    """ส่ง command ไปยัง Atom และรอผลลัพธ์"""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx not available"}

    config = _load_config()
    atom_url = config.get("atom_url", "http://localhost:8766")

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(f"{atom_url}/command", json=command)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


async def fetch_atom_status() -> dict:
    """ดึงสถานะจาก Atom"""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx not available"}

    config = _load_config()
    atom_url = config.get("atom_url", "http://localhost:8766")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{atom_url}/status")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


# ── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Mark LV — Atom Bridge")
    print("  เชื่อมต่อ PC (Mark LV) กับ Android (Atom)")
    print("=" * 60)

    # เริ่ม API server
    server = start_api_server()
    if server:
        print(f"\n✅ API server ทำงานที่ port {_load_config().get('atom_port', 8765)}")
        print("   Atom สามารถเชื่อมต่อผ่าน:")
        print(f"   - HTTP: http://<PC_IP>:{_load_config().get('atom_port', 8765)}")
        print(f"   - WebSocket: ws://<PC_IP>:{_load_config().get('atom_port', 8765)}/ws")
    else:
        print("\n⚠️ API server ไม่พร้อมใช้งาน (FastAPI not installed)")

    print("\n📋 คำสั่งที่รองรับ:")
    print("   GET  /health — ตรวจสอบสถานะ")
    print("   GET  /status — ดูสถานะ connections")
    print("   POST /command — ส่ง command จาก Atom")
    print("   GET  /result/:id — ดูผลลัพธ์")
    print("   WS   /ws — real-time updates")
    print("   POST /sync/memory — sync memory")

    # ทดสอบ sync
    print("\n🔄 ทดสอบ memory sync...")
    test_memory = {"test": True, "timestamp": datetime.now().isoformat()}
    result = sync_memory_to_cloud(test_memory)
    print(f"   Sync to cloud: {'✅' if result else '❌ (gdrive disabled)'}")

    downloaded = sync_memory_from_cloud()
    print(f"   Sync from cloud: {'✅' if downloaded else '❌ (gdrive disabled)'}")

    print("\nกด Ctrl+C เพื่อหยุด")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 ปิด Atom Bridge")
