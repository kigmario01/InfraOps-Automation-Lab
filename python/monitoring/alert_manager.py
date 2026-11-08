#!/usr/bin/env python3
"""
InfraOps Automation Lab - Mission 14: Alerting & Incident Notification Engine
Module: python.monitoring.alert_manager
Purpose: Dispatches structured alert notifications to Webhooks (Slack/Discord/Telegram)
         or system logs upon threshold breach or service outage.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class AlertManager:
    """Manages dispatching and logging infrastructure alerts."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("ALERT_WEBHOOK_URL", "").strip()

    def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "WARNING",
        node: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Sends an alert notification.
        Severity levels: INFO, WARNING, CRITICAL, RECOVERY
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        host = node or os.getenv("HOSTNAME", "unknown-host")

        # Visual indicator colors
        color_map = {
            "INFO": 0x3498DB,      # Blue
            "WARNING": 0xF39C12,   # Amber/Orange
            "CRITICAL": 0xE74C3C,  # Red
            "RECOVERY": 0x2ECC71,  # Green
        }
        color_code = color_map.get(severity.upper(), 0x95A5A6)

        # Discord / Slack compatible payload
        payload = {
            "username": "InfraOps Monitor",
            "content": f"**[{severity.upper()}]** {title}",
            "embeds": [
                {
                    "title": f"🚨 {title}" if severity in ("WARNING", "CRITICAL") else f"✅ {title}",
                    "description": message,
                    "color": color_code,
                    "fields": [
                        {"name": "Server / Host", "value": f"`{host}`", "inline": True},
                        {"name": "Severity", "value": f"**{severity.upper()}**", "inline": True},
                        {"name": "Timestamp", "value": timestamp, "inline": False},
                    ],
                    "footer": {"text": "InfraOps Automation Lab | Telemetry & Observability"},
                }
            ],
        }

        if metadata:
            for k, v in metadata.items():
                payload["embeds"][0]["fields"].append(
                    {"name": str(k), "value": f"`{str(v)}`", "inline": True}
                )

        # Console logging always happens
        print(f"[{timestamp}] [{severity.upper()}] {title}: {message} (Host: {host})")

        if not self.webhook_url:
            print("  -> Notice: ALERT_WEBHOOK_URL not configured. Alert logged to console.")
            return True

        # Send HTTP POST to Webhook
        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "InfraOps-AlertManager/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status in (200, 204):
                    print(f"  -> Alert successfully dispatched to webhook ({resp.status}).")
                    return True
                print(f"  -> Webhook returned status {resp.status}.")
                return False
        except urllib.error.URLError as e:
            print(f"  -> Failed to deliver alert to webhook: {e.reason}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"  -> Unexpected error sending alert: {e}", file=sys.stderr)
            return False


def main() -> None:
    parser = argparse.ArgumentParser(description="InfraOps Alert Notification Dispatcher")
    parser.add_argument("--title", default="Test Alert", help="Alert title summary")
    parser.add_argument("--message", default="This is a test notification from InfraOps Lab", help="Detailed alert body")
    parser.add_argument(
        "--severity",
        choices=["INFO", "WARNING", "CRITICAL", "RECOVERY"],
        default="WARNING",
        help="Alert severity level",
    )
    parser.add_argument("--webhook", help="Webhook destination URL")
    args = parser.parse_args()

    manager = AlertManager(webhook_url=args.webhook)
    success = manager.send_alert(
        title=args.title,
        message=args.message,
        severity=args.severity,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
