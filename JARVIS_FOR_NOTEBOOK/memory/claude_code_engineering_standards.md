# สรุปมาตรฐานวิศวกรรม Claude Code (Anthropic Official Tech Talk)

## 1. ปรัชญาและแก่นแท้ของระบบ (Agentic CLI Philosophy)
- Claude Code คือ Autonomous Agentic AI ทำงานบน Terminal / CLI เต็มรูปแบบ
- รองรับการทำงานกับระบบทั้งฟังก์ชัน แก้ไขโค้ดทั้งโมดูล รันคำสั่งคอมไพล์ และทดสอบได้ด้วยตนเอง
- ไม่ผูกติดกับ IDE ใดๆ ทำงานข้ามแพลตฟอร์มได้อย่างอิสระ (VS Code, Cursor, JetBrains, Terminal, SSH, Tmux)

## 2. กระบวนการทำงาน 3 ขั้นตอน (Three-Phase Execution)
1. Brainstorm: สำรวจและคิดแนวทางหลายรูปแบบก่อนลงมือ
2. Plan: จัดทำแผนสถาปัตยกรรม (Architecture Plan) ตรวจสอบความถูกต้องและผลกระทบ
3. Approve: ผู้ใช้ตรวจสอบและอนุมัติ (Approval Gate) ก่อนเริ่มแตะต้องไฟล์โค้ดจริง

## 3. วงรอบการแก้ไขตนเอง (Automated Feedback Loops)
- ผูกเครื่องมือทดสอบ (Unit Test, Linter, AST Checker) เข้ากับ Agent
- เมื่อรันแล้วพบ Error ให้ AI วิเคราะห์ผลลัพธ์และวนลูปแก้ตัวเอง (Self-Correction) จนกว่าจะผ่านเกณฑ์ 100%

## 4. โครงสร้างบริบทแบบลำดับชั้น (Hierarchical Context Architecture)
- Root CLAUDE.md: คู่มือและกฎเกณฑ์ส่วนกลางของทั้งโปรเจกต์
- Sub-directory CLAUDE.md: โหลดเฉพาะเมื่อเข้าไปทำงานในโฟลเดอร์ย่อยนั้นๆ
- User Memory: ค่า Preference ประจำตัวบุคคล
- Self-Healing Memory (#): สกัดบทเรียนจากความผิดพลาดบันทึกเป็น Gotchas ถาวร

## 5. การขยายผลขั้นสูง (Headless & Parallel Scaling)
- รองรับโหมด Non-interactive (`claude -p`) เชื่อมต่อผ่าน Unix Pipe (|)
- รันคู่ขนานอย่างปลอดภัยด้วย Git Worktrees เพื่อแยก Branch และโฟลเดอร์ไม่ให้โค้ดทับซ้อนกัน
