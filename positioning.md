# Positioning — hyperv-mcp vs adjacent tools

**Goal of this doc**: justify why `hyperv-mcp` is not a duplicate of any of the 13 obvious lookalikes, and surface the one real competitor (terraform-mcp + community Hyper-V provider) so we can articulate the imperative-vs-declarative split honestly.

## TL;DR

`hyperv-mcp` is the **only agentic / MCP-native imperative control plane for Windows on-prem Hyper-V VMs with GPU-passthrough awareness**. Five-attribute intersection has zero existing tool. Closest neighbor is `terraform-mcp + hyperv community provider` (declarative IaC, not imperative action); next nearest is `azure-mcp` (wrong cloud-vs-on-prem half).

## Five-attribute matrix

| Tool | Hyper-V native | Imperative agentic | MCP-native | On-prem | GPU-PV / vGPU aware |
|---|---|---|---|---|---|
| **hyperv-mcp** | ✅ | ✅ | ✅ | ✅ | ✅ (v1.0) |
| vagrant | partial via hyperv provider | ✅ (imperative CLI, no agent) | ❌ | ✅ | ❌ |
| packer | image build only | ❌ (build-then-handoff) | ❌ | ✅ | ❌ |
| multipass | Ubuntu only, uses Hyper-V on Win | ✅ | ❌ | ✅ | ❌ |
| azure-mcp | ❌ (Azure VM not Hyper-V) | ✅ | ✅ | ❌ | n/a |
| aws-labs/mcp | ❌ | ✅ | ✅ | ❌ | n/a |
| cloudflare-mcp | ❌ | ✅ | ✅ | ❌ | n/a |
| kubernetes-mcp | container not VM | ✅ | ✅ | ✅ | ❌ |
| terraform-mcp + community hyperv provider | ✅ | ❌ (declarative IaC) | ✅ | ✅ | partial |
| portainer | container only | ✅ | ❌ | ✅ | ❌ |
| MS System Center VMM | ✅ | partial (GUI-first) | ❌ | ✅ | ✅ |
| WAC (Windows Admin Center) | ✅ | partial (web GUI) | ❌ | ✅ | partial |
| Veeam | backup tool | ❌ | ❌ | ✅ | n/a |

Only `hyperv-mcp` hits all five.

## The honest competitor analysis

### 1. terraform-mcp + community Hyper-V provider — closest neighbor, different shape

Terraform's `taliesins/hyperv` provider exists. Wrapped in `terraform-mcp`, an agent can apply `.tf` files to spin VMs. So why not just use that?

- **TF is declarative**: "the world should look like this." Snapshot-before-risky-op, start-on-demand, query-live-metrics — these are *imperative actions*, awkward to express as `terraform apply` cycles.
- **TF state is heavy**: every action requires state file lock + plan + apply. Latency unacceptable for an agent doing 20 ops/min.
- **Plan/apply blocks streaming responses**: agent UX expects sub-second tool calls; `terraform apply` is 5-30s+.
- **GPU-PV not in the TF provider**: community Hyper-V provider doesn't expose `Add-VMGpuPartitionAdapter`. Would have to write a custom provider — at which point we're back to building hyperv-mcp anyway.

**Coexistence**: `hyperv-mcp` for imperative agent actions, `terraform-mcp` for declarative platform engineering. Different jobs, both legit.

### 2. azure-mcp / aws-mcp / cloudflare-mcp — wrong half of the market

Cloud-side MCP is well-served. Enterprises with on-prem mandates (data residency / air-gap / latency / cost) cannot use these. Top regulated verticals are exactly the ones running Hyper-V on-prem:

- **Finance**: trading desks, KYC platforms, regional bank cores.
- **Government / defense**: classified workloads, GovCloud-equivalent on-prem.
- **Healthcare**: HIPAA-driven on-prem isolation.
- **Telco**: edge compute at carrier sites.

`hyperv-mcp` does not compete with cloud MCP — it covers the half that cloud MCP cannot reach.

### 3. multipass / vagrant — predate MCP

Both are CLI tools meant for human operators. Neither speaks MCP. Wrapping them in MCP is possible but inherits their constraints (multipass = Ubuntu-only; vagrant = box-based, slow). hyperv-mcp targets the Hyper-V control plane directly via PowerShell module, avoiding both abstraction layers.

### 4. Microsoft official — SCVMM, WAC, Windows Admin Center

These exist but:
- GUI-first; CLI is afterthought.
- No MCP exposure (and unlikely soon — Microsoft is pushing Azure / Win365 instead, per `project_anthropic_managed_agents_signal_2026-05-16`).
- Enterprise licensing required for SCVMM.

A free, open-source, MCP-native alternative for Hyper-V Server (free SKU) is a real product gap.

## Defensibility analysis

Following the Boris four-axis framing from `project_monetize_path_B_2026-05-10`:

| Axis | hyperv-mcp standing |
|---|---|
| **Counter-positioning** | Strong: cloud-vendor MCP cannot do on-prem without killing their cloud thesis. Microsoft cannot push GPU-PV via Win365 (excluded). |
| **Switching cost** | Weak alone (agent re-targets easily). Strengthened by GPU-PV plugin lock-in + audit-trail accumulation. |
| **Unique data / process** | AIWFF brings unique fleet operations knowledge (`thunder-vm-dev`, Lollipop 9-fleet) — encodes hard-won knobs (SR-IOV, MAC spoofing, integration services edge cases) other authors won't know. |
| **Cross-provider cost arbitrage** | n/a (this isn't an LLM, it's a control plane) |

**Verdict**: counter-positioning + unique operational knowledge are the two real moats. Switching cost is weak in v0.1; build it via v1.0 GPU-PV plugin + v1.1 audit-trail sink.

## Strategic timing

Per `project_monetize_path_B_2026-05-10`, **the 9-15 month window before Win365 for Agents goes GA with broader region / SKU coverage is the time to plant standards**. Standards in MCP ecosystem = first server with non-trivial usage to define tool names. After GA, Microsoft's distribution will compress space for alternatives.

Action: **ship v0.2 by end of 2026-06**, get it on the Anthropic MCP registry, target 100 GitHub stars by Q3.

## Open-core monetization angle

Pairs with the project monetization line in `project_monetize_path_B_2026-05-10`:

- **Free OSS core**: 5 tools + Hyper-V Server SKU support.
- **Commercial plugin** (v1.1+): GPU-PV vGPU partitioning, multi-host federation, RBAC + audit-trail sink (SIEM integration), SLA support.
- **Target buyer**: small studios with 5-50 GPU-passthrough VMs (LLM fleets, render farms, game-bot operations) — the AIWFF / Lollipop persona scaled up.

## Risks

- **Microsoft ships an official hyperv-mcp first**: possible but unlikely (they're pushing Azure / Win365). Mitigation: ship + community-anchor before they decide.
- **AAIF maintainer-track gets crowded**: getting into the Anthropic-connector directory may slow over time. Mitigation: register early.
- **Hyper-V itself declines as a platform**: low probability in the next 3 years; Windows Server / Hyper-V Server remains a primary on-prem virtualization platform for the named verticals.
