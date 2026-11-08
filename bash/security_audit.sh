#!/usr/bin/env bash
# ==============================================================================
# InfraOps Automation Lab - Mission 4: Security Audit & SSH Hardening Verification
# Script: security_audit.sh
# Purpose: Non-invasive security baseline inspection for Linux servers.
# ==============================================================================

set -euo pipefail

# ANSI Colors
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
BOLD="\033[1m"
RESET="\033[0m"

PASSED_CHECKS=0
TOTAL_CHECKS=0
WARNINGS=0

check_result() {
    local status="$1"
    local desc="$2"
    local detail="${3:-}"

    TOTAL_CHECKS=$(( TOTAL_CHECKS + 1 ))
    if [ "$status" = "PASS" ]; then
        PASSED_CHECKS=$(( PASSED_CHECKS + 1 ))
        echo -e "${GREEN}[PASS]${RESET} $desc"
    elif [ "$status" = "WARN" ]; then
        WARNINGS=$(( WARNINGS + 1 ))
        echo -e "${YELLOW}[WARN]${RESET} $desc"
        [ -n "$detail" ] && echo -e "       ${YELLOW}-> $detail${RESET}"
    else
        echo -e "${RED}[FAIL]${RESET} $desc"
        [ -n "$detail" ] && echo -e "       ${RED}-> $detail${RESET}"
    fi
}

echo -e "${BOLD}${CYAN}================================================================${RESET}"
echo -e "${BOLD}${CYAN}          INFRAOPS AUTOMATION LAB - SECURITY AUDIT              ${RESET}"
echo -e "${BOLD}${CYAN}================================================================${RESET}"
echo "Audited at: $(date -u '+%Y-%m-%d %H:%M:%SZ') on host $(hostname)"
echo ""

# 1. SSH Server Configuration Audit
echo -e "${BOLD}1. SSH Configuration Hardening (/etc/ssh/sshd_config)${RESET}"
SSHD_CONFIG="/etc/ssh/sshd_config"

if [ -f "$SSHD_CONFIG" ]; then
    # Root Login
    root_login=$(grep -Ei '^\s*PermitRootLogin' "$SSHD_CONFIG" | awk '{print $2}' || echo "default(yes)")
    if [[ "$root_login" =~ ^(no|prohibit-password|without-password)$ ]]; then
        check_result "PASS" "PermitRootLogin is restricted ($root_login)"
    else
        check_result "WARN" "PermitRootLogin is enabled ($root_login)" "Set 'PermitRootLogin no' to prevent direct root brute force."
    fi

    # Password Authentication
    pwd_auth=$(grep -Ei '^\s*PasswordAuthentication' "$SSHD_CONFIG" | awk '{print $2}' || echo "default(yes)")
    if [ "$pwd_auth" = "no" ]; then
        check_result "PASS" "PasswordAuthentication is disabled (Key-only SSH)"
    else
        check_result "WARN" "PasswordAuthentication is enabled" "Consider key-based SSH authentication only."
    fi

    # Protocol check
    ssh_proto=$(grep -Ei '^\s*Protocol' "$SSHD_CONFIG" | awk '{print $2}' || echo "2")
    if [ "$ssh_proto" = "2" ]; then
        check_result "PASS" "SSH Protocol 2 enforced"
    else
        check_result "FAIL" "Insecure SSH Protocol: $ssh_proto" "Enforce Protocol 2."
    fi
else
    check_result "WARN" "sshd_config file not found in /etc/ssh" "Audit skipped (running in container or non-standard path)"
fi

# 2. SSH Directory Permissions
echo ""
echo -e "${BOLD}2. SSH Key File Permissions Audit${RESET}"
USER_HOME="${HOME}"
SSH_DIR="${USER_HOME}/.ssh"

if [ -d "$SSH_DIR" ]; then
    ssh_dir_perm=$(stat -c "%a" "$SSH_DIR" 2>/dev/null || stat -f "%Lp" "$SSH_DIR" 2>/dev/null || echo "unknown")
    if [ "$ssh_dir_perm" = "700" ]; then
        check_result "PASS" "~/.ssh directory permissions are 700"
    else
        check_result "WARN" "~/.ssh directory permissions are $ssh_dir_perm (expected 700)" "Run 'chmod 700 ~/.ssh'"
    fi

    AUTH_KEYS="${SSH_DIR}/authorized_keys"
    if [ -f "$AUTH_KEYS" ]; then
        auth_perm=$(stat -c "%a" "$AUTH_KEYS" 2>/dev/null || stat -f "%Lp" "$AUTH_KEYS" 2>/dev/null || echo "unknown")
        if [ "$auth_perm" = "600" ] || [ "$auth_perm" = "644" ]; then
            check_result "PASS" "authorized_keys permissions are safe ($auth_perm)"
        else
            check_result "FAIL" "authorized_keys permissions insecure: $auth_perm" "Run 'chmod 600 ~/.ssh/authorized_keys'"
        fi
    fi
else
    check_result "PASS" "No local user .ssh directory to audit"
fi

# 3. Host Firewall Status (UFW / iptables)
echo ""
echo -e "${BOLD}3. Firewall Inspection${RESET}"
if command -v ufw >/dev/null 2>&1; then
    ufw_status=$(ufw status 2>/dev/null | grep -i "Status:" | awk '{print $2}' || echo "unknown")
    if [ "$ufw_status" = "active" ]; then
        check_result "PASS" "UFW Firewall is active"
    else
        check_result "WARN" "UFW Firewall is inactive" "Enable UFW with 'ufw enable' after allowing SSH."
    fi
else
    check_result "WARN" "UFW firewall is not installed" "Install and configure ufw or nftables."
fi

# 4. Open Network Ports Exposure
echo ""
echo -e "${BOLD}4. Listening Sockets Exposure (ss -tuln)${RESET}"
if command -v ss >/dev/null 2>&1; then
    insecure_ports=$(ss -tuln 2>/dev/null | grep -E ':(21|23|25|110|143) ' || true)
    if [ -z "$insecure_ports" ]; then
        check_result "PASS" "No legacy insecure plain-text services detected (Telnet, FTP, unencrypted POP/IMAP)"
    else
        check_result "WARN" "Detected potentially unencrypted services listening" "$insecure_ports"
    fi
else
    check_result "WARN" "ss utility not available"
fi

# 5. SUID and World-Writable Check
echo ""
echo -e "${BOLD}5. File System Privileges${RESET}"
if [ -w "/etc/shadow" ] 2>/dev/null; then
    check_result "FAIL" "/etc/shadow is writable by current user!" "CRITICAL security misconfiguration"
else
    check_result "PASS" "/etc/shadow is properly protected"
fi

if [ -w "/etc/passwd" ] 2>/dev/null && [ "$(id -u)" -ne 0 ]; then
    check_result "FAIL" "/etc/passwd is writable by non-root user!"
else
    check_result "PASS" "/etc/passwd is read-only for standard users"
fi

# Summary Score
echo ""
echo -e "${BOLD}${CYAN}================================================================${RESET}"
echo -e "${BOLD}Audit Summary:${RESET} ${PASSED_CHECKS}/${TOTAL_CHECKS} Passed | ${WARNINGS} Warnings"
SCORE=$(( (PASSED_CHECKS * 100) / (TOTAL_CHECKS > 0 ? TOTAL_CHECKS : 1) ))
echo -e "Security Hardening Score: ${BOLD}${SCORE}%${RESET}"
echo -e "${BOLD}${CYAN}================================================================${RESET}"
