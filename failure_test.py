#!/usr/bin/env python3
"""
Failure simulation suite for BARQ Academy assessment.
Tests stack resilience during backend container outage and recovery.
"""
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8080"

def log(check_name, status, details=""):
    mark = "PASS" if status else "FAIL"
    print(f"[{mark}] {check_name}" + (f": {details}" if details else ""))
    return status

def run_cmd(cmd):
    """Executes shell command silently."""
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode == 0

def send_request(endpoint="/health"):
    """Sends a request and returns tuple: (success_bool, status_code, instance_id)"""
    url = f"{BASE_URL}{endpoint}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            instance_id = data.get("instance_id") or resp.headers.get("X-Instance-ID")
            return True, resp.status, instance_id
    except urllib.error.HTTPError as e:
        return False, e.code, None
    except Exception:
        return False, 0, None

def main():
    print("=== BARQ Academy Failure Simulation Test ===")

    # 1. Baseline check: Ensure both backends are initially healthy
    print("\n1. Verifying baseline readiness...")
    initial_instances = set()
    for _ in range(6):
        ok, code, inst = send_request()
        if ok and inst:
            initial_instances.add(inst)
        time.sleep(0.2)

    if len(initial_instances) < 2:
        log("Baseline Check", False, f"Expected both app-01 and app-02, but saw: {initial_instances}")
        sys.exit(1)
    log("Baseline Check", True, f"Both instances active: {sorted(list(initial_instances))}")

    # 2. Simulate failure: Stop app-01
    print("\n2. Stopping container 'app-01'...")
    if not run_cmd("docker stop app-01"):
        log("Stop app-01", False, "Failed to execute 'docker stop app-01'")
        sys.exit(1)
    log("Stop app-01", True, "Container app-01 stopped successfully")

    # 3. Measure traffic and availability during outage
    print("\n3. Measuring traffic during outage (sending 10 requests)...")
    success_count = 0
    error_count = 0
    active_instances_during_fail = set()

    for _ in range(10):
        ok, code, inst = send_request()
        if ok and code == 200:
            success_count += 1
            if inst:
                active_instances_during_fail.add(inst)
        else:
            error_count += 1
        time.sleep(0.3)

    degraded_ok = (success_count == 10 and error_count == 0 and active_instances_during_fail == {"app-02"})
    log("High Availability During Failure", degraded_ok, 
        f"Success: {success_count}/10, Errors: {error_count}, Active Instances: {list(active_instances_during_fail)}")

    # 4. Recovery: Start app-01
    print("\n4. Restoring container 'app-01'...")
    if not run_cmd("docker start app-01"):
        log("Restore app-01", False, "Failed to execute 'docker start app-01'")
        sys.exit(1)
    
    # Bounded wait for app-01 to become ready again
    time.sleep(3)
    log("Restore app-01", True, "Container app-01 started successfully")

    # 5. Prove recovered backend serves requests again
    print("\n5. Verifying round-robin traffic after recovery...")
    recovered_instances = set()
    for _ in range(10):
        ok, code, inst = send_request()
        if ok and inst:
            recovered_instances.add(inst)
        time.sleep(0.3)

    recovery_ok = ("app-01" in recovered_instances and "app-02" in recovered_instances)
    log("Backend Recovery Traffic Check", recovery_ok, f"Traffic routed across: {sorted(list(recovered_instances))}")

    # Summary
    if degraded_ok and recovery_ok:
        print("\nAll failure and recovery tests PASSED successfully.")
        sys.exit(0)
    else:
        print("\nFailure simulation checks FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
