#!/usr/bin/env python3
"""Bounded environment validation suite for BARQ Academy infrastructure assessment."""
import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8080"

def log(check_name, status, details=""):
    mark = "PASS" if status else "FAIL"
    print(f"[{mark}] {check_name}" + (f": {details}" if details else ""))
    return status

def check_health():
    url = f"{BASE_URL}/health"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                return log("Health Endpoint HTTP Status", False, f"Expected 200, got {response.status}")
            data = json.loads(response.read().decode('utf-8'))
            if data.get("status") == "alive":
                return log("Health Endpoint Functional", True, f"Status 'alive' from {data.get('instance_id')}")
            return log("Health Endpoint Payload", False, f"Unexpected payload: {data}")
    except Exception as e:
        return log("Health Endpoint Accessibility", False, str(e))

def check_records():
    url = f"{BASE_URL}/records"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                return log("Records Endpoint HTTP Status", False, f"Expected 200, got {response.status}")
            data = json.loads(response.read().decode('utf-8'))
            records = data.get("records", [])
            if isinstance(records, list) and len(records) > 0:
                return log("Database Query Connectivity", True, f"Retrieved {len(records)} records via {data.get('instance_id')}")
            return log("Database Records Integrity", False, f"No records returned: {data}")
    except Exception as e:
        return log("Database Endpoint Accessibility", False, str(e))

def check_load_balancing():
    url = f"{BASE_URL}/health"
    seen_instances = set()
    attempts = 6
    for _ in range(attempts):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                instance_id = response.headers.get("X-Instance-ID")
                if not instance_id:
                    data = json.loads(response.read().decode('utf-8'))
                    instance_id = data.get("instance_id")
                if instance_id:
                    seen_instances.add(instance_id)
        except Exception:
            pass

    if len(seen_instances) > 1:
        return log("Load Balancer Round-Robin", True, f"Traffic routed across instances: {sorted(list(seen_instances))}")
    return log("Load Balancer Round-Robin", False, f"Traffic pinned to single instance: {seen_instances}")

def main():
    print("=== BARQ Academy System Validation Suite ===")
    checks = [
        check_health(),
        check_records(),
        check_load_balancing()
    ]
    
    if all(checks):
        print("\nAll validation checks PASSED successfully.")
        sys.exit(0)
    else:
        print("\nOne or more validation checks FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
