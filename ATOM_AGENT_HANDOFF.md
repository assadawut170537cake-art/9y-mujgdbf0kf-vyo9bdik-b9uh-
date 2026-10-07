# ATOM — AGENT HANDOFF BRIEF
### Shared long-term memory + workstation build request

_Issued 2026-10-06 by **Hermes / คริกชี่** (local steward agent) on behalf of **อัษฎาวุธ เมืองซอง (ลูกพี่)**_
_Recipient: peer agent (J.A.R.V.I.S. / F.R.I.D.A.Y. / external builder)_

---

## 1. The single source of truth

All agent memory for this operation is now recorded in **Supermemory**, not in local files.
Any agent that authenticates to the same organisation sees the same brain.

| Field | Value |
|---|---|
| Provider | Supermemory — `https://api.supermemory.ai` |
| Console | `https://console.supermemory.ai` |
| Organisation ID | `wdZDwW4LKqt62TUTyBLjNn` |
| Account | `assadawut170537cake@gmail.com` |
| MCP endpoint (no API key needed) | `https://mcp.supermemory.ai/mcp` |
| Hermes integration | plugin `supermemory` 1.0.1 · `memory.provider: supermemory` |

### Container layout — parent + four folders

Parent namespace: **`project_atom_memory_base_4folders`**
(= `โปรเจคอะตอม\ฐานความจำรวม\4โฟรเด้อ`; underscore form is mandatory — the Hermes plugin rewrites
every character outside `[a-zA-Z0-9_]` to `_`, so colons/backslashes/Thai are not usable.)

| Container tag | Contents |
|---|---|
| `project_atom_memory_base_4folders_atom_core` | conversation memory, completed work, task context — **primary / auto-capture** |
| `project_atom_memory_base_4folders_atom_knowledge` | blueprints, J.A.R.V.I.S. Central Master Roadmap, cron + system digests, technical docs |
| `project_atom_memory_base_4folders_atom_ideas` | live ideas, pending work, voice memos awaiting triage |
| `project_atom_memory_base_4folders_atom_user` | operator profile: working style, rules of engagement, site coordinates |

### Isolation contract — do not break this
- A `containerTag` is a **hard boundary**. A search scoped to one container never returns another
  container's memories. Never assume cross-container recall.
- **One tag per request.** Singular `containerTag` in JSON bodies; `containerTags` (array) only on
  `/v4/memories/list` and `/v3/documents/list`.
- Tag charset `^[a-zA-Z0-9_:-]+$`, max 100 chars. Under Hermes: underscore only.
- Metadata filters narrow results *inside* one container — they can never cross a boundary.

### How another app joins the same memory
1. **MCP (preferred, no key):** add `https://mcp.supermemory.ai/mcp` → OAuth in browser → select the
   space. Already wired on the current PC for **Cursor** (`~/.cursor/mcp.json`) and
   **VS Code** (`%APPDATA%\Code\User\mcp.json`).
2. **Scoped API key (scripts / headless):** minted per container, cannot cross boundaries
   (`403` outside its own). Existing keys are stored in
   `AppData\Local\hermes\secrets\scoped_key_atom_*.txt` and are **never** to be echoed into chat.
   ```bash
   curl -X POST https://api.supermemory.ai/v3/auth/scoped-key \
     -H "Authorization: Bearer $SUPERMEMORY_API_KEY" -H 'Content-Type: application/json' \
     -d '{"containerTag":"project_atom_memory_base_4folders_atom_core","name":"<app>","expiresInDays":90}'
   ```

### Current memory contents (measured 2026-10-06)
- `atom_core` — 14 documents, **73 extracted memory facts**
- `atom_knowledge` — 19 documents, **4 facts** (roadmap + cron digests)
- `atom_user` — 1 document (operator profile), extraction in progress
- `atom_ideas` — empty, ready for capture

Local exports for offline review: `AppData\Local\hermes\exports\memory_facts\MEMORY_FACTS.md`
Runbook: `J:\01_JARVIS_CORE\ATOM_MEMORY_RUNBOOK.md` · Profile: `J:\01_JARVIS_CORE\ATOM_CORE_CONTEXT.md`

---

## 2. What we are asking for: one build machine

We need **one computer** provisioned so the entire stack — Hermes, the peer agents, the local model
runtimes and the dev toolchain — can be installed and run in one place, connected to the shared
memory above.

**Decisions already made by the operator (2026-10-06):**
- **OS: Windows + Ubuntu dual boot** (two separate drives recommended; see the spec document).
- **No 24/7 requirement** — the machine will not run continuously. Memory is cloud-hosted and
  unaffected; scheduled jobs simply skip while it is off.
- **No hardware purchase** — local models are limited to what already runs on the existing 8 GB GPU.

**Target:** see `ATOM_NEW_MACHINE_SPEC.md` for the hardware specification, the benchmarked model
shortlist and the exact software manifest. An idempotent installer is provided at
`install_atom_workstation.ps1` (it pulls only the three verified models).

**Minimum acceptance criteria for the delivered machine:**
1. Windows 11 Pro **and** Ubuntu, dual boot on separate drives, with a shared data drive both can mount.
2. Runs `install_atom_workstation.ps1` to completion with no manual intervention.
3. `hermes memory status` reports `Provider: supermemory · ✓ Connected`.
4. A write-then-search round trip against `atom_core` returns the written fact.
5. Ollama serves `qwen2.5-coder:7b` at **≥ 20 tok/s fully on GPU** (the verified baseline on the
   current 8 GB card is 21.7 tok/s — a new machine must not regress on this).

---

## 3. Operating rules that travel with this brief

- **Permission zones:** Green = act autonomously · Yellow = act but log first · Red = confirm first.
  Destructive or irreversible actions are Red: summarise the plan and blast radius, then wait.
- **Checkpoint before change:** back up config/code (`.bak` or git) before modifying anything.
- **Secrets:** never paste, echo or transmit an API key, token, password or verification code —
  including in this conversation. A key that was pasted anywhere is treated as burned and rotated.
- **Language:** the operator writes Thai (Thai/English mix). Address him as **ลูกพี่** or **บอส** and
  reply mainly in Thai regardless of the language he types in.
- **Refuse offensive tooling** (malware/RAT/rootkit, credential or cookie harvesting, trace erasure)
  and offer legitimate alternatives. Never fabricate a result to appear compliant.

---

## 4. Reply format we need back

When the machine is ready, return:
1. Hostname / access method (SSH endpoint or RDP + credentials **out of band**, never in chat).
2. Confirmation of each acceptance criterion above, with the raw command output.
3. Any deviation from the software manifest and why.
4. Whether the machine will run 24/7 (needed for the scheduled jobs currently bound to the old PC).
