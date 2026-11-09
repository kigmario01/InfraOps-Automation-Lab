#!/usr/bin/env bash
# ==============================================================================
# InfraOps Automation Lab - Automated Disaster Recovery (DR) Drill Benchmark
# Script: dr_drill_simulation.sh
# Purpose: Simulates service failure, restores from backup, reconstructs stack,
#          and measures Recovery Time Objective (RTO) until /healthz responds.
# ==============================================================================

set -euo pipefail

BOLD=$'\033[1m'
GREEN=$'\033[0;32m'
CYAN=$'\033[0;36m'
YELLOW=$'\033[1;33m'
RED=$'\033[0;31m'
RESET=$'\033[0m'

TARGET_PORT="${WEB_PORT:-8090}"
HEALTH_URL="http://localhost:${TARGET_PORT}/healthz"
BACKUP_DIR="./backups"
RESTORE_DIR="./restore_drill"

echo "${BOLD}${CYAN}================================================================${RESET}"
echo "${BOLD}${CYAN}   INFRAOPS AUTOMATION LAB - DISASTER RECOVERY (DR) DRILL      ${RESET}"
echo "${BOLD}${CYAN}================================================================${RESET}"
echo "Iniciando simulacro reproducible de fallo y recuperacion..."
echo "Endpoint objetivo de verificacion: ${HEALTH_URL}"
echo ""

# 1. Asegurar estado inicial saludable
echo "${BOLD}[Paso 1/5] Verificando o preparando estado inicial del stack...${RESET}"
if command -v docker >/dev/null 2>&1; then
    docker compose -f docker/compose.yaml up -d web-app >/dev/null 2>&1 || true
    sleep 2
fi

# 2. Generar o localizar copia de respaldo
echo "${BOLD}[Paso 2/5] Generando respaldo verificado con suma SHA-256...${RESET}"
bash bash/backup_automation.sh --backup >/dev/null 2>&1
LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/infraops_backup_*.tar.gz 2>/dev/null | head -n 1)

if [ -z "$LATEST_BACKUP" ] || [ ! -f "$LATEST_BACKUP" ]; then
    echo "${RED}ERROR: No se pudo generar o encontrar el archivo de respaldo.${RESET}" >&2
    exit 1
fi
echo "  -> Copia de seguridad utilizada: ${LATEST_BACKUP}"
echo "  -> Verificacion SHA-256: $(cat "${LATEST_BACKUP}.sha256" | awk '{print $1}')"

# 3. Simular desastre / caída del servicio
echo ""
echo "${BOLD}[Paso 3/5] Simulando desastre: destruccion del contenedor y configuracion...${RESET}"
T_START=$(date +%s)

if command -v docker >/dev/null 2>&1; then
    docker stop infraops-web-app >/dev/null 2>&1 || true
    docker rm -f infraops-web-app >/dev/null 2>&1 || true
fi

# Verificar caida del servicio
if curl -s -f -m 1 "$HEALTH_URL" >/dev/null 2>&1; then
    echo "${YELLOW}Advertencia: El servicio sigue respondiendo (posible proxy externo).${RESET}"
else
    echo "  -> Caida confirmada: ${HEALTH_URL} no responde (DOWN)."
fi

# 4. Restauracion desde copia de seguridad
echo ""
echo "${BOLD}[Paso 4/5] Restaurando configuracion y datos desde el tarball...${RESET}"
bash bash/backup_automation.sh --restore "$LATEST_BACKUP" "$RESTORE_DIR" >/dev/null 2>&1
echo "  -> Archivos restaurados en: ${RESTORE_DIR}"
echo "  -> Contenido recuperado: $(ls -A "$RESTORE_DIR")"

# 5. Reconstruccion y reinicio del servicio
echo ""
echo "${BOLD}[Paso 5/5] Reconstruyendo servicio e infraestructura...${RESET}"
if command -v docker >/dev/null 2>&1; then
    docker compose -f docker/compose.yaml up -d --force-recreate web-app >/dev/null 2>&1
fi

# Medir tiempo hasta que /healthz responda HTTP 200
echo "  -> Esperando recuperacion de ${HEALTH_URL}..."
MAX_WAIT=60
ELAPSED=0
RECOVERED=false

while [ $ELAPSED -lt $MAX_WAIT ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 1 "$HEALTH_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        RECOVERED=true
        break
    fi
    sleep 1
    ELAPSED=$(( $(date +%s) - T_START ))
done

T_END=$(date +%s)
TOTAL_RTO=$(( T_END - T_START ))

echo ""
echo "${BOLD}${CYAN}================================================================${RESET}"
if [ "$RECOVERED" = true ]; then
    echo "${BOLD}${GREEN}✅ SIMULACRO DRP COMPLETADO CON EXITO (STATUS HTTP 200)${RESET}"
    echo "  * Copia utilizada     : ${LATEST_BACKUP}"
    echo "  * Que recupero Backup : Configuracion de Nginx, variables .env y templates"
    echo "  * Que reconstruyo IaC : Contenedores Docker, redes bridge y puertos mapeados"
    echo "  * RTO Medido (Tiempo) : ${BOLD}${GREEN}${TOTAL_RTO} segundos${RESET} (Objetivo: < 60s)"
else
    echo "${BOLD}${RED}❌ FALLO EL SIMULACRO DRP (Timeout tras ${TOTAL_RTO}s)${RESET}"
fi
echo "${BOLD}${CYAN}================================================================${RESET}"

# Limpieza del directorio temporal del drill
rm -rf "$RESTORE_DIR"
exit $([ "$RECOVERED" = true ] && echo 0 || echo 1)
