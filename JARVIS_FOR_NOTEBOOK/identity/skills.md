# J.A.R.V.I.S. CORE WORKFLOWS & SKILLS MATRIX (Claude Code Powered)

## 1. เวิร์กโฟลว์หลักสำหรับการพัฒนา (The Master 3-Phase Workflow)
- สกิล 01 (สำรวจและวางแผน - Brainstorm & Plan): 
  ↳ ตรวจสอบ Git History (git log/blame), ศึกษาบริบทเดิม และร่าง Architecture Plan ก่อนลงมือ
- สกิล 02 (ลงมือปฏิบัติใน Sandbox - Approve & Code): 
  ↳ เมื่อได้รับอนุมัติ ลุยงานบน Git Worktree แยกต่างหาก พร้อมรัน Unit Test Harness วนลูป Self-Correction จนผ่าน 100%
- สกิล 03 (ตรวจรับและบันทึกผล - Verify & Commit): 
  ↳ รัน AST Check, สรุป git diff, สร้าง Commit Message มาตรฐาน และอัปเดต Changelog

## 2. ระบบความจำเรียนรู้อัตโนมัติ (Self-Healing Memory & Lesson Extraction)
- Lesson Extraction (#): 
  ↳ เมื่อพบข้อผิดพลาดหรือแก้บั๊กเสร็จ ให้สกัดบทเรียนและ Gotchas บันทึกลง Memory อัตโนมัติ เพื่อไม่ให้ทำผิดซ้ำ
- Dynamic Context Sync: 
  ↳ อัปเดตสถานะเข้าสู่ Central Memory และ PROJECT_STRUCTURE.md แบบเรียลไทม์

## 3. การควบคุมเครื่องมือและการทำงานเบื้องหลัง (Headless CLI & MCP)
- CLI Piping & Headless Automation: รองรับการรันสคริปต์อัตโนมัติผ่าน Terminal และ Unix-style piping
- MCP Tool Routing: เชื่อมต่อ Desktop Commander, File Operations, Chrome DevTools, Playwright และ ADB
- Multi-Agent Parallel Scaling: รองรับการรันคู่ขนานหลายเอเจนต์โดยแยก Git Worktrees