#!/usr/bin/env python3
"""
InfraOps Automation Lab - Mission 9: System Diagnostics Engine
Module: python.diagnostics.sys_diagnostics
Purpose: Collects and analyzes CPU, memory, disk, network, and process health metrics.
Compatibility: Linux, macOS, and Windows. Fallback to stdlib if psutil is not installed.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

try:
    import psutil  # type: ignore
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def get_uptime_seconds() -> float:
    """Returns system uptime in seconds."""
    if HAS_PSUTIL:
        return time.time() - psutil.boot_time()
    if os.path.exists("/proc/uptime"):
        try:
            with open("/proc/uptime", "r") as f:
                return float(f.readline().split()[0])
        except Exception:
            pass
    return 0.0


def format_duration(seconds: float) -> str:
    """Format seconds into readable days, hours, minutes."""
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts) or "0m"


def get_cpu_info() -> Dict[str, Any]:
    """Collects CPU metrics including core count and usage."""
    core_count = os.cpu_count() or 1
    model = platform.processor() or "Unknown CPU"

    load_avg = [0.0, 0.0, 0.0]
    if hasattr(os, "getloadavg"):
        try:
            load_avg = list(os.getloadavg())
        except OSError:
            pass

    usage_pct = 0.0
    if HAS_PSUTIL:
        usage_pct = psutil.cpu_percent(interval=0.2)
    elif os.path.exists("/proc/stat"):
        try:
            with open("/proc/stat", "r") as f:
                fields = [float(column) for column in f.readline().strip().split()[1:]]
            idle, total = fields[3], sum(fields)
            time.sleep(0.1)
            with open("/proc/stat", "r") as f:
                fields = [float(column) for column in f.readline().strip().split()[1:]]
            idle2, total2 = fields[3], sum(fields)
            idle_delta = idle2 - idle
            total_delta = total2 - total
            if total_delta > 0:
                usage_pct = round(100.0 * (1.0 - idle_delta / total_delta), 1)
        except Exception:
            usage_pct = round((load_avg[0] / core_count) * 100, 1) if core_count else 0.0

    return {
        "model": model,
        "cores": core_count,
        "usage_pct": round(usage_pct, 1),
        "load_avg_1m": round(load_avg[0], 2),
        "load_avg_5m": round(load_avg[1], 2),
        "load_avg_15m": round(load_avg[2], 2),
    }


def get_memory_info() -> Dict[str, Any]:
    """Collects RAM and swap usage."""
    if HAS_PSUTIL:
        vmem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "total_mb": round(vmem.total / (1024 * 1024), 1),
            "used_mb": round(vmem.used / (1024 * 1024), 1),
            "free_mb": round(vmem.available / (1024 * 1024), 1),
            "used_pct": round(vmem.percent, 1),
            "swap_total_mb": round(swap.total / (1024 * 1024), 1),
            "swap_used_mb": round(swap.used / (1024 * 1024), 1),
            "swap_pct": round(swap.percent, 1),
        }

    # Fallback to /proc/meminfo on Linux
    if os.path.exists("/proc/meminfo"):
        mem_data: Dict[str, int] = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    if val.isdigit():
                        mem_data[key] = int(val)
        total_kb = mem_data.get("MemTotal", 1024)
        avail_kb = mem_data.get("MemAvailable", mem_data.get("MemFree", 0))
        used_kb = max(total_kb - avail_kb, 0)
        pct = (used_kb / total_kb) * 100 if total_kb else 0.0
        return {
            "total_mb": round(total_kb / 1024, 1),
            "used_mb": round(used_kb / 1024, 1),
            "free_mb": round(avail_kb / 1024, 1),
            "used_pct": round(pct, 1),
            "swap_total_mb": round(mem_data.get("SwapTotal", 0) / 1024, 1),
            "swap_used_mb": round(
                (mem_data.get("SwapTotal", 0) - mem_data.get("SwapFree", 0)) / 1024, 1
            ),
            "swap_pct": 0.0,
        }

    return {
        "total_mb": 0.0,
        "used_mb": 0.0,
        "free_mb": 0.0,
        "used_pct": 0.0,
        "swap_total_mb": 0.0,
        "swap_used_mb": 0.0,
        "swap_pct": 0.0,
    }


def get_disk_info() -> List[Dict[str, Any]]:
    """Inspects primary filesystem storage mounts."""
    results = []
    if HAS_PSUTIL:
        for part in psutil.disk_partitions(all=False):
            if os.name == "nt" and "cdrom" in part.opts or part.fstype == "":
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                results.append({
                    "mount": part.mountpoint,
                    "device": part.device,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "used_pct": round(usage.percent, 1),
                })
            except PermissionError:
                continue
        return results

    # Fallback to standard library shutil.disk_usage
    root_path = "C:\\" if os.name == "nt" else "/"
    try:
        total, used, free = shutil.disk_usage(root_path)
        pct = (used / total) * 100 if total > 0 else 0
        results.append({
            "mount": root_path,
            "device": root_path,
            "fstype": "standard",
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "used_pct": round(pct, 1),
        })
    except Exception:
        pass
    return results


def get_docker_summary() -> Dict[str, Any]:
    """Inspects Docker daemon and active containers via CLI if present."""
    summary: Dict[str, Any] = {
        "available": False,
        "containers_running": 0,
        "containers_total": 0,
        "containers": [],
    }
    if not shutil.which("docker"):
        return summary

    try:
        proc = subprocess.run(
            ["docker", "info", "--format", "{{.ContainersRunning}}|{{.Containers}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        )
        if proc.returncode == 0 and "|" in proc.stdout:
            parts = proc.stdout.strip().split("|")
            summary["available"] = True
            summary["containers_running"] = int(parts[0]) if parts[0].isdigit() else 0
            summary["containers_total"] = int(parts[1]) if parts[1].isdigit() else 0

            # List containers
            c_proc = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=3,
            )
            containers = []
            for line in c_proc.stdout.strip().splitlines():
                if line:
                    tokens = line.split("|")
                    containers.append({
                        "name": tokens[0] if len(tokens) > 0 else "",
                        "image": tokens[1] if len(tokens) > 1 else "",
                        "status": tokens[2] if len(tokens) > 2 else "",
                        "ports": tokens[3] if len(tokens) > 3 else "",
                    })
            summary["containers"] = containers
    except Exception:
        pass
    return summary


def get_top_processes(limit: int = 5) -> List[Dict[str, Any]]:
    """Returns top processes sorted by CPU and memory."""
    if not HAS_PSUTIL:
        return []
    procs = []
    try:
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = p.info
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"] or "unknown",
                    "cpu_pct": round(info["cpu_percent"] or 0.0, 1),
                    "mem_pct": round(info["memory_percent"] or 0.0, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda x: (x["cpu_pct"], x["mem_pct"]), reverse=True)
        return procs[:limit]
    except Exception:
        return []


def run_diagnostics() -> Dict[str, Any]:
    """Orchestrates a comprehensive system diagnostic audit."""
    uptime_sec = get_uptime_seconds()
    cpu = get_cpu_info()
    mem = get_memory_info()
    disks = get_disk_info()
    docker = get_docker_summary()
    top_proc = get_top_processes(5)

    # Determine overall node health
    warnings = []
    if cpu["usage_pct"] >= 90.0:
        warnings.append(f"Critical CPU usage: {cpu['usage_pct']}%")
    elif cpu["usage_pct"] >= 75.0:
        warnings.append(f"Elevated CPU usage: {cpu['usage_pct']}%")

    if mem["used_pct"] >= 92.0:
        warnings.append(f"Critical Memory usage: {mem['used_pct']}%")
    elif mem["used_pct"] >= 80.0:
        warnings.append(f"High Memory usage: {mem['used_pct']}%")

    for d in disks:
        if d["used_pct"] >= 90.0:
            warnings.append(f"Critical disk usage on {d['mount']}: {d['used_pct']}%")
        elif d["used_pct"] >= 80.0:
            warnings.append(f"High disk usage on {d['mount']}: {d['used_pct']}%")

    status = "CRITICAL" if any("Critical" in w for w in warnings) else (
        "WARNING" if warnings else "HEALTHY"
    )

    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "host": {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "uptime_seconds": int(uptime_sec),
            "uptime_human": format_duration(uptime_sec),
            "python_version": platform.python_version(),
        },
        "health_status": status,
        "warnings": warnings,
        "cpu": cpu,
        "memory": mem,
        "disks": disks,
        "docker": docker,
        "top_processes": top_proc,
    }


def print_text_diagnostics(data: Dict[str, Any]) -> None:
    """Pretty prints diagnostics to terminal."""
    h = data["host"]
    cpu = data["cpu"]
    mem = data["memory"]
    disks = data["disks"]
    docker = data["docker"]

    print("=" * 64)
    print(f" INFRAOPS AUTOMATION LAB - SYSTEM DIAGNOSTICS ({data['health_status']})")
    print("=" * 64)
    print(f"Host: {h['hostname']} | OS: {h['os']} {h['os_release']} ({h['architecture']})")
    print(f"Uptime: {h['uptime_human']} | Reported at: {data['timestamp']}")
    print("-" * 64)

    print(f"[CPU] Usage: {cpu['usage_pct']}% | Cores: {cpu['cores']} | Load: {cpu['load_avg_1m']}, {cpu['load_avg_5m']}, {cpu['load_avg_15m']}")
    print(f"[RAM] Used: {mem['used_mb']} MB / {mem['total_mb']} MB ({mem['used_pct']}%) | Free: {mem['free_mb']} MB")

    print("[DISKS]")
    for d in disks:
        print(f"  * Mount {d['mount']} [{d.get('fstype', 'fs')}]: {d['used_gb']} GB / {d['total_gb']} GB ({d['used_pct']}% used)")

    print(f"[DOCKER] Available: {docker['available']} | Running: {docker['containers_running']}/{docker['containers_total']}")
    for c in docker.get("containers", []):
        print(f"  - {c['name']} ({c['image']}) -> {c['status']}")

    if data["warnings"]:
        print("-" * 64)
        print("ALERT WARNINGS DETECTED:")
        for w in data["warnings"]:
            print(f"  ! {w}")
    print("=" * 64)


def main() -> None:
    parser = argparse.ArgumentParser(description="InfraOps System Diagnostics")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    data = run_diagnostics()
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_text_diagnostics(data)


if __name__ == "__main__":
    main()
