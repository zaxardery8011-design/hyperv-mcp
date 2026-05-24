# Release Roadmap — hyperv-mcp

| Version | Scope | Exit criteria | ETA |
|---|---|---|---|
| **v0.1** (this spec) | Manifest + scaffold + mock backend + 5 tool stubs + mock e2e tests + docs | All `tests/mock_server_test.py` cases pass; `mcp.json` validates against MCP 2026-03-05 manifest schema | **2026-05-24** |
| **v0.2** | Real Hyper-V cmdlet wiring; live host integration tests; published to PyPI | Live integration suite passes on Hyper-V Server 2025 + Windows 11 Pro Hyper-V; pip-installable | 2026-06 |
| **v0.3** | MCP notifications for VM state changes; Streamable HTTP transport; Server Cards `.well-known` | Notification e2e test (start a VM, receive `vm_state_changed` push within 2s); HTTP test pass | 2026-07 |
| **v1.0** | GPU-PV attach/detach + SR-IOV + vGPU partitioning tools; production-ready logging + structured errors; registry listing | Registry-listed (Anthropic MCP directory); 500+ stars OR 3 enterprise pilots; SemVer 1.0 commitment | 2026-Q3 |
| **v1.1** (commercial) | Per-host RBAC, multi-host federation, audit-trail SIEM sink, vGPU per-tenant partitioning, SLA support | First paid customer; commercial license alongside MIT core | 2026-Q4 |

## v0.1 — what's in this spike (THIS commit)

Status: **DONE in spec form**. Repo skeleton + manifest + spec + mock server + tool stubs + tests + positioning. No live Hyper-V calls. Not on PyPI.

Deliverables:
- `README.md` — outward-facing pitch
- `LICENSE` — MIT
- `mcp.json` — MCP server manifest with 5 tool schemas
- `spec.md` — API contract (this is the canonical reference)
- `server.py` — MCP server stub (stdio transport, mock backend)
- `tools/*.ps1` — 5 PowerShell wrappers (boundary defined, mock JSON for v0.1)
- `tests/mock_server_test.py` — 3 e2e tests against the mock backend
- `positioning.md` — competitive landscape
- `release_roadmap.md` — this file

What v0.1 is **not**:
- Not callable against real Hyper-V (returns canned data)
- Not on PyPI / not on npm / not on Anthropic MCP registry
- Not signed
- Has not been tested against `claude.exe` end-to-end

## v0.2 — real Hyper-V wiring (2 weeks, ~16-20hr)

| Task | Estimate |
|---|---|
| Replace mock backend with `subprocess.run(["pwsh", "-File", "tools/<x>.ps1", ...])` invocations + JSON parse | 3hr |
| Real PS wrappers (replace mock JSON emission with `Get-VM | ConvertTo-Json`) for all 5 tools | 4hr |
| Live host integration tests (`tests/live_host_test.py`, requires Hyper-V role) | 4hr |
| Error-mode coverage: `vm_not_found`, `vm_busy`, `permission_denied`, `hyperv_unavailable` paths | 3hr |
| PyPI packaging (`pyproject.toml`, GitHub Action for publish) | 2hr |
| Doc update + example Claude Code session capture | 2hr |
| Buffer | 2hr |

**Exit criteria**: live test suite passes on a fresh Hyper-V Server 2025 host with one demo VM; `pip install hyperv-mcp` works.

## v0.3 — push notifications + HTTP transport (3 weeks)

| Task | Estimate |
|---|---|
| Streamable HTTP transport (per MCP 2026-03-05 AAIF priority #1) | 6hr |
| `.well-known/mcp.json` Server Card endpoint | 2hr |
| VM state-change watcher (WMI event subscription → MCP notification) | 8hr |
| `wait_for_vm_state` tool (long-poll companion) | 3hr |
| Tests for notification delivery + reconnect | 4hr |

**Exit criteria**: agent receives `vm_state_changed` notification within 2s of `Start-VM`; HTTP test passes against `hyperv-mcp` running on remote box.

## v1.0 — GPU + production hardening (6-8 weeks)

| Task | Estimate |
|---|---|
| `attach_gpu_partition` / `detach_gpu_partition` tools (calls `Add/Remove-VMGpuPartitionAdapter`) | 12hr |
| SR-IOV tool group (4 tools: list adapters / assign / unassign / status) | 10hr |
| Structured logging (OTel GenAI semantic conventions, per `project_0516_evolution_master_2026-05-16` G5) | 6hr |
| Hardened input validation (timeout enforcement, name sanitization for cmdlet injection) | 4hr |
| Multi-host abstraction (`-ComputerName` plumbing through every tool) | 8hr |
| Anthropic MCP registry submission + listing review | 4hr |
| Doc site (mkdocs material) | 6hr |

**Exit criteria**: Listed on Anthropic MCP registry. At least one external user reports successful GPU-PV attach via the tool. SemVer 1.0 commit (API stability promise).

## v1.1 — commercial features (open-core)

Pricing model TBD per `project_monetize_path_B_2026-05-10`. Plugin sits beside OSS core, separate license.

| Feature | Driver |
|---|---|
| Per-host RBAC | Enterprise audit requirement |
| Multi-host federation (one MCP server → N Hyper-V hosts) | Scale to fleet ops |
| SIEM audit-trail sink (Splunk / Elastic / generic webhook) | Compliance |
| Per-tenant vGPU partitioning | Studio / multi-customer hosting |
| SLA support | Enterprise procurement |

## Cross-references

- Strategy: `brain/monetization_0524/deep_res_mcp_2026.md` § C1 (this server is the C1 contribution)
- Moat thesis: `project_monetize_path_B_2026-05-10` (BAE P1 Windows + GPU + on-prem)
- Timing thesis: 9-15 month window before Win365 for Agents GA
- Adjacent integrations: `terraform-mcp` (declarative companion), `playwright-mcp` (Gumroad listing automation)
