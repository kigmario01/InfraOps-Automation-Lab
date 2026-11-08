#!/usr/bin/env python3
"""
InfraOps Automation Lab - Master CLI Tool
File: python/infraops_cli.py
Purpose: Unified command-line interface for diagnostics, monitoring, reports, and alerts.
Usage:
    python python/infraops_cli.py diagnose
    python python/infraops_cli.py check-endpoints
    python python/infraops_cli.py probe-network --host github.com
    python python/infraops_cli.py report --output-dir reports
    python python/infraops_cli.py alert --title "High CPU" --message "CPU usage is 95%"
    python python/infraops_cli.py full-audit
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.diagnostics.network_probe import probe_dns, probe_tcp_port, probe_ssl_certificate, run_network_audit
from python.diagnostics.sys_diagnostics import run_diagnostics, print_text_diagnostics
from python.monitoring.alert_manager import AlertManager
from python.monitoring.service_checker import check_all_services, DEFAULT_ENDPOINTS, load_endpoints_from_file
from python.reports.generate_report import build_full_report_data, generate_html_report, generate_markdown_report


def cmd_diagnose(args: argparse.Namespace) -> int:
    data = run_diagnostics()
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_text_diagnostics(data)
    return 0 if data["health_status"] == "HEALTHY" else (1 if data["health_status"] == "WARNING" else 2)


def cmd_check_endpoints(args: argparse.Namespace) -> int:
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
    return 0 if summary["down"] == 0 else 1


def cmd_probe_network(args: argparse.Namespace) -> int:
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
            if p.get("ssl"):
                ssl_info = p["ssl"]
                if ssl_info.get("valid"):
                    print(f"  SSL Certificate: VALID (Expires in {ssl_info['days_until_expiration']} days)")
                else:
                    print(f"  SSL Certificate: FAILED ({ssl_info.get('error')})")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    os.makedirs(args.output_dir, exist_ok=True)
    report_data = build_full_report_data()

    html_path = os.path.join(args.output_dir, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(generate_html_report(report_data))

    md_path = os.path.join(args.output_dir, "report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(generate_markdown_report(report_data))

    json_path = os.path.join(args.output_dir, "report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"Reports successfully generated in '{args.output_dir}/':")
    print(f"  * HTML: {html_path}")
    print(f"  * Markdown: {md_path}")
    print(f"  * JSON: {json_path}")
    return 0


def cmd_alert(args: argparse.Namespace) -> int:
    mgr = AlertManager(webhook_url=args.webhook)
    success = mgr.send_alert(
        title=args.title,
        message=args.message,
        severity=args.severity,
    )
    return 0 if success else 1


def cmd_full_audit(args: argparse.Namespace) -> int:
    print(">>> Executing Full InfraOps System & Service Audit...")
    report_data = build_full_report_data()
    status = report_data["overall_status"]

    # Save reports
    os.makedirs(args.output_dir, exist_ok=True)
    html_path = os.path.join(args.output_dir, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(generate_html_report(report_data))

    print(f">>> Audit complete. System Overall Status: {status}")
    print(f">>> Executive report saved to {html_path}")

    # Trigger alert if abnormal
    if status in ("WARNING", "CRITICAL") and args.notify:
        mgr = AlertManager(webhook_url=args.webhook)
        mgr.send_alert(
            title=f"Infrastructure Audit Result: {status}",
            message=f"Audit completed with status {status}. Review report for details.",
            severity=status,
        )

    return 0 if status == "HEALTHY" else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="infraops",
        description="InfraOps Automation Lab - Unified CLI Tool",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: diagnose
    p_diag = subparsers.add_parser("diagnose", help="Run system resource diagnostics")
    p_diag.add_argument("--json", action="store_true", help="Output in JSON")
    p_diag.set_defaults(func=cmd_diagnose)

    # Subcommand: check-endpoints
    p_check = subparsers.add_parser("check-endpoints", help="Check HTTP/HTTPS service uptime")
    p_check.add_argument("--config", help="Path to endpoints configuration JSON")
    p_check.add_argument("--json", action="store_true", help="Output in JSON")
    p_check.set_defaults(func=cmd_check_endpoints)

    # Subcommand: probe-network
    p_net = subparsers.add_parser("probe-network", help="Inspect DNS, TCP port, and SSL certificate")
    p_net.add_argument("--host", default="github.com", help="Target hostname or IP")
    p_net.add_argument("--port", type=int, default=443, help="Target TCP port")
    p_net.add_argument("--json", action="store_true", help="Output in JSON")
    p_net.set_defaults(func=cmd_probe_network)

    # Subcommand: report
    p_rep = subparsers.add_parser("report", help="Generate HTML and Markdown reports")
    p_rep.add_argument("--output-dir", default="reports", help="Directory where reports are stored")
    p_rep.set_defaults(func=cmd_report)

    # Subcommand: alert
    p_alt = subparsers.add_parser("alert", help="Dispatch alert notification")
    p_alt.add_argument("--title", default="Manual Alert", help="Alert title")
    p_alt.add_argument("--message", default="InfraOps manual test alert", help="Alert message")
    p_alt.add_argument(
        "--severity",
        choices=["INFO", "WARNING", "CRITICAL", "RECOVERY"],
        default="WARNING",
    )
    p_alt.add_argument("--webhook", help="Webhook URL override")
    p_alt.set_defaults(func=cmd_alert)

    # Subcommand: full-audit
    p_audit = subparsers.add_parser("full-audit", help="Run full system audit and generate reports")
    p_audit.add_argument("--output-dir", default="reports")
    p_audit.add_argument("--notify", action="store_true", help="Send alert if status is not healthy")
    p_audit.add_argument("--webhook", help="Webhook URL override")
    p_audit.set_defaults(func=cmd_full_audit)

    args = parser.parse_args()
    exit_code = args.func(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
