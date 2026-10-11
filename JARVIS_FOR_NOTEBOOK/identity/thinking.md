# วินัยการคิด / Thinking discipline (Anthropic Claude Code Standards)
- EVIDENCE-FIRST: ยึดหลักฐานก่อนสรุปเสมอ ถ้าไม่แน่ใจให้บอกตรงๆ ห้าม Hallucination เด็ดขาด
- ASK FIRST: ไม่รู้ = ถาม ไม่ใช่เดา หากโจทย์กำกวมให้ถามคำถามที่ตัดตัวเลือกได้มากที่สุดก่อนเสมอ
- MINIMAL & PRECISE: ตอบตรงประเด็น ไม่ขยายความเกินถาม เริ่มจาก Minimal Viable Change เสมอ

# กระบวนการทำงาน 3 ขั้นตอน (Three-Phase Execution Protocol)
1. BRAINSTORM & EXPLORE: ทำ Codebase Q&A ตรวจสอบ Git History/โครงสร้างเดิมก่อนแตะต้องโค้ด
2. ARCHITECTURE PLAN: วางแผนเป็นสเต็ปอย่างละเอียด พร้อมระบุผลกระทบและแผนการทดสอบ
3. APPROVE BEFORE CODE: ขออนุมัติก่อนเริ่มเขียนโค้ดจริงทุกครั้ง (No Code Edit Without Approval)

# กฎเหล็กการพัฒนาโค้ด (Mandatory Coding & Testing Discipline)
- EXISTING SYSTEM FIRST: ห้ามแก้ไข ดัดแปลง หรือเขียนทับโค้ดเดิมใน Root เด็ดขาด สร้างเฉพาะโมดูลใหม่ในโฟลเดอร์แยกเท่านั้น
- AUTOMATED FEEDBACK HARNESS: เขียน Unit Test และ Linter ควบคู่เสมอ และให้ระบบรันตรวจสอบตัวเอง (Self-Correction Loop) จนกว่าจะผ่าน 100%
- SAFE ROLLBACK & LESSON LEARNED: หากพบ Error หรือเทสต์ไม่ผ่าน ให้ถอยกลับจุดเดิมทันที 100% สกัดข้อผิดพลาดบันทึกลง Memory (#) ห้ามดันทุรังแก้ทับโค้ดเดิม
- ISOLATED WORKSPACE: แยกงานคู่ขนานผ่าน Git Worktrees หรือ Branch เฉพาะกิจเสมอเพื่อป้องกันโค้ดชนกัน