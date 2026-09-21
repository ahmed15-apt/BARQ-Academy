#!/usr/bin/env python3
"""
Bounded environment validation suite for BARQ Academy infrastructure assessment.
Tests endpoints, database/cache connectivity, load balancing, and exit codes for CI integration.
"""
import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8090"

def log(check_name, status, details=""):
    mark = "PASS" if status else "FAIL"
    print(f"[{mark}] {check_name}" + (f": {details}" if details else ""))
    return status

def check_endpoint(endpoint, expected_keys=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                return log(f"Endpoint {endpoint} HTTP Status", False, f"Expected 200, got {response.status}")
            
            data = json.loads(response.read().decode('utf-8'))
            if expected_keys:
                for key in expected_keys:
                    if key not in data:
                        return log(f"Endpoint {endpoint} Schema", False, f"Missing required key '{key}'")
            return log(f"Endpoint {endpoint}", True, f"Response: {data}")
    except Exception as e:
        return log(f"Endpoint {endpoint} Accessibility", False, str(e))

def check_counter():
    url = f"{BASE_URL}/counter"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as r1:
            d1 = json.loads(r1.read().decode('utf-8'))
            c1 = d1.get("counter", 0)
            
        with urllib.request.urlopen(req, timeout=5) as r2:
            d2 = json.loads(r2.read().decode('utf-8'))
            c2 = d2.get("counter", 0)
            
        if c2 > c1:
            return log("Redis Counter Endpoint /counter", True, f"Counter incremented successfully ({c1} -> {c2})")
        return log("Redis Counter Endpoint /counter", False, f"Counter failed to increment ({c1} -> {c2})")
    except Exception as e:
        return log("Redis Counter Endpoint /counter", False, str(e))

def check_load_balancing():
    url = f"{BASE_URL}/health"
    seen_instances = set()
    for _ in range(6):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                instance_id = response.headers.get("X-Instance-ID")
                if not instance_id:
                    data = json.loads(response.read().decode('utf-8'))
                    instance_id = data.get("instance_id") or data.get("instance")
                if instance_id:
                    seen_instances.add(instance_id)
        except Exception:
            pass

    if len(seen_instances) > 1:
        return log("Load Balancer Round-Robin", True, f"Traffic routed across backends: {sorted(list(seen_instances))}")
    return log("Load Balancer Round-Robin", False, f"Traffic pinned to single instance: {seen_instances}")

def main():
    print("=== BARQ Academy System Validation Suite ===")
    checks = [
        check_endpoint("/", ["message"]),
        check_endpoint("/health", ["status"]),
        check_endpoint("/ready", ["status"]),
        check_endpoint("/instance", ["instance_id"]),
        check_endpoint("/records", ["records"]),
        check_counter(),
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
