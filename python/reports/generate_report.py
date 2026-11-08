#!/usr/bin/env python3
"""
InfraOps Automation Lab - Mission 12: Infrastructure Executive Report Generator
Module: python.reports.generate_report
Purpose: Generates modern HTML, Markdown, and JSON executive reports summarizing
         host health, resources, Docker containers, and service uptime.
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import os
import sys

# Ensure repository root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from typing import Any, Dict, Optional

# Import local diagnostics and monitoring modules
from python.diagnostics.sys_diagnostics import run_diagnostics
from python.monitoring.service_checker import check_all_services


def generate_html_report(data: Dict[str, Any]) -> str:
    """Renders a responsive, modern HTML5 report with embedded CSS."""
    h = data["host"]
    cpu = data["cpu"]
    mem = data["memory"]
    disks = data["disks"]
    docker = data["docker"]
    services = data["services"]
    overall = data["overall_status"]

    # Color badge for overall status
    status_bg = "#2ecc71" if overall == "HEALTHY" else ("#f39c12" if overall == "WARNING" else "#e74c3c")

    # Generate disk rows
    disk_rows_html = ""
    for d in disks:
        pct = d.get("used_pct", 0)
        bar_color = "#2ecc71" if pct < 80 else ("#f39c12" if pct < 90 else "#e74c3c")
        disk_rows_html += f"""
        <tr>
            <td><strong>{html.escape(str(d.get('mount')))}</strong></td>
            <td>{d.get('used_gb', 0)} GB / {d.get('total_gb', 0)} GB</td>
            <td>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: {pct}%; background-color: {bar_color};"></div>
                </div>
            </td>
            <td><strong>{pct}%</strong></td>
        </tr>
        """

    # Generate service rows
    service_rows_html = ""
    for s in services.get("endpoints", []):
        st = s.get("state", "UNKNOWN")
        st_color = "#2ecc71" if st == "UP" else ("#f39c12" if st == "DEGRADED" else "#e74c3c")
        lat = f"{s.get('latency_ms', 'N/A')} ms"
        code = f"HTTP {s.get('http_code')}" if s.get('http_code') else "NO RESPONSE"
        service_rows_html += f"""
        <tr>
            <td><strong>{html.escape(s.get('name', ''))}</strong><br><small class="text-muted">{html.escape(s.get('url', ''))}</small></td>
            <td><span class="badge" style="background-color: {st_color};">{st}</span></td>
            <td>{lat}</td>
            <td>{code}</td>
        </tr>
        """

    # Generate container rows
    docker_rows_html = ""
    if docker.get("containers"):
        for c in docker["containers"]:
            docker_rows_html += f"""
            <tr>
                <td><strong>{html.escape(c.get('name', ''))}</strong></td>
                <td><code>{html.escape(c.get('image', ''))}</code></td>
                <td>{html.escape(c.get('status', ''))}</td>
                <td><small>{html.escape(c.get('ports', 'None'))}</small></td>
            </tr>
            """
    else:
        docker_rows_html = "<tr><td colspan='4' class='text-muted'>No running containers or Docker inactive.</td></tr>"

    cpu_bar_color = "#2ecc71" if cpu['usage_pct'] < 75 else ("#f39c12" if cpu['usage_pct'] < 90 else "#e74c3c")
    mem_bar_color = "#2ecc71" if mem['used_pct'] < 80 else ("#f39c12" if mem['used_pct'] < 92 else "#e74c3c")

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InfraOps Report - {html.escape(h['hostname'])}</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --border-color: #334155;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            padding: 2rem 1rem;
            line-height: 1.5;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        h1 {{ font-size: 1.75rem; font-weight: 700; color: #fff; }}
        .badge {{
            display: inline-block;
            padding: 0.35rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            color: #fff;
            text-transform: uppercase;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }}
        .card h3 {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .card .metric-val {{
            font-size: 2rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 0.5rem;
        }}
        .card .metric-sub {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        .progress-bar-container {{
            width: 100%;
            height: 8px;
            background: #334155;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }}
        .progress-bar {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            margin-top: 0.5rem;
        }}
        th, td {{
            padding: 0.85rem 1rem;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            color: var(--text-secondary);
            font-size: 0.8rem;
            text-transform: uppercase;
        }}
        .section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--accent);
        }}
        .text-muted {{ color: var(--text-secondary); }}
        footer {{
            margin-top: 3rem;
            text-align: center;
            font-size: 0.85rem;
            color: var(--text-secondary);
            border-top: 1px solid var(--border-color);
            padding-top: 1.5rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>InfraOps Automation Lab</h1>
                <p class="text-muted">Informe Técnico de Infraestructura y Observabilidad</p>
            </div>
            <div>
                <span class="badge" style="background-color: {status_bg};">{overall}</span>
            </div>
        </header>

        <!-- KPI Metrics Grid -->
        <div class="grid">
            <div class="card">
                <h3>Servidor / Host</h3>
                <div class="metric-val" style="font-size: 1.4rem;">{html.escape(h['hostname'])}</div>
                <div class="metric-sub">{html.escape(h['os'])} {html.escape(h['os_release'])} ({html.escape(h['architecture'])})<br>Uptime: {h['uptime_human']}</div>
            </div>
            <div class="card">
                <h3>Uso de CPU</h3>
                <div class="metric-val">{cpu['usage_pct']}%</div>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: {cpu['usage_pct']}%; background-color: {cpu_bar_color};"></div>
                </div>
                <div class="metric-sub" style="margin-top:0.5rem;">Cores: {cpu['cores']} | Load: {cpu['load_avg_1m']}, {cpu['load_avg_5m']}</div>
            </div>
            <div class="card">
                <h3>Memoria RAM</h3>
                <div class="metric-val">{mem['used_pct']}%</div>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: {mem['used_pct']}%; background-color: {mem_bar_color};"></div>
                </div>
                <div class="metric-sub" style="margin-top:0.5rem;">{mem['used_mb']} MB / {mem['total_mb']} MB ({mem['free_mb']} MB libres)</div>
            </div>
            <div class="card">
                <h3>Servicios Monitoreados</h3>
                <div class="metric-val">{services.get('up', 0)} / {services.get('total_services', 0)}</div>
                <div class="metric-sub">Up: {services.get('up', 0)} | Degraded: {services.get('degraded', 0)} | Down: {services.get('down', 0)}</div>
            </div>
        </div>

        <!-- Filesystem Disks -->
        <div class="card" style="margin-bottom: 1.5rem;">
            <h2 class="section-title">Almacenamiento y Particiones de Disco</h2>
            <table>
                <thead>
                    <tr>
                        <th>Punto de Montaje</th>
                        <th>Espacio Usado / Total</th>
                        <th>Barra de Uso</th>
                        <th>Porcentaje</th>
                    </tr>
                </thead>
                <tbody>
                    {disk_rows_html}
                </tbody>
            </table>
        </div>

        <!-- Service Availability -->
        <div class="card" style="margin-bottom: 1.5rem;">
            <h2 class="section-title">Disponibilidad de Endpoints y Servicios Web</h2>
            <table>
                <thead>
                    <tr>
                        <th>Servicio</th>
                        <th>Estado</th>
                        <th>Latencia</th>
                        <th>Código HTTP</th>
                    </tr>
                </thead>
                <tbody>
                    {service_rows_html}
                </tbody>
            </table>
        </div>

        <!-- Docker Containers -->
        <div class="card">
            <h2 class="section-title">Contenedores Docker</h2>
            <table>
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>Imagen</th>
                        <th>Estado</th>
                        <th>Puertos</th>
                    </tr>
                </thead>
                <tbody>
                    {docker_rows_html}
                </tbody>
            </table>
        </div>

        <footer>
            <p>Reporte generado automáticamente el {data['timestamp']} | InfraOps Automation Lab Portfolio</p>
        </footer>
    </div>
</body>
</html>
"""
    return html_content


def generate_markdown_report(data: Dict[str, Any]) -> str:
    """Generates GitHub Flavored Markdown report."""
    h = data["host"]
    cpu = data["cpu"]
    mem = data["memory"]
    disks = data["disks"]
    docker = data["docker"]
    services = data["services"]
    overall = data["overall_status"]

    md = f"""# InfraOps Automation Lab - Infrastructure Status Report

**Generated at:** `{data['timestamp']}`  
**Host:** `{h['hostname']}` (`{h['os']} {h['os_release']}`) | **Uptime:** `{h['uptime_human']}`  
**Overall Status:** **`{overall}`**

---

## 1. System Resources & Hardware
| Metric | Current Value | Details |
| :--- | :--- | :--- |
| **CPU Usage** | `{cpu['usage_pct']}%` | {cpu['cores']} cores, Load: `{cpu['load_avg_1m']}, {cpu['load_avg_5m']}, {cpu['load_avg_15m']}` |
| **RAM Memory** | `{mem['used_pct']}%` | `{mem['used_mb']} MB` used / `{mem['total_mb']} MB` total (`{mem['free_mb']} MB` free) |
| **Swap** | `{mem['swap_pct']}%` | `{mem['swap_used_mb']} MB` / `{mem['swap_total_mb']} MB` |

### Disks & Mounts
| Mount Point | Used / Total | Percentage |
| :--- | :--- | :--- |
"""
    for d in disks:
        md += f"| `{d.get('mount')}` | `{d.get('used_gb')} GB / {d.get('total_gb')} GB` | **{d.get('used_pct')}%** |\n"

    md += """
---

## 2. Service Availability & Latency
| Service Name | URL | State | Latency | HTTP Code |
| :--- | :--- | :--- | :--- | :--- |
"""
    for s in services.get("endpoints", []):
        state_icon = "🟢" if s.get("state") == "UP" else ("🟡" if s.get("state") == "DEGRADED" else "🔴")
        md += f"| {s.get('name')} | `{s.get('url')}` | {state_icon} **{s.get('state')}** | `{s.get('latency_ms', 'N/A')} ms` | `{s.get('http_code', 'ERR')}` |\n"

    md += f"""
---

## 3. Docker Containers Status
* **Docker Daemon Active:** `{docker.get('available')}`
* **Active Containers:** `{docker.get('containers_running', 0)} / {docker.get('containers_total', 0)}`

| Container Name | Image | Status | Ports |
| :--- | :--- | :--- | :--- |
"""
    if docker.get("containers"):
        for c in docker["containers"]:
            md += f"| `{c.get('name')}` | `{c.get('image')}` | {c.get('status')} | `{c.get('ports', 'N/A')}` |\n"
    else:
        md += "| *No active containers detected* | - | - | - |\n"

    md += "\n---\n*Report generated by InfraOps Automation Lab Automation Suite.*\n"
    return md


def build_full_report_data() -> Dict[str, Any]:
    """Collects all diagnostics and service health data into a unified dictionary."""
    diag = run_diagnostics()
    services = check_all_services()

    # Consolidate overall status
    overall = "HEALTHY"
    if diag["health_status"] == "CRITICAL" or services["overall_status"] == "CRITICAL":
        overall = "CRITICAL"
    elif diag["health_status"] == "WARNING" or services["overall_status"] == "DEGRADED":
        overall = "WARNING"

    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "overall_status": overall,
        "host": diag["host"],
        "cpu": diag["cpu"],
        "memory": diag["memory"],
        "disks": diag["disks"],
        "docker": diag["docker"],
        "top_processes": diag["top_processes"],
        "services": services,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="InfraOps Report Generator")
    parser.add_argument("--output-dir", default="reports", help="Target output directory")
    parser.add_argument("--format", choices=["all", "html", "md", "json"], default="all")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    report_data = build_full_report_data()

    if args.format in ("all", "html"):
        html_path = os.path.join(args.output_dir, "report.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(generate_html_report(report_data))
        print(f"Generated HTML report: {html_path}")

    if args.format in ("all", "md"):
        md_path = os.path.join(args.output_dir, "report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(generate_markdown_report(report_data))
        print(f"Generated Markdown report: {md_path}")

    if args.format in ("all", "json"):
        json_path = os.path.join(args.output_dir, "report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        print(f"Generated JSON report: {json_path}")


if __name__ == "__main__":
    main()
