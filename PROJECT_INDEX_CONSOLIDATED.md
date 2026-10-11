# MARK-LV Project Index (Unified J.A.R.V.I.S. Ecosystem)

## Overview
J.A.R.V.I.S. Autonomous Operating System & Agentic Coding Engine v4.0.23 (Lead Architect: Khun Assadawut).
Unified cross-platform ecosystem combining:
1. **J.A.R.V.I.S. Desktop Native App** (`JARVIS_FOR_NOTEBOOK/JARVIS_Desktop_v1.4.0.exe` - Wails/Svelte 5 Desktop OS)
2. **J.A.R.V.I.S. Python Core HUD** (`main.py` + `ui.py` with 2D Emoji State Avatar & Gemini Live API)
3. **Automated Windows Installer** (`dist_installer/JARVIS_v4.0.23_Setup.exe` via Inno Setup 6)
4. **Agentic Knowledge & Learning Plugins** (`plugins/notebooklm_plugin.py`, `plugins/auto_learner.py`, `plugins/web_researcher.py`)

## Project Structure
```
Mark-LV/
├── main.py — Python Engine Entry Point (HUD + Gemini Live v1beta)
├── ui.py — UI layer (HUD, Overlays & Plugin Management)
├── start_jarvis_unified.bat — One-Click Unified Launcher
├── requirements.txt — Dependencies
├── JARVIS_FOR_NOTEBOOK/ — Desktop App v1.4.0, Mobile APKs & Master Identity Specs
│   ├── JARVIS_Desktop_v1.4.0.exe
│   ├── JARVIS_Mobile_v1.0.4_Release.apk
│   ├── identity/ (context.md, identity.md, skills.md, thinking.md)
│   └── memory/ (claude_code_engineering_standards.md)
├── actions/ — 20 bundled action handlers (including game_updater / self_updater)
├── plugins/ — Drop-in plugins (notebooklm, auto_learner, web_researcher)
├── core/ — 17 core modules (including lightweight 2D emoji avatar.py)
├── memory/ — Persistent memory manager & long-term storage
├── deployment/ — Inno Setup Script (jarvis_installer.iss)
└── dist_installer/ — Generated Windows Setup executable (JARVIS_v4.0.23_Setup.exe)
```


## Actions (21 modules)
| Module | Lines | Key Functions |
|--------|-------|---------------|
| background_monitor.py | 160 | add_monitor, remove_monitor, list_monitors, check_all |
| browser_control.py | 1133 | _resolve_browser, _detect_default_browser, _open_native |
| code_helper.py | 634 | generate_content, _read_file, _save_file, _preview |
| computer_control.py | 590 | _type, _random_data, _user_profile |
| computer_settings.py | 963 | volume_up/down/mute/get, brightness_get/set |
| desktop.py | 519 | set_wallpaper, organize_desktop |
| dev_agent.py | 640 | generate_content, _plan_project, _parse_traceback |
| file_controller.py | 770 | _undo_move, _undo_create, _undo_write, _restore_from_trash |
| file_processor.py | 924 | _process_image, _process_pdf, _process_text_doc |
| flight_finder.py | 406 | flight_finder, _search_flights_browser |
| game_updater.py | 1102 | _find_steam_path, _get_steam_libraries, _get_steam_games |
| open_app.py | 294 | open_app, _launch_windows/macos/linux |
| proactive.py | 128 | ProactiveEngine, should_trigger, build_prompt |
| reminder.py | 368 | reminder, _schedule_windows/macos/linux |
| screen_processor.py | 184 | _capture_screen, _cv2_backend, _probe_camera |
| send_message.py | 349 | _send_whatsapp, _desktop_send, _search_in_app |
| system_monitor.py | 201 | get_system_status, check, _get_gpu_usage |
| video_player.py | 318 | video_player, _play_youtube |
| weather_report.py | 72 | weather_action |
| web_search.py | 417 | _gemini_search, _ddg_search, _run_bounded |
| youtube_video.py | 476 | _get_transcript, _summarize_with_gemini, _save_summary |

## Core (17 modules)
| Module | Lines | Key Classes/Functions |
|--------|-------|----------------------|
| action_loader.py | 222 | ActionRecord, ActionRegistry, discover_actions |
| audio_devices.py | 422 | configure, prefetch, _collect |
| avatar.py | 716 | HoloAvatar, step, paint, _mouth_step |
| avatar_mesh.py | 352 | build_head, _load_obj |
| confirm.py | 162 | _Pending, bind, request, resolve |
| echo.py | 289 | EchoGuard, band_energies, calibrated |
| gemini.py | 550 | _Reply, live_model, api_key, client |
| hotkey.py | 174 | PushToTalk, chord_label, qt_sequence |
| installer.py | 139 | _available, _pip, install_for_config |
| llm_client.py | 587 | get_llm_provider, ensure_ollama_running, call_llm |
| plugin_loader.py | 286 | PluginRecord, PluginRegistry, settings_schemas |
| stt.py | 94 | WhisperSTT, VoskSTT, transcribe |
| tts.py | 443 | EdgeTTSEngine, KokoroTTSEngine, ElevenLabsTTSEngine, TTSPlayer |
| undo.py | 122 | push_undo, can_undo, undo_last |
| viseme.py | 276 | VisemeStream, text_to_visemes |
| wake_word.py | 212 | WakeWordDetector, start, stop, feed |
| __init__.py | 1 | (empty) |

## Plugins (2 modules)
- _template.py — 46 lines, run() function
- __init__.py — empty

## Memory (3 modules)
- config_manager.py — 384 lines, API key management, config
- memory_manager.py — 479 lines, load/save/update memory
- __init__.py — empty

## Dashboard (2 components)
- server.py — 885 lines, DashboardServer, FastAPI+WebSocket
- __init__.py — empty

## Config (1 module)
- __init__.py — platform detection, get_config

## Dependencies (39 items)
PyQt6, sounddevice, numpy, google-genai, requests, beautifulsoup4, playwright, yt-dlp, pyautogui, pyperclip, pillow, opencv-python, mss, psutil, send2trash, python-pptx, fastapi, uvicorn, cryptography, python-multipart, qrcode, google-api-python-client, google-auth-oauthlib, tinytuya, paho-mqtt, openpyxl, youtube-transcript-api, pygetwindow, comtypes, pycaw, win10toast, pywin32, wmi, pywinauto, ddgs, pdfplumber, PyPDF2, python-docx, pynvml

## Entry Points
- main.py: J:\Mark-LV\main.py
- setup.py: J:\Mark-LV\setup.py

## File Stats
- Total: 62 files
- Python: 49 files
- Size: 1.3MB
- Extensions: .py (49), .md (1), .txt (2), .json (1), .ico (1), .crt (1), .key (1), .obj (1), .html (2), .js (1)

## Key Features
- Agent/automation system architecture
- Modular plugin-based design
- State/memory persistence
- Dashboard UI with FastAPI+WebSocket
- Action handler system (21 actions)
- Multi-platform (Windows/macOS/Linux)
- LLM integration (Gemini, Ollama)
- STT/TTS (Whisper, Edge, Kokoro, ElevenLabs)
- Wake word detection
- Screen processing & computer control
- File management with undo
- Web search, YouTube, flight finder
- System monitoring
- Proactive engine