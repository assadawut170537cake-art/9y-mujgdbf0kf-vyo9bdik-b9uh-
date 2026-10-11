# ATOM MEMORY — RUNBOOK (single shared memory for every agent app)

_Updated 2026-10-06 · Owner: อัษฎาวุธ เมืองซอง (ลูกพี่)_

---

## 1. The shared brain

| Item | Value |
|---|---|
| Provider | Supermemory (`https://api.supermemory.ai`) |
| Hermes plugin | `supermemory` 1.0.1 (enabled) · `memory.provider: supermemory` |
| Hermes config | `AppData\Local\hermes\supermemory.json` |
| API key (Hermes) | `AppData\Local\hermes\.env` → `SUPERMEMORY_API_KEY` |
| Account / org | `assadawut170537cake@gmail.com` · org `wdZDwW4LKqt62TUTyBLjNn` |

### Container layout (parent → 4 folders)

Parent namespace: **`project_atom_memory_base_4folders`**
(= โปรเจคอะตอม\ฐานความจำรวม\4โฟรเด้อ → underscore form, because the Hermes plugin rewrites any
character outside `[a-zA-Z0-9_]` to `_`.)

| Child | Purpose | Who writes |
|---|---|---|
| `..._atom_core` | conversation memory, completed work, task context (**primary / auto-capture**) | Hermes auto, all apps |
| `..._atom_knowledge` | blueprints, Central Master Roadmap, cron + system digests, technical docs | cron, subagents, docs |
| `..._atom_ideas` | live ideas, pending work, voice memos awaiting triage | on demand |
| `..._atom_user` | operator profile: working style, rules of engagement, site coordinates | profile seeding |

**Isolation rule:** a search scoped to one container never returns another container's memories.
Metadata filters narrow results *inside* a container only.

---

## 2. Connect another app (so it syncs into the same brain)

### Option A — MCP (no key to manage, recommended for desktop apps)

Server URL: `https://mcp.supermemory.ai/mcp` → the app opens a browser OAuth flow → sign in and pick
the space. Already wired up on this machine:

| App | Config file | Status |
|---|---|---|
| Cursor | `%USERPROFILE%\.cursor\mcp.json` | added (`mcpServers.supermemory`) |
| VS Code | `%APPDATA%\Code\User\mcp.json` | added (`servers.supermemory`) |
| Claude Desktop / ChatGPT | add the same URL in the app's connector dialog | manual (not installed here) |

### Option B — scoped API key (for scripts, bots, headless services)

Keys are minted per container and **cannot cross** into another container (a request for a foreign
tag returns `403`). Values are stored, never printed:

```
AppData\Local\hermes\secrets\
  scoped_key_atom_apps.txt        -> atom_core      (general app sync)
  scoped_key_atom_knowledge.txt   -> atom_knowledge
  scoped_key_atom_ideas.txt       -> atom_ideas
  scoped_key_atom_user.txt        -> atom_user
```

Mint another one:

```bash
curl -X POST https://api.supermemory.ai/v3/auth/scoped-key \
  -H "Authorization: Bearer $SUPERMEMORY_API_KEY" -H 'Content-Type: application/json' \
  -d '{"containerTag":"project_atom_memory_base_4folders_atom_core","name":"<app>","expiresInDays":90}'
```

Revoke: `DELETE /v3/auth/scoped-key/<KEY_ID>` (memories and containers are untouched).

---

## 3. Scripts on this machine

| Script | Purpose |
|---|---|
| `AppData\Local\hermes\scripts\import_history_to_supermemory.py` | backfill Hermes sessions from `state.db` → `/v4/conversations` (`--dry-run` / `--session <id>` / `--all`) |
| `AppData\Local\hermes\scripts\export_memories.py` | export extracted memory facts → `exports\memory_facts\` (`MEMORY_FACTS.md`, per-container JSON) |
| `AppData\Local\hermes\scripts\seed_atom_context.py` | seed `atom_user` (operator profile) + `atom_knowledge` (roadmap) from local docs |

All three read `SUPERMEMORY_API_KEY` from the environment and never print it.

---

## 4. Cloud / uptime — keep things running with the PC off

### What already survives a shutdown
- **Memory** — Supermemory is cloud-hosted: every memory, profile and container stays available to
  any app that authenticates, whether or not this PC is on.
- **Scheduled jobs** — Hermes cron only fires while the gateway runs on this PC. With the PC off, no
  job fires. Migrate the recurring ones (daily crypto digest, hydration nudge, weekly review) to a
  cloud scheduler if they must run unattended.
- **RDP / SSH access** — this machine is only reachable when powered on; that needs wake-on-LAN or a
  cloud jump host.

### Cloud assets present
- Google Cloud project **`gen-lang-client-0007726885`** (account `assadawut170537cake@gmail.com`).
- GCP VM observed earlier at `136.111.26.173` (SSH key `~/.ssh/atom_deploy`).
- ATOM Core service bundle: `J:\ATOM_SYSTEM\vps_core\` — FastAPI (`main.py`), `atom-core.service`
  systemd unit (`/opt/atom-core`, `Restart=always`), `setup_ingress.sh`, SQLite at
  `/opt/atom-core/data/atom_master.db`.

### Open items (need the operator)
1. **`gcloud auth login`** — every cached token in `%APPDATA%\gcloud\access_tokens.db` is expired, so
   VM state cannot be read or deployed. Run it once interactively, then cloud work can continue.
2. **Confirm the VPS host** — is `136.111.26.173` the ATOM Core box, and is `atom-core.service`
   currently enabled and running there?
3. **Decide what must run 24/7** — memory (already cloud) vs cron jobs (currently PC-bound).

---

## 5. Routine operations

```bash
# health
hermes memory status                     # expect: Provider supermemory · ✓ Connected
curl -s -o /dev/null -w '%{http_code}\n' -X POST https://api.supermemory.ai/v3/search \
  -H "Authorization: Bearer $SUPERMEMORY_API_KEY" -H 'Content-Type: application/json' \
  -d '{"q":"probe","containerTag":"project_atom_memory_base_4folders_atom_core"}'   # expect 200

# backfill / re-export
python scripts/import_history_to_supermemory.py --all
python scripts/export_memories.py

# list containers
curl -s -H "Authorization: Bearer $SUPERMEMORY_API_KEY" \
  https://api.supermemory.ai/v3/container-tags/list
```

Backups of touched config live next to the originals as `*.bak_<timestamp>`
(e.g. `~/.cursor/mcp.json.bak_20261006_170538`) and in
`AppData\Local\hermes\backups\pre-supermemory_*`.

---

## 6. Guardrails

- Never paste or echo an API key / token / verification code in chat. Keys go into `.env` or
  `secrets\` only; a key that was pasted into a conversation is treated as burned and rotated.
- `.env` and `secrets\` stay out of any git repo.
- Offensive-tooling requests are refused with legitimate alternatives; results are never fabricated.
