"""hyperv-mcp v0.1 — MCP server scaffold.

Stdio transport, mock backend. v0.2 replaces _mock_* with subprocess calls to
tools/*.ps1. The tool handler signatures and JSON contract are fixed by spec.md;
swap the backend without changing them.

Run:
    python server.py            # starts stdio MCP server in mock mode
    HYPERV_MCP_MODE=live python server.py  # v0.2+, no-op today

Test (without MCP SDK):
    python -c "import server, json; print(json.dumps(server.handle_list_vms({}), indent=2))"
"""

from __future__ import annotations

import os
import json
import datetime
import uuid
from typing import Any, Callable

MODE = os.environ.get("HYPERV_MCP_MODE", "mock").lower()
SERVER_NAME = "hyperv-mcp"
SERVER_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------

_MOCK_VMS: list[dict[str, Any]] = [
    {
        "name": "LINC-01",
        "id": "8c5a4f12-1ab2-4cde-90f1-0123456789ab",
        "state": "Running",
        "cpu_usage_pct": 12,
        "memory_assigned_mb": 4096,
        "uptime_sec": 3680,
        "version": "10.0",
        "generation": 2,
        "notes": "",
    },
    {
        "name": "LINC-02",
        "id": "9b6e5f23-2cd3-5def-a012-1234567890bc",
        "state": "Off",
        "cpu_usage_pct": 0,
        "memory_assigned_mb": 0,
        "uptime_sec": 0,
        "version": "10.0",
        "generation": 2,
        "notes": "",
    },
    {
        "name": "THUNDER-BASE",
        "id": "ac7f6034-3de4-6ef0-b123-2345678901cd",
        "state": "Saved",
        "cpu_usage_pct": 0,
        "memory_assigned_mb": 8192,
        "uptime_sec": 0,
        "version": "10.0",
        "generation": 2,
        "notes": "thunder v2.0 base image",
    },
]


def _now_iso() -> str:
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz).isoformat(timespec="seconds")


def _find_vm(name: str) -> dict[str, Any] | None:
    return next((vm for vm in _MOCK_VMS if vm["name"] == name), None)


def _fnmatch_like(value: str, pattern: str) -> bool:
    """Minimal PowerShell -Like wildcard (`*`, `?`). Sufficient for v0.1 mock."""
    import fnmatch
    return fnmatch.fnmatchcase(value, pattern)


# ---------------------------------------------------------------------------
# Tool handlers — contract is the source of truth in spec.md
# ---------------------------------------------------------------------------


def handle_list_vms(args: dict[str, Any]) -> dict[str, Any]:
    state_filter = args.get("state_filter", "any")
    name_pattern = args.get("name_pattern")

    vms = list(_MOCK_VMS)
    if state_filter != "any":
        vms = [v for v in vms if v["state"] == state_filter]
    if name_pattern:
        vms = [v for v in vms if _fnmatch_like(v["name"], name_pattern)]

    return {
        "ok": True,
        "host": os.environ.get("COMPUTERNAME", "MOCK-HOST"),
        "captured_at": _now_iso(),
        "vm_count": len(vms),
        "vms": vms,
    }


def handle_start_vm(args: dict[str, Any]) -> dict[str, Any]:
    name = args.get("name")
    if not name:
        return _err("invalid_arg", "name is required")

    vm = _find_vm(name)
    if vm is None:
        return _err("vm_not_found", f"No VM named {name!r}")

    previous = vm["state"]
    if previous == "Running":
        return {
            "ok": True,
            "name": name,
            "previous_state": previous,
            "current_state": "Running",
            "note": "already Running, no action taken",
        }

    vm["state"] = "Running"
    vm["uptime_sec"] = 1
    return {
        "ok": True,
        "name": name,
        "previous_state": previous,
        "current_state": "Running",
        "heartbeat_received": bool(args.get("wait_for_heartbeat", False)),
        "elapsed_sec": 0.0 if MODE == "mock" else None,
    }


def handle_stop_vm(args: dict[str, Any]) -> dict[str, Any]:
    name = args.get("name")
    if not name:
        return _err("invalid_arg", "name is required")
    force = bool(args.get("force", False))
    save = bool(args.get("save", False))
    if force and save:
        return _err("invalid_arg", "force and save are mutually exclusive")

    vm = _find_vm(name)
    if vm is None:
        return _err("vm_not_found", f"No VM named {name!r}")

    previous = vm["state"]
    new_state = "Saved" if save else "Off"
    if previous == new_state:
        return {
            "ok": True,
            "name": name,
            "previous_state": previous,
            "current_state": new_state,
            "note": f"already {new_state}, no action taken",
        }

    mode = "saved" if save else ("force" if force else "graceful")
    vm["state"] = new_state
    vm["uptime_sec"] = 0
    vm["cpu_usage_pct"] = 0
    return {
        "ok": True,
        "name": name,
        "previous_state": previous,
        "current_state": new_state,
        "mode": mode,
        "elapsed_sec": 0.0,
    }


def handle_snapshot_vm(args: dict[str, Any]) -> dict[str, Any]:
    name = args.get("name")
    if not name:
        return _err("invalid_arg", "name is required")
    vm = _find_vm(name)
    if vm is None:
        return _err("vm_not_found", f"No VM named {name!r}")

    snapshot_name = args.get("snapshot_name") or _now_iso()
    return {
        "ok": True,
        "name": name,
        "snapshot": {
            "id": str(uuid.uuid4()),
            "name": snapshot_name,
            "parent_id": None,
            "created_at": _now_iso(),
            "type": "Standard",
        },
    }


def handle_get_vm_metrics(args: dict[str, Any]) -> dict[str, Any]:
    name = args.get("name")
    include = args.get("include") or ["cpu", "memory"]

    if not name:
        running = [v for v in _MOCK_VMS if v["state"] == "Running"]
        return {
            "ok": True,
            "host": os.environ.get("COMPUTERNAME", "MOCK-HOST"),
            "captured_at": _now_iso(),
            "vm_count_running": len(running),
            "vm_count_total": len(_MOCK_VMS),
            "cpu": {"logical_processors": 16, "total_usage_pct": 24},
            "memory": {
                "total_mb": 65536,
                "assigned_to_vms_mb": sum(v["memory_assigned_mb"] for v in running),
                "free_mb": 38400,
            },
        }

    vm = _find_vm(name)
    if vm is None:
        return _err("vm_not_found", f"No VM named {name!r}")

    out: dict[str, Any] = {
        "ok": True,
        "name": name,
        "captured_at": _now_iso(),
    }
    if "cpu" in include:
        out["cpu"] = {"usage_pct": vm["cpu_usage_pct"], "vcpu_count": 4}
    if "memory" in include:
        out["memory"] = {
            "assigned_mb": vm["memory_assigned_mb"],
            "demand_mb": int(vm["memory_assigned_mb"] * 0.6),
            "available_mb": int(vm["memory_assigned_mb"] * 0.4),
        }
    if "disk" in include:
        out["disk"] = [{"path": f"C:\\\\Hyper-V\\\\{name}\\\\disk.vhdx", "size_gb": 60, "used_gb": 22}]
    if "network" in include:
        out["network"] = [{"adapter": "Default Switch", "tx_bps": 124000, "rx_bps": 89000}]
    return out


def _err(code: str, message: str, **extra: Any) -> dict[str, Any]:
    body = {"ok": False, "error": {"code": code, "message": message}}
    if extra:
        body["error"].update(extra)
    return body


# ---------------------------------------------------------------------------
# Registry — used by the MCP runtime and by tests
# ---------------------------------------------------------------------------

TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "list_vms": handle_list_vms,
    "start_vm": handle_start_vm,
    "stop_vm": handle_stop_vm,
    "snapshot_vm": handle_snapshot_vm,
    "get_vm_metrics": handle_get_vm_metrics,
}


# ---------------------------------------------------------------------------
# MCP server entry — uses official `mcp` SDK if installed; otherwise prints
# a structured banner so the scaffold still validates without dependencies.
# ---------------------------------------------------------------------------

def _load_manifest() -> dict[str, Any]:
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "mcp.json"), encoding="utf-8") as f:
        return json.load(f)


def _run_with_mcp_sdk() -> None:
    """Wire handlers to the official `mcp` SDK over stdio."""
    from mcp.server import Server  # type: ignore
    from mcp.server.stdio import stdio_server  # type: ignore
    from mcp import types  # type: ignore

    manifest = _load_manifest()
    server: Server = Server(SERVER_NAME)

    @server.list_tools()  # type: ignore[misc]
    async def _list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"],
            )
            for t in manifest["tools"]
        ]

    @server.call_tool()  # type: ignore[misc]
    async def _call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            payload = _err("invalid_arg", f"unknown tool {name!r}")
        else:
            payload = handler(arguments or {})
        return [types.TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

    import asyncio

    async def _main() -> None:
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(_main())


def main() -> int:
    if MODE not in ("mock", "live"):
        print(f"[hyperv-mcp] ERROR: HYPERV_MCP_MODE must be mock|live, got {MODE!r}")
        return 2
    if MODE == "live":
        print(f"[hyperv-mcp] WARNING: live mode is not implemented in v0.1; falling back to mock")

    try:
        _run_with_mcp_sdk()
        return 0
    except ImportError:
        print(
            f"[hyperv-mcp] {SERVER_NAME} v{SERVER_VERSION} scaffold ready (mode={MODE}).\n"
            f"            `mcp` SDK not installed — install with `pip install mcp` to run as MCP server.\n"
            f"            Tool handlers are importable: list_vms, start_vm, stop_vm, snapshot_vm, get_vm_metrics.",
            flush=True,
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
