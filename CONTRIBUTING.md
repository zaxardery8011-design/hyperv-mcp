# Contributing to hyperv-mcp

Thanks for considering a contribution. This document covers local dev setup, the PR flow, and the pattern for adding a new tool. Keep it short and current — if you find a step wrong, fix it in the same PR as your change.

## TL;DR

```powershell
git clone https://github.com/zaxardery8011-design/hyperv-mcp.git
cd hyperv-mcp
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install mcp ruff
$env:HYPERV_MCP_MODE = "mock"
python tests\mock_server_test.py   # must report 3 / 3 PASS
ruff check server.py tests\
```

If both commands succeed you have a working dev environment.

## Requirements

| Tool | Minimum | Notes |
|---|---|---|
| Windows | 10 / 11 / Server 2022+ | Hyper-V role *not* required for mock mode |
| Python | 3.10 | 3.12 is the CI target |
| PowerShell | 5.1 or pwsh 7+ | tools/*.ps1 wrappers parse-checked in CI |
| Git | any | |
| `mcp` Python SDK | latest | only needed to wire the SDK transport — handlers are import-clean without it |

For v0.2 (live Hyper-V) you additionally need: Hyper-V role enabled, membership in the `Hyper-V Administrators` group, and at least one VM defined on the host. None of that is needed to land changes in v0.1.

## Repo layout

```
hyperv-mcp/
├── server.py              # MCP server entry + handlers
├── mcp.json               # tool manifest (schema source of truth)
├── spec.md                # behavior contract (read before changing handlers)
├── tools/                 # PowerShell wrappers (v0.2 cmdlet boundary)
├── tests/mock_server_test.py
├── .github/workflows/ci.yml
├── CONTRIBUTING.md        # this file
├── CHANGELOG.md
├── RELEASE_PLAN.md
└── README.md
```

## PR flow

1. Open an issue first if the change is non-trivial (new tool, schema break, behavior change). Tiny doc / typo PRs can skip this.
2. Fork → branch off `main`. Branch name: `feat/<scope>`, `fix/<scope>`, or `docs/<scope>`.
3. Make the change. Keep the diff focused — one tool or one fix per PR.
4. Run the local checks (above). CI runs the same checks on Python 3.10 / 3.11 / 3.12 against `windows-latest`.
5. Update `CHANGELOG.md` under the `## [Unreleased]` heading. One line, present-tense, user-facing wording. Don't paraphrase your commit message — describe what users will see change.
6. Open the PR. The description should answer: what changed, why, and how it was tested. If it changes a tool schema, link the relevant section of `spec.md`.

## Adding a new tool

Tools must round-trip through three places. Add them in this order:

### 1. Spec it in `spec.md`

Describe input, output (success), output (idempotent / no-op), error cases. Use the existing five tools as templates. Mention the backing PowerShell cmdlet under "Backing cmdlet (v0.2)".

### 2. Declare it in `mcp.json`

Add a tool entry with `name`, `description`, and `inputSchema` (JSON Schema draft 2020-12). Match the field names used in `spec.md` exactly. Keep `description` LLM-readable: one sentence ending in a period.

### 3. Implement the handler in `server.py`

```python
def handle_<tool_name>(args: dict[str, Any]) -> dict[str, Any]:
    # Validate required fields → _err("invalid_arg", "...") on miss
    # Look up VM → _err("vm_not_found", "...") if absent
    # Mutate the mock state (if applicable)
    # Return the success envelope from spec.md
```

Then register it in `TOOL_HANDLERS`. If the handler does not touch `_MOCK_VMS`, it can be pure — preferred where possible.

### 4. Add a PowerShell wrapper under `tools/`

Even in v0.1 (mock backend), the wrapper script must exist and parse-check cleanly. It defines the cmdlet boundary for v0.2. Output JSON to stdout via `ConvertTo-Json -Depth 5`. Use the existing five wrappers as templates.

### 5. Test it

Add a `@case(...)` to `tests/mock_server_test.py`. Cover at least: happy path, one error path, idempotency or no-op behavior if applicable. Aim for one test function per tool to keep diff blame readable.

## Code style

- Python: ruff defaults. No mypy gate yet (planned for v0.3). Type hints encouraged; `from __future__ import annotations` is on.
- PowerShell: 2-space indent, PascalCase for cmdlet params (`-Name`, not `-name`). Always specify `-ErrorAction Stop` on cmdlets whose errors must propagate.
- JSON: 2-space indent in `mcp.json`. Field naming is `snake_case` everywhere we control (matches `spec.md` exactly); we *don't* echo PowerShell's PascalCase out to the LLM.
- No comments narrating what the code does. Comments are for *why* — invariants, references to spec sections, gotchas.

## Schema breaks

Renaming or removing a tool / field is a breaking change. v0.x can ship breaks but each one needs:

- a `CHANGELOG.md` entry under a `### Breaking` heading,
- a `spec.md` change in the same PR, and
- a one-line migration note (old → new).

v1.0 will commit to semver. Until then, breaks land on `main` with a clear changelog entry rather than a deprecation cycle.

## Filing bugs

Include:

- Windows build (`winver`)
- Python version
- Output of `python tests/mock_server_test.py` (pass/fail per case)
- The exact tool call + arguments that misbehaved (redact VM names if sensitive)
- Whether `HYPERV_MCP_MODE` was `mock` or `live`

## Security

Found a security issue (cmdlet injection via VM name, server card spoofing, etc.)? Don't open a public issue. Email the maintainer (see repo metadata). We'll respond within 7 days and coordinate disclosure.

## License

By contributing you agree your contribution is licensed under the [MIT License](LICENSE), the same license as the rest of the project.
