#!/usr/bin/env python3
"""
InfraOps Automation Lab - Network & Connectivity Probe
Module: python.diagnostics.network_probe
Purpose: Evaluates DNS resolution, TCP ports, socket latency, and SSL certificate health.
"""

from __future__ import annotations

import argparse
import datetime
import json
import socket
import ssl
import time
from typing import Any, Dict, List, Optional, Tuple


def probe_dns(host: str) -> Dict[str, Any]:
    """Tests DNS resolution and measures query latency."""
    t_start = time.perf_counter()
    try:
        resolved_ip = socket.gethostbyname(host)
        duration_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return {
            "host": host,
            "resolved_ip": resolved_ip,
            "reachable": True,
            "latency_ms": duration_ms,
            "error": None,
        }
    except Exception as e:
        duration_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return {
            "host": host,
            "resolved_ip": None,
            "reachable": False,
            "latency_ms": duration_ms,
            "error": str(e),
        }


def probe_tcp_port(host: str, port: int, timeout: float = 2.0) -> Dict[str, Any]:
    """Tests TCP socket handshake and measures latency."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    t_start = time.perf_counter()
    try:
        result = sock.connect_ex((host, port))
        duration_ms = round((time.perf_counter() - t_start) * 1000, 2)
        is_open = (result == 0)
        return {
            "host": host,
            "port": port,
            "open": is_open,
            "latency_ms": duration_ms if is_open else None,
            "error_code": result if not is_open else 0,
        }
    except Exception as e:
        return {
            "host": host,
            "port": port,
            "open": False,
            "latency_ms": None,
            "error_code": str(e),
        }
    finally:
        sock.close()


def probe_ssl_certificate(host: str, port: int = 443, timeout: float = 3.0) -> Dict[str, Any]:
    """Inspects SSL/TLS certificate validity and expiration date."""
    context = ssl.create_default_context()
    t_start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                duration_ms = round((time.perf_counter() - t_start) * 1000, 2)
                if not cert:
                    return {"host": host, "valid": False, "error": "No certificate received"}

                not_after_str = cert.get("notAfter", "")
                expiry_dt = datetime.datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(
                    tzinfo=datetime.timezone.utc
                )
                days_left = (expiry_dt - datetime.datetime.now(datetime.timezone.utc)).days

                subject = dict(x[0] for x in cert.get("subject", []))
                issuer = dict(x[0] for x in cert.get("issuer", []))

                return {
                    "host": host,
                    "valid": True,
                    "latency_ms": duration_ms,
                    "common_name": subject.get("commonName", host),
                    "issuer": issuer.get("organizationName", "Unknown"),
                    "expires_at": expiry_dt.isoformat(),
                    "days_until_expiration": days_left,
                    "is_expired": days_left <= 0,
                    "warning": days_left < 14,
                }
    except Exception as e:
        return {
            "host": host,
            "valid": False,
            "error": str(e),
            "days_until_expiration": None,
        }


def run_network_audit(targets: Optional[List[Tuple[str, int]]] = None) -> Dict[str, Any]:
    """Runs a standard network connectivity baseline probe."""
    if targets is None:
        targets = [
            ("1.1.1.1", 53),      # Cloudflare DNS
            ("8.8.8.8", 53),      # Google DNS
            ("github.com", 443),  # GitHub HTTPS
        ]

    probes = []
    for host, port in targets:
        dns_res = probe_dns(host)
        tcp_res = probe_tcp_port(host, port)
        ssl_res = probe_ssl_certificate(host, port) if port == 443 and not host.replace(".", "").isdigit() else None
        probes.append({
            "target": f"{host}:{port}",
            "dns": dns_res,
            "tcp": tcp_res,
            "ssl": ssl_res,
        })

    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "probes": probes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="InfraOps Network & SSL Probe")
    parser.add_argument("--host", default="github.com", help="Target host")
    parser.add_argument("--port", type=int, default=443, help="Target TCP port")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    audit = run_network_audit([(args.host, args.port)])
    if args.json:
        print(json.dumps(audit, indent=2))
    else:
        print(f"Network probe for {args.host}:{args.port}")
        for p in audit["probes"]:
            tcp = p["tcp"]
            status = "OPEN" if tcp["open"] else "CLOSED/TIMEOUT"
            lat = f"{tcp['latency_ms']} ms" if tcp["latency_ms"] else "N/A"
            print(f"  TCP Handshake: {status} ({lat})")
            if p["ssl"]:
                ssl_info = p["ssl"]
                if ssl_info.get("valid"):
                    print(f"  SSL Certificate: VALID (Expires in {ssl_info['days_until_expiration']} days)")
                else:
                    print(f"  SSL Certificate: FAILED ({ssl_info.get('error')})")


if __name__ == "__main__":
    main()
