# Changelog

All notable changes to **hyperv-mcp** are documented here.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (SemVer 1.0 commitment lands at v1.0; pre-1.0 minors may break).

## [Unreleased]

_Nothing yet._

## [0.1.0] — 2026-05-24

First public spike. Spec + mock backend + scaffolding only — no live Hyper-V calls.

### Added

- MCP server scaffold (`server.py`) targeting MCP protocol `2026-03-05`, stdio transport, with the official `mcp` Python SDK wiring.
- `mcp.json` manifest declaring five tools: `list_vms`, `start_vm`, `stop_vm`, `snapshot_vm`, `get_vm_metrics`.
- `spec.md` — canonical behavior contract: input / output / error envelope per tool, error code table, ISO-8601 timestamp convention, `HYPERV_MCP_MODE=mock|live` switch.
- Mock backend covering all five handlers with three fixture VMs (`LINC-01`, `LINC-02`, `THUNDER-BASE`) that survive in-process mutation across handler calls.
- PowerShell wrappers under `tools/` for each tool — define the v0.2 cmdlet boundary; emit canned JSON for v0.1 so the scaffold parse-checks end-to-end.
- `tests/mock_server_test.py` — three end-to-end cases (list-then-start state flip, snapshot UUID + idempotency, error paths) — runs without the `mcp` SDK or Hyper-V role.
- `positioning.md` — competitive landscape vs `vagrant`, `packer`, `multipass`, `azure-mcp`, `terraform-mcp + hyperv provider`.
- `release_roadmap.md` — v0.1 → v1.1 milestones and exit criteria.
- `CONTRIBUTING.md` — dev setup, PR flow, "how to add a new tool" pattern.
- GitHub Actions CI (`.github/workflows/ci.yml`) — runs the mock test matrix on Python 3.10 / 3.11 / 3.12 against `windows-latest`, plus `ruff check` and PowerShell parse-check on every wrapper.
- MIT `LICENSE`.

### Known limitations (v0.1)

- **Mock only.** `HYPERV_MCP_MODE=live` falls back to mock with a console warning. No `Get-VM` is ever invoked.
- **stdio transport only.** Streamable HTTP arrives in v0.3 per the MCP 2026-03-05 AAIF priority list.
- **Single host.** No `-ComputerName` parameter; multi-host federation deferred to v1.0.
- **No PyPI publish.** Install via `git clone` for now.
- **Not on the Anthropic MCP registry.** Submission targeted for v1.0.
- **Not signed.** Code-signing for the future PyPI wheel is a v1.0 task.

### Security

- v0.1 only exposes mock fixtures; no cmdlet injection surface yet. The wrapper layer (`tools/*.ps1`) is the v0.2 attack surface and will be hardened (name allow-list / argument array splatting) before live mode ships.

## Release reference

- v0.2 (target 2026-06): wire real Hyper-V cmdlets, PyPI publish, live integration test suite.
- v0.3 (target 2026-07): MCP notifications + Streamable HTTP + Server Cards.
- v1.0 (target 2026-Q3): GPU-PV / SR-IOV tools, OpenTelemetry GenAI semantic conventions, MCP registry listing, SemVer 1.0 commitment.
- v1.1 (target 2026-Q4, commercial): per-host RBAC, multi-host federation, SIEM audit-trail sink, vGPU partitioning.

[Unreleased]: https://github.com/zaxardery8011-design/hyperv-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/zaxardery8011-design/hyperv-mcp/releases/tag/v0.1.0
