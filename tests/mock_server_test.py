"""hyperv-mcp v0.1 — mock backend e2e tests.

Three end-to-end scenarios. No Hyper-V role required; no `mcp` SDK required.
Imports server.py directly and exercises tool handlers as MCP would.

Run:
    python tests/mock_server_test.py
Exit code 0 = all pass; non-zero = first failure printed.
"""

from __future__ import annotations

import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import server  # noqa: E402


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------

_PASSED: list[str] = []
_FAILED: list[tuple[str, str]] = []


def case(name: str):
    def deco(fn):
        def _wrap():
            try:
                fn()
            except AssertionError as e:
                _FAILED.append((name, str(e)))
                traceback.print_exc()
            except Exception:
                _FAILED.append((name, traceback.format_exc()))
            else:
                _PASSED.append(name)
        _wrap.__name__ = fn.__name__
        return _wrap
    return deco


def assert_eq(expected, actual, msg: str = ""):
    if expected != actual:
        raise AssertionError(f"{msg}: expected {expected!r}, got {actual!r}")


def assert_true(condition, msg: str):
    if not condition:
        raise AssertionError(msg)


# ---------------------------------------------------------------------------
# Test 1 — list / start / verify state transition
# ---------------------------------------------------------------------------


@case("list_vms shows 3 mock VMs and start_vm flips LINC-02 to Running")
def test_list_and_start():
    listing = server.handle_list_vms({})
    assert_true(listing["ok"], "list_vms should succeed")
    assert_eq(3, listing["vm_count"], "mock should return 3 VMs")
    names = {vm["name"] for vm in listing["vms"]}
    assert_eq({"LINC-01", "LINC-02", "THUNDER-BASE"}, names, "vm names mismatch")

    off_vms = [vm for vm in listing["vms"] if vm["state"] == "Off"]
    assert_eq(1, len(off_vms), "should be 1 Off VM (LINC-02)")
    assert_eq("LINC-02", off_vms[0]["name"], "")

    start = server.handle_start_vm({"name": "LINC-02"})
    assert_true(start["ok"], "start_vm should succeed")
    assert_eq("Off", start["previous_state"], "previous_state mismatch")
    assert_eq("Running", start["current_state"], "current_state mismatch")

    relisting = server.handle_list_vms({"state_filter": "Running"})
    running_names = {vm["name"] for vm in relisting["vms"]}
    assert_true("LINC-02" in running_names, "LINC-02 should now be Running")

    # Restore for isolation between tests
    server.handle_stop_vm({"name": "LINC-02"})


# ---------------------------------------------------------------------------
# Test 2 — snapshot returns well-formed id + parent
# ---------------------------------------------------------------------------


@case("snapshot_vm returns uuid id + null parent on first checkpoint")
def test_snapshot():
    res = server.handle_snapshot_vm({"name": "LINC-01", "snapshot_name": "test-snap-01"})
    assert_true(res["ok"], "snapshot_vm should succeed")
    snap = res["snapshot"]
    assert_eq("test-snap-01", snap["name"], "snapshot_name mismatch")
    assert_true(snap["parent_id"] is None, "first snapshot should have null parent")
    assert_eq("Standard", snap["type"], "expected Standard type")

    import uuid
    try:
        uuid.UUID(snap["id"])
    except ValueError:
        raise AssertionError(f"snapshot id is not a valid uuid: {snap['id']!r}")

    # Non-existent VM should return vm_not_found
    err = server.handle_snapshot_vm({"name": "NO-SUCH-VM"})
    assert_true(not err["ok"], "non-existent VM should fail")
    assert_eq("vm_not_found", err["error"]["code"], "expected vm_not_found code")


# ---------------------------------------------------------------------------
# Test 3 — error paths: bad args, mutual exclusion, unknown tool
# ---------------------------------------------------------------------------


@case("error model: missing name, mutual exclusion, idempotent stop_vm")
def test_error_paths():
    missing = server.handle_start_vm({})
    assert_true(not missing["ok"], "missing name should fail")
    assert_eq("invalid_arg", missing["error"]["code"], "")

    conflict = server.handle_stop_vm({"name": "LINC-01", "force": True, "save": True})
    assert_true(not conflict["ok"], "force+save should fail")
    assert_eq("invalid_arg", conflict["error"]["code"], "")

    # Idempotent stop: LINC-02 is Off (after test 1 cleanup)
    idem = server.handle_stop_vm({"name": "LINC-02"})
    assert_true(idem["ok"], "stop on already-Off should be ok:true")
    assert_true("note" in idem, "should annotate the no-op with note")

    metrics = server.handle_get_vm_metrics({})
    assert_true(metrics["ok"], "host-aggregate metrics should succeed without name")
    assert_true("vm_count_total" in metrics, "host aggregate missing vm_count_total")

    # All five tools must be registered
    assert_eq(
        {"list_vms", "start_vm", "stop_vm", "snapshot_vm", "get_vm_metrics"},
        set(server.TOOL_HANDLERS.keys()),
        "TOOL_HANDLERS registry mismatch",
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    tests = [test_list_and_start, test_snapshot, test_error_paths]
    for t in tests:
        t()

    print()
    print(f"PASSED: {len(_PASSED)} / {len(tests)}")
    for name in _PASSED:
        print(f"  [ok] {name}")
    if _FAILED:
        print(f"FAILED: {len(_FAILED)}")
        for name, msg in _FAILED:
            print(f"  [FAIL] {name}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
