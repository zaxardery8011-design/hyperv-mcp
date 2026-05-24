# hyperv-mcp

> **Agentic control plane for Microsoft Hyper-V via the Model Context Protocol.**
> First-mover MCP server for Windows on-prem VM lifecycle — fills the largest gap in the 2026 Q1-Q2 MCP server ecosystem.

[![CI](https://github.com/zaxardery8011-design/hyperv-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/zaxardery8011-design/hyperv-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![status: spec / PoC](https://img.shields.io/badge/status-spec%20%2F%20PoC-orange)](release_roadmap.md)
[![MCP: 2026-03-05](https://img.shields.io/badge/MCP-2026--03--05-blue)](https://modelcontextprotocol.io/specification)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D4)](README.md)

## Why this exists

The 2026 MCP server inventory (Top 20 + bonus, per `brain/monetization_0524/deep_res_mcp_2026.md`) has **zero coverage for Hyper-V / Windows VM lifecycle**. Container-side (Kubernetes / Portainer) and cloud-side (AWS / Cloudflare / Azure) both skip Windows on-prem. Enterprises with regulatory on-prem mandates (finance / government / healthcare) and small studios running GPU-passthrough workloads (gaming bots, 3D / render farms, ML inference) have no agentic control plane.

`hyperv-mcp` is the open-core MCP server that closes that gap.

## Who is this for

| Persona | Use case |
|---|---|
| **Enterprise DevOps on Windows** | Let Claude / Cursor / Codex spin VMs, take checkpoints before patch windows, roll back on failure. |
| **AI agent operators with on-prem GPU** | Bot fleets needing per-VM GPU-PV attach (game bots, distributed render, local LLM inference). |
| **Security researchers / malware analysts** | Snapshot → detonate → revert workflow exposed as MCP tools. |
| **Homelab tinkerers** | One MCP server replaces three PS scripts and a wiki page. |

## Quick start

**60 seconds. Mock backend, no admin, no Hyper-V role.**

```powershell
git clone https://github.com/zaxardery8011-design/hyperv-mcp.git
cd hyperv-mcp

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install mcp

# Sanity check — should print "PASSED: 3 / 3"
python tests\mock_server_test.py

# Start the MCP server in mock mode
$env:HYPERV_MCP_MODE = "mock"
python server.py
```

Register the server with Claude Code (`~/.claude.json`, under `mcpServers`):

```json
{
  "mcpServers": {
    "hyperv": {
      "command": "python",
      "args": ["C:\\path\\to\\hyperv-mcp\\server.py"],
      "env": { "HYPERV_MCP_MODE": "mock" }
    }
  }
}
```

Restart Claude Code. Then ask:

> *list my Hyper-V VMs and snapshot any whose name starts with `LINC-`*

You should see Claude call `list_vms` followed by `snapshot_vm` against `LINC-01` and `LINC-02`. The mock backend returns three pre-baked VMs — `LINC-01`, `LINC-02`, `THUNDER-BASE` — so you can verify the contract before touching real Hyper-V.

To go live (v0.2+, real `Get-VM` calls), set `HYPERV_MCP_MODE=live` once the host has the Hyper-V role and your account is in `Hyper-V Administrators`.

## Tools

| Tool | Purpose | Underlying cmdlet (v0.2) |
|---|---|---|
| `list_vms` | Enumerate VMs with state + uptime + memory | `Get-VM` |
| `start_vm` | Boot a VM (optional heartbeat wait) | `Start-VM` |
| `stop_vm` | Graceful shutdown / force / save-state | `Stop-VM` |
| `snapshot_vm` | Create checkpoint | `Checkpoint-VM` |
| `get_vm_metrics` | CPU / memory / disk / network counters | `Measure-VM` / `Get-VMNetworkAdapter` |

Full schema: see [`mcp.json`](mcp.json). Behavior contract: see [`spec.md`](spec.md).

## Comparison to alternatives

See [`positioning.md`](positioning.md). TL;DR:

| Tool | Hyper-V native | Agentic / MCP | On-prem | GPU passthrough aware |
|---|---|---|---|---|
| **hyperv-mcp** | ✅ | ✅ | ✅ | ✅ (planned v1.0) |
| vagrant | partial | ❌ | ✅ | ❌ |
| packer | image build only | ❌ | ✅ | ❌ |
| multipass | Ubuntu-only | ❌ | ✅ | ❌ |
| azure-mcp | ❌ (Azure VM) | ✅ | ❌ | n/a |
| terraform-mcp + hyperv provider | ✅ via TF | ✅ | ✅ | partial |

The closest comparable is `terraform-mcp + community Hyper-V provider`, but TF flow is declarative IaC — `hyperv-mcp` is **imperative agentic actions** (snapshot before risky op, start a VM on demand, query live metrics). Different shape.

## Roadmap

| Milestone | Scope | ETA |
|---|---|---|
| **v0.1 (this)** | Spec + scaffold + mock server + 5 tool stubs + tests | 2026-05-24 |
| **v0.2** | Wire real Hyper-V cmdlets, integration tests on live host | 2026-06 |
| **v0.3** | Live VM events (state-change push) via MCP notifications | 2026-07 |
| **v1.0** | GPU-PV attach/detach + SR-IOV + remote-FX legacy, production hardening | 2026-Q3 |
| **v1.1 (commercial)** | Per-host RBAC, multi-host federation, audit-trail sink, vGPU partitioning | TBD |

See [`release_roadmap.md`](release_roadmap.md) for detail.

## Project status

**Spec / PoC.** v0.1 ships mock JSON responses so the contract can be verified without admin rights or Hyper-V role installed. The PowerShell wrappers under `tools/` define the cmdlet boundary that v0.2 will call.

Not on PyPI yet. Not signed. Not on the Anthropic MCP registry. v0.2 ships these.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for dev setup, PR flow, and the "add a new tool" pattern. Release history is in [`CHANGELOG.md`](CHANGELOG.md).

Maintainer focus areas:

- v0.2 cmdlet integration (need testers with Hyper-V role + Server / Pro / Enterprise SKU)
- GPU-PV attach test harness (need GPU-PV capable hardware — RTX 3060+ / Quadro)
- Tool schema feedback (does `wait_for_heartbeat` belong on `start_vm` or as a separate `wait_for_vm` tool?)

## License

MIT. See [`LICENSE`](LICENSE).

## References

- MCP spec: <https://modelcontextprotocol.io/specification>
- AIWFF deep research (server-side MCP ecosystem 2026 Q1-Q2): `brain/monetization_0524/deep_res_mcp_2026.md` (internal)
- Hyper-V PowerShell module: <https://learn.microsoft.com/powershell/module/hyper-v/>
