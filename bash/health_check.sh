#!/usr/bin/env bash
# ==============================================================================
# InfraOps Automation Lab - Mission 3: Linux System Health Check
# Script: health_check.sh
# Purpose: Validates CPU, RAM, Disk, Systemd, Network, and Docker health.
# Exit Codes (Nagios/Monitoring standard):
#   0: OK (All checks passed)
#   1: WARNING (Non-critical threshold exceeded)
#   2: CRITICAL (Critical resource exhaustion or service failure)
# ==============================================================================

set -euo pipefail

# Threshold configurations
CPU_WARN=75
CPU_CRIT=90
MEM_WARN=80
MEM_CRIT=92
DISK_WARN=80
DISK_CRIT=90

# Output controls
CRON_MODE=false
JSON_MODE=false
OVERALL_STATUS=0 # 0=OK, 1=WARN, 2=CRIT

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cron|-q|--quiet)
            CRON_MODE=true
            shift
            ;;
        --json)
            JSON_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--cron|--quiet] [--json]"
            echo "Exit codes: 0 = OK, 1 = WARNING, 2 = CRITICAL"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# ANSI Colors
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BOLD="\033[1m"
RESET="\033[0m"

log_info() {
    if [ "$CRON_MODE" = false ] && [ "$JSON_MODE" = false ]; then
        echo -e "${GREEN}[OK]${RESET} $1"
    fi
}

log_warn() {
    if [ "$OVERALL_STATUS" -lt 1 ]; then OVERALL_STATUS=1; fi
    if [ "$JSON_MODE" = false ]; then
        echo -e "${YELLOW}[WARN]${RESET} $1" >&2
    fi
}

log_crit() {
    OVERALL_STATUS=2
    if [ "$JSON_MODE" = false ]; then
        echo -e "${RED}[CRITICAL]${RESET} $1" >&2
    fi
}

# 1. CPU Check
cpu_idle=$(top -bn1 2>/dev/null | grep -E "Cpu\(s\)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print int($1)}' || echo "50")
cpu_used=$(( 100 - cpu_idle ))

cpu_status="OK"
if [ "$cpu_used" -ge "$CPU_CRIT" ]; then
    log_crit "CPU usage is CRITICAL: ${cpu_used}% (Threshold: >=${CPU_CRIT}%)"
    cpu_status="CRITICAL"
elif [ "$cpu_used" -ge "$CPU_WARN" ]; then
    log_warn "CPU usage is HIGH: ${cpu_used}% (Threshold: >=${CPU_WARN}%)"
    cpu_status="WARNING"
else
    log_info "CPU usage: ${cpu_used}% (Idle: ${cpu_idle}%)"
fi

# 2. Memory Check
mem_used_pct=0
if command -v free >/dev/null 2>&1; then
    mem_used_pct=$(free | awk '/Mem:/ {if ($2>0) printf("%d", ($3/$2)*100); else print 0}')
fi

mem_status="OK"
if [ "$mem_used_pct" -ge "$MEM_CRIT" ]; then
    log_crit "RAM usage is CRITICAL: ${mem_used_pct}% (Threshold: >=${MEM_CRIT}%)"
    mem_status="CRITICAL"
elif [ "$mem_used_pct" -ge "$MEM_WARN" ]; then
    log_warn "RAM usage is HIGH: ${mem_used_pct}% (Threshold: >=${MEM_WARN}%)"
    mem_status="WARNING"
else
    log_info "RAM usage: ${mem_used_pct}%"
fi

# 3. Disk Check (Root Filesystem)
disk_used_pct=$(df / 2>/dev/null | awk 'NR==2 {gsub(/%/, "", $5); print $5}' || echo "0")

disk_status="OK"
if [ "$disk_used_pct" -ge "$DISK_CRIT" ]; then
    log_crit "Root Disk (/) usage is CRITICAL: ${disk_used_pct}% (Threshold: >=${DISK_CRIT}%)"
    disk_status="CRITICAL"
elif [ "$disk_used_pct" -ge "$DISK_WARN" ]; then
    log_warn "Root Disk (/) usage is HIGH: ${disk_used_pct}% (Threshold: >=${DISK_WARN}%)"
    disk_status="WARNING"
else
    log_info "Root Disk (/) usage: ${disk_used_pct}%"
fi

# 4. Systemd Failed Services Check
failed_services=0
failed_services_list=""
if command -v systemctl >/dev/null 2>&1; then
    failed_services_list=$(systemctl --failed --no-legend 2>/dev/null | awk '{print $2}' || true)
    if [ -n "$failed_services_list" ]; then
        failed_services=$(echo "$failed_services_list" | wc -l | tr -d ' ')
        log_warn "Systemd has ${failed_services} failed unit(s): $(echo "$failed_services_list" | tr '\n' ' ')"
    else
        log_info "Systemd units: All active and healthy"
    fi
else
    log_info "Systemd check skipped (not available in this environment)"
fi

# 5. Network Connectivity Check
network_ok=true
if ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1 || ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    log_info "Internet / Gateway connectivity: REACHABLE"
else
    log_warn "Outbound internet ping failed (1.1.1.1 / 8.8.8.8 unreachable)"
    network_ok=false
fi

# 6. Docker Health Check
docker_status="N/A"
unhealthy_containers=0
if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        docker_status="RUNNING"
        # Check for unhealthy or restarting containers
        unhealthy_containers=$(docker ps --filter "health=unhealthy" -q 2>/dev/null | wc -l | tr -d ' ')
        restarting_containers=$(docker ps --filter "status=restarting" -q 2>/dev/null | wc -l | tr -d ' ')
        
        if [ "$unhealthy_containers" -gt 0 ] || [ "$restarting_containers" -gt 0 ]; then
            log_warn "Docker detected unhealthy (${unhealthy_containers}) or restarting (${restarting_containers}) containers"
        else
            log_info "Docker daemon is active, all monitored containers healthy"
        fi
    else
        log_warn "Docker command exists, but daemon is not responding"
        docker_status="STOPPED"
    fi
fi

# Output JSON if requested
if [ "$JSON_MODE" = true ]; then
    cat <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "status_code": ${OVERALL_STATUS},
  "overall_status": "$([ $OVERALL_STATUS -eq 0 ] && echo "OK" || ([ $OVERALL_STATUS -eq 1 ] && echo "WARNING" || echo "CRITICAL"))",
  "checks": {
    "cpu": {
      "used_pct": ${cpu_used},
      "status": "${cpu_status}"
    },
    "memory": {
      "used_pct": ${mem_used_pct},
      "status": "${mem_status}"
    },
    "disk": {
      "used_pct": ${disk_used_pct},
      "status": "${disk_status}"
    },
    "systemd": {
      "failed_units_count": ${failed_services}
    },
    "network": {
      "internet_reachable": ${network_ok}
    },
    "docker": {
      "status": "${docker_status}",
      "unhealthy_containers": ${unhealthy_containers}
    }
  }
}
EOF
fi

if [ "$CRON_MODE" = false ] && [ "$JSON_MODE" = false ]; then
    echo "--------------------------------------------------------"
    if [ "$OVERALL_STATUS" -eq 0 ]; then
        echo -e "${BOLD}${GREEN}Summary: SYSTEM STATUS IS HEALTHY (Exit 0)${RESET}"
    elif [ "$OVERALL_STATUS" -eq 1 ]; then
        echo -e "${BOLD}${YELLOW}Summary: SYSTEM HAS WARNINGS (Exit 1)${RESET}"
    else
        echo -e "${BOLD}${RED}Summary: SYSTEM REQUIRES CRITICAL ATTENTION (Exit 2)${RESET}"
    fi
    echo "--------------------------------------------------------"
fi

exit "$OVERALL_STATUS"
