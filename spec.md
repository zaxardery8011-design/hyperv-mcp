# hyperv-mcp — API Spec v0.1

**Status**: Draft / PoC. Mock implementation in `server.py` returns canned responses; v0.2 will replace mock backend with real Hyper-V cmdlet invocations.

**MCP version targeted**: 2026-03-05 (AAIF roadmap), Streamable HTTP + stdio transports.

**Transport (v0.1)**: stdio only. v0.2 adds Streamable HTTP per AAIF Q2 priority #1.

## Conventions

- **Error model**: Tools return JSON-RPC errors via the MCP error envelope. Domain failures (VM not found, etc.) return a successful tool call with `{ "ok": false, "error": { "code": "...", "message": "..." } }` so the LLM can reason about partial failure without trapping protocol-level exceptions.
- **Naming**: VM names use the host's display name (`Get-VM -Name`), not the GUID. GUID lookups added in v0.2 as `vm_id` alternate.
- **Timestamps**: ISO-8601 with timezone offset (`+08:00`), not Z. PowerShell `Get-Date -Format "o"` output.
- **Mode flag**: `HYPERV_MCP_MODE=mock|live` env var. v0.1 forces mock; v0.2 accepts both; v1.0 defaults to live with `--mock` flag for CI.

## Error codes (canonical)

| code | meaning |
|---|---|
| `vm_not_found` | No VM with given name on this host |
| `vm_already_in_state` | start_vm on Running, stop_vm on Off (returns ok:true with note) |
| `vm_busy` | Operation pending (snapshot in progress, migration, etc.) |
| `hyperv_unavailable` | Hyper-V role not installed or service stopped |
| `permission_denied` | Caller is not in Hyper-V Administrators |
| `timeout` | wait_for_heartbeat exceeded timeout_sec |
| `invalid_arg` | Schema validation failed at server side |
| `internal` | Unexpected cmdlet failure (stderr captured in `error.detail`) |

---

## Tool 1: `list_vms`

**Purpose**: Enumerate all VMs on the host, optionally filtered by state or name pattern.

### Input

```json
{
  "state_filter": "any | Running | Off | Saved | Paused",
  "name_pattern": "LINC-*"
}
```

Both fields optional. Defaults: `state_filter="any"`, no name filter.

### Output (success)

```json
{
  "ok": true,
  "host": "DESKTOP-W10",
  "captured_at": "2026-05-24T13:05:12+08:00",
  "vm_count": 3,
  "vms": [
    {
      "name": "LINC-01",
      "id": "8c5a4f12-1ab2-4cde-90f1-0123456789ab",
      "state": "Running",
      "cpu_usage_pct": 12,
      "memory_assigned_mb": 4096,
      "uptime_sec": 3680,
      "version": "10.0",
      "generation": 2,
      "notes": ""
    }
  ]
}
```

### Mock behavior (v0.1)

Returns 3 fake VMs: `LINC-01` (Running), `LINC-02` (Off), `THUNDER-BASE` (Saved). Filter logic implemented client-side so schema can be tested.

### Backing cmdlet (v0.2)

```powershell
Get-VM | Where-Object { ($State -eq 'any' -or $_.State -eq $State) -and $_.Name -like $Pattern } |
  Select-Object Name,Id,State,CPUUsage,MemoryAssigned,Uptime,Version,Generation,Notes
```

---

## Tool 2: `start_vm`

**Purpose**: Boot a VM. Idempotent for already-Running state.

### Input

```json
{
  "name": "LINC-01",
  "wait_for_heartbeat": true,
  "timeout_sec": 90
}
```

### Output (success)

```json
{
  "ok": true,
  "name": "LINC-01",
  "previous_state": "Off",
  "current_state": "Running",
  "heartbeat_received": true,
  "elapsed_sec": 14.2
}
```

### Output (idempotent no-op)

```json
{
  "ok": true,
  "name": "LINC-01",
  "previous_state": "Running",
  "current_state": "Running",
  "note": "already Running, no action taken"
}
```

### Backing cmdlet (v0.2)

```powershell
Start-VM -Name $Name -ErrorAction Stop
if ($WaitHeartbeat) {
  Wait-VM -Name $Name -For Heartbeat -Timeout $Timeout
}
```

---

## Tool 3: `stop_vm`

**Purpose**: Stop a VM. Three modes: graceful (default), force (power-off), save (suspend to disk).

### Input

```json
{
  "name": "LINC-01",
  "force": false,
  "save": false
}
```

Validation: `force` and `save` are mutually exclusive. Both false = graceful.

### Output

```json
{
  "ok": true,
  "name": "LINC-01",
  "previous_state": "Running",
  "current_state": "Off",
  "mode": "graceful",
  "elapsed_sec": 5.1
}
```

### Backing cmdlet (v0.2)

```powershell
if     ($Save)  { Save-VM  -Name $Name }
elseif ($Force) { Stop-VM  -Name $Name -TurnOff }
else            { Stop-VM  -Name $Name }
```

---

## Tool 4: `snapshot_vm`

**Purpose**: Create a checkpoint of a VM. Returns checkpoint id + parent.

### Input

```json
{
  "name": "LINC-01",
  "snapshot_name": "before-patch-2026-05-24"
}
```

Default `snapshot_name`: ISO-8601 timestamp (`2026-05-24T13:10:00+08:00`).

### Output

```json
{
  "ok": true,
  "name": "LINC-01",
  "snapshot": {
    "id": "ab12cd34-5678-90ef-1234-567890abcdef",
    "name": "before-patch-2026-05-24",
    "parent_id": null,
    "created_at": "2026-05-24T13:10:02+08:00",
    "type": "Standard"
  }
}
```

### Backing cmdlet (v0.2)

```powershell
Checkpoint-VM -Name $Name -SnapshotName $SnapshotName -PassThru |
  Select-Object Id,Name,ParentSnapshotId,CreationTime,SnapshotType
```

---

## Tool 5: `get_vm_metrics`

**Purpose**: Return current resource counters. Two modes: per-VM (with `name`) and host aggregate (no `name`).

### Input

```json
{
  "name": "LINC-01",
  "include": ["cpu", "memory", "network"]
}
```

### Output (per-VM)

```json
{
  "ok": true,
  "name": "LINC-01",
  "captured_at": "2026-05-24T13:11:00+08:00",
  "cpu": { "usage_pct": 12, "vcpu_count": 4 },
  "memory": { "assigned_mb": 4096, "demand_mb": 2410, "available_mb": 1686 },
  "network": [
    { "adapter": "Default Switch", "tx_bps": 124000, "rx_bps": 89000 }
  ]
}
```

### Output (host aggregate)

```json
{
  "ok": true,
  "host": "DESKTOP-W10",
  "captured_at": "2026-05-24T13:11:00+08:00",
  "vm_count_running": 2,
  "vm_count_total": 3,
  "cpu": { "logical_processors": 16, "total_usage_pct": 24 },
  "memory": { "total_mb": 65536, "assigned_to_vms_mb": 8192, "free_mb": 38400 }
}
```

### Backing cmdlets (v0.2)

```powershell
# Per-VM
Measure-VM -Name $Name  # requires Enable-VMResourceMetering pre-run
Get-VM -Name $Name | Select-Object CPUUsage,MemoryAssigned,MemoryDemand
Get-VMNetworkAdapter -VMName $Name | Select-Object SwitchName,*Bytes*

# Host
Get-Counter '\Hyper-V Hypervisor Logical Processor(*)\% Total Run Time'
Get-VMHost | Select-Object MemoryCapacity
```

---

## Out of scope for v0.1

- Live migration / shared cluster control (deferred to v1.0)
- VHD/VHDX disk operations (`New-VHD`, `Resize-VHD`) — separate tool group in v0.3
- Virtual switch management (`New-VMSwitch`) — admin-heavy, deferred to v1.0
- GPU-PV attach/detach (`Add-VMGpuPartitionAdapter`) — v1.0 commercial plugin
- Hyper-V replica setup — out of scope (use System Center / vendor tools)

## Open questions (to resolve before v0.2)

1. **Authorization model**: today caller's Windows token is authoritative. Do we need MCP-level scopes (read-only vs admin) on top? — Lean: yes, env var `HYPERV_MCP_READONLY=1`.
2. **Heartbeat semantics**: `Wait-VM -For Heartbeat` requires integration services. Does `wait_for_heartbeat` fall back to `-For IPAddress` if heartbeat unavailable? — Lean: yes, with `wait_strategy` field.
3. **Snapshot chain limits**: Hyper-V supports nested checkpoints up to 50; do we enforce a max in MCP to prevent agent runaway? — Lean: configurable cap, default 10.
4. **Multi-host**: v0.1 is single-host. v0.2 stays single. v1.0 plans `-ComputerName` parameter — affects every tool's schema. — Defer concrete schema decision.

## Compliance with MCP 2026-03-05

| AAIF priority | Status in v0.1 |
|---|---|
| Streamable HTTP + stateless | ❌ stdio only — v0.2 |
| Server Cards (`.well-known`) | ❌ — v0.2 |
| Tool Search / Programmatic Tool Calling | ✅ tool list small enough to inline; PTC compatible (deterministic schema) |
| Enterprise audit trail | ❌ — v1.1 commercial |
