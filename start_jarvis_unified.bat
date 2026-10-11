@echo off
chcp 65001 > nul
title J.A.R.V.I.S. Desktop OS v4.0.23 - Unified Launcher

echo ======================================================================
echo    J.A.R.V.I.S. AUTONOMOUS DESKTOP OS ^& AGENTIC SYSTEM v4.0.23
echo    Lead Architect: Khun Assadawut (Supreme Commander)
echo ======================================================================
echo.
echo [1] เปิด J.A.R.V.I.S. Desktop Native App (Svelte/Wails Desktop OS)
echo [2] เปิด J.A.R.V.I.S. Python Core HUD (พร้อม 2D Emoji Avatar)
echo [3] เปิดทั้งคู่พร้อมกัน (Full Unified Ecosystem)
echo [4] คอมไพล์ตัวติดตั้ง Windows (.exe Installer via Inno Setup)
echo [0] ออกจากโปรแกรม
echo.
set /p opt="กรุณาเลือกเมนู [1-4]: "

if "%opt%"=="1" goto run_desktop
if "%opt%"=="2" goto run_python
if "%opt%"=="3" goto run_both
if "%opt%"=="4" goto build_installer
if "%opt%"=="0" exit
goto end

:run_desktop
echo.
echo [*] กำลังเปิด J.A.R.V.I.S. Desktop Native App...
start "" "%~dp0JARVIS_FOR_NOTEBOOK\JARVIS_Desktop_v1.4.0.exe"
goto end

:run_python
echo.
echo [*] กำลังเริ่ม J.A.R.V.I.S. Python Core HUD...
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py
) else (
    python main.py
)
goto end

:run_both
echo.
echo [*] กำลังเปิดระบบแบบบูรณาการ Full Ecosystem...
start "" "%~dp0JARVIS_FOR_NOTEBOOK\JARVIS_Desktop_v1.4.0.exe"
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py
) else (
    python main.py
)
goto end

:build_installer
echo.
echo [*] กำลังคอมไพล์ Windows Installer ด้วย Inno Setup 6...
"C:\Users\CJN_assadawut17\AppData\Local\Programs\Inno Setup 6\ISCC.exe" "%~dp0deployment\jarvis_installer.iss"
if %ERRORLEVEL% EQU 0 (
    echo [✓] สร้างตัวติดตั้งสำเร็จ! ไฟล์อยู่ที่โฟลเดอร์: dist_installer\JARVIS_v4.0.23_Setup.exe
) else (
    echo [!] การคอมไพล์ขัดข้อง กรุณาตรวจสอบ log
)
pause
goto end

:end
