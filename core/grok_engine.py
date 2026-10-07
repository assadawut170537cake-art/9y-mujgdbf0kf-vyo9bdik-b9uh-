import asyncio
import json
import base64
import os
import websockets

class GrokEngine:
    def __init__(self, ui_logger=None, out_queue=None, audio_in_queue=None, set_state=None):
        self.ui_logger = ui_logger
        self.out_queue = out_queue
        self.audio_in_queue = audio_in_queue
        self.set_state = set_state
        self.running = False
        self._task = None

    def log(self, message: str):
        if self.ui_logger:
            self.ui_logger(f"SYS: {message}", "sys")
        else:
            print(f"[Grok] {message}")

    def start(self):
        self.running = True
        self._task = asyncio.create_task(self._run_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run_loop(self):
        api_key = os.environ.get("XAI_API_KEY", "")
        if not api_key:
            self.log("XAI_API_KEY not found in environment.")
            if self.set_state: self.set_state("SLEEPING")
            return

        headers = {"Authorization": f"Bearer {api_key}"}
        url = "wss://api.x.ai/v1/realtime?agent_id=agent_WPQ7at27A92BPQwG"
        
        try:
            async with websockets.connect(url, additional_headers=headers) as ws:
                self.log("JARVIS ONLINE (xAI Grok) connected.")
                if self.set_state: self.set_state("LISTENING")
                
                # Send initial greeting or configuration
                await ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {"type": "message", "role": "user",
                             "content": [{"type": "input_text", "text": "Hello, JARVIS is online."}]},
                }))
                await ws.send(json.dumps({"type": "response.create"}))
                
                send_task = asyncio.create_task(self._send_audio(ws))
                recv_task = asyncio.create_task(self._recv_audio(ws))
                
                await asyncio.gather(send_task, recv_task)
                
        except asyncio.CancelledError:
            self.log("Grok connection stopped.")
        except Exception as e:
            self.log(f"Grok connection error: {e}")
        finally:
            if self.set_state: self.set_state("SLEEPING")

    async def _send_audio(self, ws):
        while self.running:
            try:
                msg = await self.out_queue.get()
                if isinstance(msg, dict) and "data" in msg:
                    await ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": base64.b64encode(msg["data"]).decode("utf-8")
                    }))
                elif isinstance(msg, bytes):
                    await ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": base64.b64encode(msg).decode("utf-8")
                    }))
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Grok Send Error] {e}")
                break

    async def _recv_audio(self, ws):
        async for raw in ws:
            if not self.running:
                break
            try:
                event = json.loads(raw)
                if event["type"] == "response.output_audio_transcript.delta":
                    print(event.get("delta", ""), end="", flush=True)
                elif event["type"] == "response.output_audio.delta":
                    pcm = base64.b64decode(event["delta"])
                    if self.audio_in_queue:
                        try:
                            self.audio_in_queue.put_nowait(pcm)
                        except asyncio.QueueFull:
                            pass
            except Exception as e:
                print(f"[Grok Recv Error] {e}")
