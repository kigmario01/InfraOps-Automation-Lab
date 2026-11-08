#!/usr/bin/env python3
"""
InfraOps Automation Lab - Mission 10: Service Availability & Latency Checker
Module: python.monitoring.service_checker
Purpose: Performs HTTP/HTTPS health checks, latency tracking, and status verification.
Zero dependencies: Uses urllib.request from standard library, with fallback support.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


DEFAULT_ENDPOINTS = [
    {
        "name": "Local Nginx Web App",
        "url": "http://localhost:8080/healthz",
        "expected_code": 200,
        "timeout": 1.0,
        "max_latency_ms": 300,
    },
    {
        "name": "Local Uptime Kuma Status",
        "url": "http://localhost:3001",
        "expected_code": 200,
        "timeout": 1.0,
        "max_latency_ms": 500,
    },
    {
        "name": "Prometheus Node Exporter",
        "url": "http://localhost:9100/metrics",
        "expected_code": 200,
        "timeout": 1.0,
        "max_latency_ms": 250,
    },
    {
        "name": "Public Connectivity Check (Cloudflare)",
        "url": "https://1.1.1.1",
        "expected_code": 200,
        "timeout": 2.0,
        "max_latency_ms": 600,
    },
]


def check_http_endpoint(
    name: str,
    url: str,
    expected_code: int = 200,
    timeout: float = 3.0,
    max_latency_ms: float = 500.0,
) -> Dict[str, Any]:
    """Tests a single HTTP/HTTPS endpoint and measures latency."""
    t_start = time.perf_counter()
    status_code: Optional[int] = None
    state = "DOWN"
    error_msg: Optional[str] = None

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "InfraOps-HealthChecker/1.0"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

            if status_code == expected_code:
                if latency_ms > max_latency_ms:
                    state = "DEGRADED"
                else:
                    state = "UP"
            else:
                state = "UNEXPECTED_STATUS"
    except urllib.error.HTTPError as e:
        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
        status_code = e.code
        if status_code == expected_code:
            state = "UP"
        else:
            state = "DOWN"
            error_msg = f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
        state = "DOWN"
        error_msg = str(e.reason)
    except Exception as e:
        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
        state = "DOWN"
        error_msg = str(e)

    return {
        "name": name,
        "url": url,
        "state": state,
        "http_code": status_code,
        "expected_code": expected_code,
        "latency_ms": latency_ms,
        "max_latency_ms": max_latency_ms,
        "error": error_msg,
        "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def check_all_services(endpoints: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Runs checks on all configured endpoints."""
    target_list = endpoints or DEFAULT_ENDPOINTS
    results = []
    down_count = 0
    degraded_count = 0
    up_count = 0

    for ep in target_list:
        res = check_http_endpoint(
            name=ep["name"],
            url=ep["url"],
            expected_code=ep.get("expected_code", 200),
            timeout=ep.get("timeout", 3.0),
            max_latency_ms=ep.get("max_latency_ms", 500.0),
        )
        results.append(res)
        if res["state"] == "UP":
            up_count += 1
        elif res["state"] == "DEGRADED":
            degraded_count += 1
        else:
            down_count += 1

    overall = "HEALTHY"
    if down_count > 0:
        overall = "CRITICAL"
    elif degraded_count > 0:
        overall = "DEGRADED"

    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "overall_status": overall,
        "total_services": len(results),
        "up": up_count,
        "degraded": degraded_count,
        "down": down_count,
        "endpoints": results,
    }


def load_endpoints_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Loads endpoints configuration from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "endpoints" in data:
            return data["endpoints"]
    return DEFAULT_ENDPOINTS


def main() -> None:
    parser = argparse.ArgumentParser(description="InfraOps Service Availability Checker")
    parser.add_argument("--config", help="Path to custom endpoints JSON config")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    endpoints = DEFAULT_ENDPOINTS
    if args.config and os.path.exists(args.config):
        endpoints = load_endpoints_from_file(args.config)

    summary = check_all_services(endpoints)

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("=" * 68)
        print(f" INFRAOPS SERVICE AVAILABILITY CHECK ({summary['overall_status']})")
        print(f" Summary: {summary['up']} UP | {summary['degraded']} DEGRADED | {summary['down']} DOWN")
        print("=" * 68)
        for ep in summary["endpoints"]:
            state = ep["state"]
            color_mark = "[+]" if state == "UP" else ("[!]" if state == "DEGRADED" else "[-]")
            lat = f"{ep['latency_ms']}ms" if ep["latency_ms"] is not None else "N/A"
            code = f"HTTP {ep['http_code']}" if ep['http_code'] else "NO RESPONSE"
            print(f"{color_mark} {ep['name']:<35} | {state:<8} | {lat:<8} | {code}")
            if ep["error"]:
                print(f"    Reason: {ep['error']}")
        print("=" * 68)

    # Return non-zero exit if any down service
    sys.exit(0 if summary["down"] == 0 else 1)


if __name__ == "__main__":
    main()
