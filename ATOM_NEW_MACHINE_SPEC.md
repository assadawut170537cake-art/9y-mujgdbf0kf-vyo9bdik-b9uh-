# ATOM — NEW MACHINE SPECIFICATION
### Build sheet for the consolidated workstation

_Issued 2026-10-06 · Baseline = the current machine (measured, not estimated)_

---

## 1. Current machine — measured baseline

| Component | Measured |
|---|---|
| OS | Windows 11 Pro, build 26200 |
| CPU | Intel Xeon E5-2690 v3 @ 2.60 GHz — 12 cores / 24 threads |
| RAM | 127.9 GB |
| GPU | NVIDIA **Quadro P4000**, 8 GB VRAM, driver 582.67 |
| Storage | C: 476 GB (128 free) · D: 1754 GB (362 free) · F: 238 GB · G: 261 GB · J: 477 GB (315 free) |
| Node | v26.7.0 / npm 11.19.0 |
| Python | 3.14.7 (plus 3.12 via uv) · uv 0.12.15 · pip 26.2.1 |
| Others | git 2.53.0 · ollama 0.35.1 · docker 29.7.2 (daemon not running) · ffmpeg 9.0.1 · winget 1.29.380 |

**Diagnosis of the baseline.** The machine is a *server-class CPU + huge RAM + weak GPU* box.
RAM is abundant (127.9 GB) but the **8 GB Quadro P4000 cannot hold the local models that are actually
installed** — `qwen3.8:27b` (17 GB) and `orcarouter/Qwen3.8-27B-Uncensored` (17 GB) do not fit in
VRAM and spill to CPU, which is why local inference is slow. C: is also down to 128 GB free.

---

## 2. Recommended specification

### Tier A — "do it properly" (recommended)

| Component | Spec | Why |
|---|---|---|
| CPU | 16–24 cores, modern (Ryzen 9 9950X / Threadripper 7960X / Xeon w7) | agent fan-out, builds, containers |
| RAM | 128 GB DDR5 ECC | keep parity with baseline; multiple local models + VMs |
| GPU | **NVIDIA RTX 5090 32 GB** (or 2× RTX 4090 24 GB) | a 27B q4 model (~17 GB) + KV cache fits in VRAM → local inference becomes fast |
| System SSD | 2 TB NVMe Gen4 | OS + toolchains + model cache |
| Data SSD | 4 TB NVMe Gen4 | project drive (`J:` role), model store, backups |
| Network | 2.5 GbE minimum | model/asset pulls, remote sessions |
| Power | 1000 W 80+ Platinum | GPU headroom |
| OS | Windows 11 Pro (keep WSL2) or Ubuntu 24.04 LTS | Hermes + peer agents run on both |

### Tier B — "budget but workable"

| Component | Spec |
|---|---|
| CPU | Ryzen 9 7900X / Core i9-14900K |
| RAM | 64 GB DDR5 |
| GPU | **RTX 4090 24 GB** or RTX 3090 24 GB (used is fine — VRAM is what matters) |
| Storage | 1 TB NVMe system + 2 TB NVMe data |
| OS | Windows 11 Pro |

### Tier C — "keep the current box, fix the bottleneck"
Keep CPU/RAM/storage; **replace only the GPU** with a 24–32 GB card and move the model store off
C:. Cheapest path to a usable local-model workstation.

> **Decision driver:** if the plan is to run ≥27B local models routinely, VRAM is the single spec that
> matters. If inference will mostly go to cloud APIs (Supermemory, Gemini, Anthropic), Tier C is
> sufficient and the money is better spent on storage and 24/7 uptime.

---

## 3. Software manifest (everything currently installed that must be re-provisioned)

### Runtimes & toolchain
- Git for Windows 2.53+ · Node.js 26.x + npm 11.x · Python 3.14 + 3.12 (uv-managed)
- uv 0.12.x · pip 26.x · winget 1.29+ · ffmpeg 9.x · Docker Desktop 29.x (daemon enabled)

### Local model runtime
- Ollama 0.35+ with **only the four verified models** (8 GB GPU ceiling — larger models spill to CPU):
  `nomic-embed-text:latest` (embeddings), `gemma4:e4b` (24 tok/s), `qwen2.5-coder:7b` (21.7 tok/s),
  `dolphin3:8b` (~4.9 GB, the single uncensored pick)
- **Model store: `J:\OLLAMA_MODELS`** (already set machine-wide via `OLLAMA_MODELS`), so Windows and
  Ubuntu mount the same model files. Do not use a Linux-only filesystem for this path.

### Agent stack
- **Hermes Agent** v0.21.x (`AppData\Local\hermes\hermes-agent`) + gateway
- **Claude Code** (`~/.local/bin/claude`) · **Codex CLI** (npm global) · **OpenCode** (optional)
- **Cursor** · **VS Code** · **Antigravity CLI (`agy`)** — optional but present in the workflow
- MCP servers: `supermemory` (remote) and `supermemory_docs` (docs) registered per client

### Memory layer
- Supermemory plugin 1.0.1 → org `wdZDwW4LKqt62TUTyBLjNn`
- `SUPERMEMORY_API_KEY` in the Hermes env file (never in a repo, never in chat)
- Containers: parent `project_atom_memory_base_4folders` + `atom_core`, `atom_knowledge`,
  `atom_ideas`, `atom_user`

### Cloud / server side
- Google Cloud project `gen-lang-client-0007726885` (account `assadawut170537cake@gmail.com`)
- GCP VM observed at `136.111.26.173` (SSH key `~/.ssh/atom_deploy`)
- ATOM Core bundle: `J:\ATOM_SYSTEM\vps_core\` — FastAPI + systemd `atom-core.service`
  (`/opt/atom-core`, `Restart=always`), SQLite `/opt/atom-core/data/atom_master.db`

---

## 4. Install order (the provided script does this)

1. Windows updates + enable WSL2, long-path support, Developer Mode
2. Git, Node 26, Python 3.12/3.14, uv, ffmpeg, winget upgrades
3. Docker Desktop (daemon set to start automatically)
4. Ollama + model pulls (data drive)
5. Hermes Agent + gateway service (auto-start on login)
6. Claude Code, Codex CLI, OpenCode
7. Cursor, VS Code + MCP registration for Supermemory
8. `SUPERMEMORY_API_KEY` into the Hermes env file (operator enters it — never scripted, never logged)
9. `hermes plugins install supermemory` → `hermes plugins enable supermemory` →
   `hermes config set memory.provider supermemory`
10. Write `supermemory.json` (four containers, underscore-only tags) → restart gateway
11. Verification suite (see the installer's `-Verify` switch)

---

## 5. DECISIONS TAKEN (2026-10-06)

| Question | Decision |
|---|---|
| OS | **Windows + Ubuntu (dual boot)** |
| 24/7 operation | **No** — the machine will not run continuously |
| Local models | **Only what already runs on the existing GPU** — no hardware purchase |

### 5.1 Measured model viability on the existing GPU (Quadro P4000, 8 GB — 5.2 GB free)

Benchmarked on the current machine with Ollama 0.35.1. "100% GPU" = fully in VRAM.

| Model | Size | Placement | Eval rate | Verdict |
|---|---|---|---|---|
| `nomic-embed-text:latest` | 0.3 GB | **100% GPU** | — | ✅ **KEEP** (embeddings) |
| `gemma4:e4b` | 3.2 GB | **100% GPU** | **24.0 tok/s** | ✅ **KEEP** |
| `qwen2.5-coder:7b` | 4.7 GB | **100% GPU** | **21.7 tok/s** | ✅ **KEEP** (best all-rounder) |
| `dolphin3:8b` (uncensored, Llama 3.1 8B) | 4.9 GB | **100% GPU** | **34.5 tok/s** | ✅ **KEEP** (the one uncensored pick — fastest of all) |
| `edtorre/hermes-qwen3.5-9b-abliterated` | 8.6 GB | 36/64 CPU/GPU | 6.0 tok/s | ⚠️ runs, slow (≈3.5× slower) |
| `qwen2.5-coder:14b` | 10 GB | 36/64 CPU/GPU | 7.8 tok/s | ⚠️ runs, slow |
| `deepseek-r1:14b` | 10 GB | 36/64 CPU/GPU | 3.6 tok/s | ❌ too slow to use |
| `qwen2.5-coder:32b` | 19 GB | CPU spill | — | ❌ not viable |
| `qwen3.8:27b` | 17 GB | CPU spill | — | ❌ not viable |
| `orcarouter/Qwen3.8-27B-Uncensored:q4_K_M` | 17 GB | CPU spill | — | ❌ not viable |

**Conclusion:** the 8 GB card is good for models **≤ 5 GB** (7B-class at 4-bit, or MoE models with a
small active footprint). Anything ≥ 9 GB spills to CPU and drops below ~8 tok/s.

**Action on the new machine:** install only the three ✅ models. That is ~8 GB instead of ~63 GB, and
frees roughly **55 GB** of disk compared with the current model store.

### 5.2 What "no 24/7" means in practice

- **Memory is unaffected** — Supermemory is cloud-hosted, so every agent reads and writes the shared
  brain whenever it is running, and the data survives the machine being off.
- **Scheduled jobs catch up on boot — already built in, no change needed.** Hermes cron classifies each
  missed occurrence (`cron/jobs.py`): a run missed by less than half the job's period (clamped to
  2 h–2 h… i.e. `max(120 s, min(period/2, 7200 s))`) fires as a normal **late** run; anything older is
  classified **catch_up** — the accumulated misses are skipped and the job runs **once** as soon as the
  gateway is back. So a daily job missed overnight runs once at next boot, and a 15-minute nudge that
  was missed for a week runs once, not 672 times.
  **Decision: leave the five jobs as they are.** Verified with `hermes cron list` (5 active) and
  `hermes cron doctor` (no issues).
- **Remote access is only possible while the machine is powered on.** No wake-on-LAN or cloud jump
  host is planned, so remote work must happen during the machine's uptime window.
- **The ATOM Core VPS remains the only always-on component** — that is where anything that must run
  continuously should live.

### 5.3 Dual-boot layout (Windows + Ubuntu)

| Item | Recommendation |
|---|---|
| Disks | **Two separate NVMe drives** — one for Windows, one for Ubuntu. Avoids fighting over the EFI partition and makes re-imaging either side trivial. |
| Windows disk | 1 TB NVMe (OS + toolchain + agent stack) |
| Ubuntu disk | 1 TB NVMe (OS + dev toolchain + container workloads) |
| Shared data | The existing data drive(s), formatted **exFAT or NTFS** so both OSes mount it read/write. Do not put the Ollama model store on a Linux-only filesystem if Windows must also use it. |
| **Model store** | **`J:\OLLAMA_MODELS`** — decided. Set `OLLAMA_MODELS` at User + Machine scope (the installer does this) and mount the same volume on Ubuntu (e.g. `/mnt/ollama-models`), then point the Linux Ollama service at it. |
| Boot | Windows installed first, then Ubuntu (GRUB detects Windows). Secure Boot off or Ubuntu's signed shim. |
| GPU | Single GPU shared by both OSes — NVIDIA driver on each side. |

> **Note:** the Ubuntu side gives the always-on services (containers, schedulers, the ATOM Core
> client) a proper home. If a task must run continuously, run it there or on the VPS — not on the
> Windows desktop.

---

## 6. Revised recommendation given the decisions

Since **no new hardware is being bought** and there is **no 24/7 requirement**, the build becomes:

1. **Reuse the existing GPU** (8 GB is enough for the three kept models).
2. **RAM:** 128 GB is already ample; if building new, 64 GB is sufficient for this workload.
3. **Storage:** 2 × 1 TB NVMe (Windows + Ubuntu) + a shared data drive for models/projects.
4. **Everything else** (CPU, network, power) can be mid-range — the GPU and RAM are no longer the
   binding constraint once the ≥27B models are dropped.
5. **Software manifest** reduces accordingly: Ollama with 3 models, Hermes, Claude Code, Codex CLI,
   Cursor, VS Code, MCP registration, Supermemory wiring — all handled by
   `install_atom_workstation.ps1` (add `-SkipModels` and pull only the kept three).

---

## 7. Remaining open questions

1. ~~Which drive / mount point holds the shared model store?~~ **Answered: `J:\OLLAMA_MODELS`**
   (already set via the `OLLAMA_MODELS` env var at User + Machine scope; the store holds ~88 GB today).
2. ~~Convert the five cron jobs to catch-up, or let them skip?~~ **Answered: catch up.** Hermes already
   does this natively (missed runs older than the grace window are skipped and executed once at the
   next boot) — no configuration change required.
3. **Is `136.111.26.173` the ATOM Core VPS?** Operator is unsure. To confirm, run `gcloud auth login`
   once, then `gcloud compute instances list` and match the external IP; or check the provider console.
   Until then, treat the VPS as unverified and do not deploy to it.

