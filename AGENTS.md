# Autonomous AI & Jules Operating Guidelines

## 1. System Philosophy & Architecture
- Explicit Logic: Never compress or minify code to reduce line count. Maintain explicit structure, clean branching, and high readability.
- Stability & Robustness: Prioritize runtime resilience over clever optimizations. All asynchronous calls and external integrations must be wrapped in structured error-handling blocks.
- Scope Boundaries:
  - ALLOWED MODIFICATIONS: `src/utils/`, `src/services/`, `src/helpers/`, `tests/`
  - STRICTLY FORBIDDEN: `src/core/auth/`, `src/config/keys/`, `database/migrations/`, and CI deployment secrets.
  - MASTER ENV RULE: The `.env` file at `J:\Mark-LV\.env` is the SINGLE SOURCE OF TRUTH for all API keys and environment configurations across ALL projects and models. Do NOT create or use scattered `.env` files in other directories. All apps must read from this master file.

## 2. Code Quality & Standards
- Function Documentation: Every modified or created function must include an explanatory docstring/comment detailing:
  - Core responsibility
  - Input parameters with explicit data types
  - Return values with explicit data types
- Error Handling: Mandatory try-catch blocks with descriptive logging:
  - Log error context with meaningful message prefixes.
  - Return safe fallbacks or rethrow controlled custom errors. Do not swallow exceptions silently.
- Type Safety: Ensure strict type validation and schema assertions for all incoming payloads.

## 3. Automated Task Execution Rules
- Suggested Tasks: Only address tasks where requirements and boundaries are explicitly detailed.
- Scheduled Tasks:
  - Weekly audits must focus exclusively on backward-compatible, non-breaking dependency updates.
  - Test coverage improvements must only append new tests without modifying existing assertions.

## 4. Verification & Pull Request Protocol
- Pre-submission Checks: All local unit and integration tests must execute and pass before submitting a Pull Request.
- Pull Request Content:
  - Concise summary of changes.
  - Exact reference to the triggered TODO tag or Scheduled Task directive.
  - Explicit notification if any external dependencies or schema shapes were touched.
