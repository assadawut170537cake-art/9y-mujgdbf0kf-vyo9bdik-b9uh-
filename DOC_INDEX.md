# ดัชนีโปรเจค Mark-LV (Mark V)

## ภาพรวมโปรเจค
- **ชื่อ**: Mark LV (Mark 5)
- **ผู้พัฒนา**: FatihMakes
- **ประเภท**: Personal AI Assistant ข้ามแพลตฟอร์ม
- **เทคโนโลยีหลัก**: Gemini Live API, PyQt6, Python 3.14.7
- **รองรับ**: Windows, macOS, Linux

## โครงสร้างโปรเจค

### ไดเรกทอรีหลัก
```
Mark-LV/
├── main.py          (2,321 บรรทัด)  - Entry point
├── ui.py            (5,848 บรรทัด)  - UI Layer (PyQt6)
├── setup.py         - ติดตั้งโปรเจค
├── requirements.txt - Dependencies
├── readme.md        (398 บรรทัด)    - เอกสารประกอบ
├── LICENSE          - ใบอนุญาต
├── PROJECT_INDEX.json - ดัชนีโปรเจค
├── venv/            - Virtual Environment
├── __pycache__/     - Python cache
│
├── actions/         (21 ไฟล์)       - Action Handlers
│   ├── background_monitor.py  (160 บรรทัด)
│   ├── browser_control.py     (1,133 บรรทัด)
│   ├── code_helper.py         (634 บรรทัด)
│   ├── computer_control.py    (590 บรรทัด)
│   ├── computer_settings.py   (963 บรรทัด)
│   ├── desktop.py             (519 บรรทัด)
│   ├── dev_agent.py           (640 บรรทัด)
│   ├── file_controller.py     (770 บรรทัด)
│   ├── file_processor.py
│   ├── flight_finder.py
│   ├── game_updater.py
│   ├── open_app.py
│   ├── proactive.py
│   ├── reminder.py
│   ├── screen_processor.py
│   ├── send_message.py
│   ├── system_monitor.py
│   ├── video_player.py
│   ├── weather_report.py
│   └── web_search.py
│
├── core/            (17 ไฟล์)       - Core Logic
│   ├── action_loader.py
│   ├── atom_bridge.py
│   ├── audio_devices.py
│   ├── avatar.py
│   ├── avatar_mesh.py
│   ├── confirm.py
│   ├── echo.py
│   ├── gemini.py
│   ├── hotkey.py
│   ├── installer.py
│   ├── llm_client.py
│   ├── plugin_loader.py
│   ├── stt.py
│   ├── tts.py
│   ├── undo.py
│   ├── viseme.py
│   ├── wake_word.py
│   └── __init__.py
│
├── config/          - Configuration
├── dashboard/       (2 ไฟล์)        - Dashboard Server
├── memory/          - Memory Manager
├── plugins/         (2 ไฟล์)        - Plugin System
├── sync/            - Sync Module
├── google_workspace_mcp/ - Google Workspace MCP
└── SpeakoFlow/      - SpeakoFlow Module
```

## คุณสมบัติหลัก

### 🎤 Voice & Audio
- **Gemini Live API**: Real-time voice streaming
- **Wake Word**: "Hey Jarvis" detection (local)
- **Push-to-Talk**: Ctrl+Space global hotkey
- **Audio Device Picker**: Select mic/speakers by name
- **Self-Echo Guard**: Never answers own voice
- **5 Native Gemini Voices**: Switch live

### 👤 Avatar & UI
- **Holographic Avatar**: Animated human head in HUD
- **Lip-Sync**: ~50 mouth shapes/second
- **Facial Acting**: Brows, gaze, blinking, nod
- **Face as Status**: Looks away while thinking
- **Reactive HUD**: Waveform pulses to audio
- **Live Theming**: Hue wheel / hex color picker

### 🧠 Memory & Intelligence
- **Persistent Memory**: Deep remembers projects/preferences
- **Memory Panel**: View/delete stored facts
- **Session Memory**: Summarizes conversations
- **Morning Briefing**: Time, recap, news
- **Proactive 2.0**: Context-aware check-ins
- **Background Monitoring**: Topic watching

### 🖥️ System Control
- **System Control**: Apps, volume, brightness, WiFi
- **Desktop Control**: Taskbar, windows, desktop
- **File Processor**: Read/summarize local files
- **Browser Control**: Open/navigate/interact
- **Send Message**: WhatsApp, Telegram
- **Reminders**: OS-native scheduled notifications

### 🌐 Web & Search
- **Multi-Mode Web Search**: news/research/price/compare/search
- **YouTube Video**: Play on HUD (muted, sound on request)
- **Weather Report**: Live localized weather
- **Flight Finder**: Search flights

### 🔌 Integration
- **Google Workspace**: Gmail, Calendar, Drive, Docs
- **MCP Server**: FastMCP Gateway :5050
- **Plugin System**: Drop .py file into plugins/
- **Remote Dashboard**: Phone control via QR

## Dependencies หลัก
- PyQt6>=6.6,<7 (UI Framework)
- google-genai>=2.8.0,<3 (Gemini API)
- sounddevice>=0.4,<1 (Audio I/O)
- numpy>=1.24,<3 (Numerics)
- opencv-python>=4.8,<5 (Vision)
- pynvml (GPU monitoring)
- playwright>=1.40,<2 (Browser automation)
- yt-dlp (YouTube download)
- pyautogui (Desktop control)
- fastapi>=0.110,<1 (Dashboard API)
- cryptography>=42,<50 (Security)
- paho-mqtt (IoT)
- tinytuya (Smart Home)

## โหมดการทำงาน
- **Green**: ทำงานอัตโนมัติ
- **Yellow**: บันทึก log ก่อน
- **Red**: ขออนุญาตก่อน

## จุดเด่น
- Zero subscriptions
- Total digital autonomy
- Cross-platform (Windows/macOS/Linux)
- Native C++ audio engine (Oboe)
- AGSL shader for 3D orb
- Model ladder (9 Gemini models)
- Sliding-window context compression
- Self-healing deployment loop
