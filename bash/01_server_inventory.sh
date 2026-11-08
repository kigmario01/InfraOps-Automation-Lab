#!/usr/bin/env bash
# ==============================================================================
# InfraOps Automation Lab - Mission 1: Technical Server Inventory
# Script: 01_server_inventory.sh
# Purpose: Gathers non-invasive technical hardware, OS, network, and Docker specs.
# Standard: POSIX/Bash strict mode, idempotency, read-only operation.
# ==============================================================================

set -euo pipefail

# Colors for terminal output
BOLD=$'\033[1m'
GREEN=$'\033[0;32m'
CYAN=$'\033[0;36m'
YELLOW=$'\033[1;33m'
RED=$'\033[0;31m'
RESET=$'\033[0m'

OUTPUT_JSON=false
OUTPUT_FILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            OUTPUT_JSON=true
            shift
            ;;
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--output file.txt|json]"
            echo "Options:"
            echo "  --json        Output in structured JSON format"
            echo "  -o, --output  Save results to specified file path"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
hostname=$(hostname)

# Collect Information
os_info="Unknown"
if [ -f /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    os_info="${NAME} ${VERSION}"
fi
kernel=$(uname -r)
arch=$(uname -m)
uptime_str=$(uptime -p 2>/dev/null || uptime | awk -F'( |,|:)+' '{print $6,"hours,",$7,"min"}')

# CPU
cpu_model=$(lscpu 2>/dev/null | grep -E 'Model name' | sed -e 's/Model name:[ \t]*//' || echo "N/A")
cpu_cores=$(nproc 2>/dev/null || grep -c '^processor' /proc/cpuinfo || echo "1")
load_avg=$(cat /proc/loadavg 2>/dev/null | awk '{print $1", "$2", "$3}' || echo "N/A")

# Memory
if command -v free >/dev/null 2>&1; then
    mem_total=$(free -h | awk '/^Mem:/ {print $2}')
    mem_used=$(free -h | awk '/^Mem:/ {print $3}')
    mem_free=$(free -h | awk '/^Mem:/ {print $4}')
    swap_total=$(free -h | awk '/^Swap:/ {print $2}')
    swap_used=$(free -h | awk '/^Swap:/ {print $3}')
else
    mem_total="N/A"
    mem_used="N/A"
    mem_free="N/A"
    swap_total="N/A"
    swap_used="N/A"
fi

# Disk root
disk_total=$(df -h / 2>/dev/null | awk 'NR==2 {print $2}')
disk_used=$(df -h / 2>/dev/null | awk 'NR==2 {print $3}')
disk_avail=$(df -h / 2>/dev/null | awk 'NR==2 {print $4}')
disk_percent=$(df -h / 2>/dev/null | awk 'NR==2 {print $5}')

# Network IP
ip_addrs=$(ip -4 -o addr show 2>/dev/null | awk '{print $2 ": " $4}' | tr '\n' ', ' | sed 's/, $//' || echo "N/A")
default_gw=$(ip route show default 2>/dev/null | awk '{print $3}' | sort -u | tr '\n' ' ' | sed 's/ $//' || echo "N/A")

# Docker check
docker_installed=false
docker_active=false
docker_containers_count=0
docker_containers_table="None"

if command -v docker >/dev/null 2>&1; then
    docker_installed=true
    if docker info >/dev/null 2>&1; then
        docker_active=true
        docker_containers_count=$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')
        docker_containers_table=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No active containers")
    fi
fi

# Listening ports
if command -v ss >/dev/null 2>&1; then
    open_ports=$(ss -tuln 2>/dev/null | awk 'NR>1 {print $1, $5}' | head -n 10 | tr '\n' '; ' | sed 's/; $//')
else
    open_ports="ss command unavailable"
fi

# Produce Human Readable Report
generate_text_report() {
    cat <<EOF
${BOLD}${CYAN}================================================================${RESET}
${BOLD}${GREEN}          INFRAOPS AUTOMATION LAB - TECHNICAL INVENTORY         ${RESET}
${BOLD}${CYAN}================================================================${RESET}
Generated at: ${timestamp}
Node Hostname: ${BOLD}${hostname}${RESET}

${BOLD}[1] SISTEMA OPERATIVO & KERNEL${RESET}
  * OS / Distribution : ${os_info}
  * Kernel Release    : ${kernel}
  * Architecture      : ${arch}
  * System Uptime     : ${uptime_str}

${BOLD}[2] RECURSOS DE HARDWARE${RESET}
  * CPU Model         : ${cpu_model}
  * Total CPU Cores   : ${cpu_cores}
  * Load Average      : ${load_avg}
  * Memory (RAM)      : Total: ${mem_total} | Used: ${mem_used} | Free: ${mem_free}
  * Swap Space        : Total: ${swap_total} | Used: ${swap_used}
  * Root Disk (/)     : Total: ${disk_total} | Used: ${disk_used} (${disk_percent}) | Available: ${disk_avail}

${BOLD}[3] RED Y CONECTIVIDAD${RESET}
  * Active IPv4 Addrs : ${ip_addrs}
  * Default Gateway   : ${default_gw}
  * Open Ports Sample : ${open_ports}

${BOLD}[4] SERVICIOS DOCKER${RESET}
  * Docker Installed  : ${docker_installed}
  * Daemon Active     : ${docker_active}
  * Running Containers: ${docker_containers_count}
${docker_containers_table}

${BOLD}${CYAN}================================================================${RESET}
${BOLD}${YELLOW}Recomendación de seguridad:${RESET} Mantener este inventario versionado
en Git para detectar drift de infraestructura.
EOF
}

# Produce JSON Report
generate_json_report() {
    cat <<EOF
{
  "timestamp": "${timestamp}",
  "hostname": "${hostname}",
  "system": {
    "os": "${os_info}",
    "kernel": "${kernel}",
    "architecture": "${arch}",
    "uptime": "${uptime_str}"
  },
  "resources": {
    "cpu": {
      "model": "${cpu_model}",
      "cores": ${cpu_cores},
      "load_avg": "${load_avg}"
    },
    "memory": {
      "ram_total": "${mem_total}",
      "ram_used": "${mem_used}",
      "ram_free": "${mem_free}",
      "swap_total": "${swap_total}",
      "swap_used": "${swap_used}"
    },
    "disk": {
      "mount": "/",
      "total": "${disk_total}",
      "used": "${disk_used}",
      "free": "${disk_avail}",
      "percentage": "${disk_percent}"
    }
  },
  "network": {
    "interfaces": "${ip_addrs}",
    "default_gateway": "${default_gw}"
  },
  "docker": {
    "installed": ${docker_installed},
    "active": ${docker_active},
    "running_containers": ${docker_containers_count}
  }
}
EOF
}

# Output handling
if [ "$OUTPUT_JSON" = true ]; then
    if [ -n "$OUTPUT_FILE" ]; then
        generate_json_report > "$OUTPUT_FILE"
        echo "Inventory saved to JSON file: $OUTPUT_FILE"
    else
        generate_json_report
    fi
else
    if [ -n "$OUTPUT_FILE" ]; then
        generate_text_report > "$OUTPUT_FILE"
        echo "Inventory saved to file: $OUTPUT_FILE"
    else
        generate_text_report
    fi
fi
