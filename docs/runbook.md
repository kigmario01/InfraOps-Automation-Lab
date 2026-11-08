# Runbook Operativo & Procedimientos de Mantenimiento

Este runbook describe los procedimientos estándar de operación (SOPs), diagnóstico de incidencias y recuperación ante desastres en **InfraOps Automation Lab**.

---

## 1. Procedimiento de Diagnóstico Rápido

Cuando se sospeche de lentitud, caída de servicios o alertas de monitoreo, sigue esta secuencia de triage:

1. **Ejecutar chequeo de salud en el nodo:**
   ```bash
   bash bash/health_check.sh
   ```
   *Interpretación:*
   - `Exit 0 (OK)`: Todos los recursos y servicios operan dentro de los umbrales normales.
   - `Exit 1 (WARNING)`: Algún recurso (CPU, RAM o Disco) supera el 75-80%. Monitorear tendencia.
   - `Exit 2 (CRITICAL)`: Saturación crítica (>90%) o contenedores reiniciándose constantemente.

2. **Generar informe ejecutivo de diagnóstico:**
   ```bash
   python python/infraops_cli.py report --output-dir reports
   ```
   Abre `reports/report.html` en el navegador para inspeccionar procesos principales y uso de disco.

3. **Verificar estado de los contenedores Docker:**
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   docker logs --tail 50 <nombre_contenedor>
   ```

---

## 2. Auditoría de Seguridad Perimetral

Para validar que no se hayan modificado permisos críticos ni abierto puertos no autorizados:

```bash
bash bash/security_audit.sh
```

El script evaluará:
- Restricción de acceso `root` por SSH (`PermitRootLogin no`).
- Desactivación de autenticación por contraseña (`PasswordAuthentication no`).
- Permisos del directorio `~/.ssh` (700) y `authorized_keys` (600).
- Estado del cortafuegos `ufw` y puertos expuestos.

---

## 3. Procedimiento de Respaldo y Simulacro de Restauración (DR Drill)

### Ejecución de Respaldo Manual
```bash
bash bash/backup_automation.sh --backup
```
El archivo resultante se ubicará en `./backups/infraops_backup_YYYYMMDD_HHMMSS.tar.gz`.

### Verificación de Integridad
```bash
bash bash/backup_automation.sh --verify ./backups/<archivo_backup>.tar.gz
```

### Simulacro de Restauración en Carpeta Aislada
```bash
bash bash/backup_automation.sh --restore ./backups/<archivo_backup>.tar.gz ./test_restore
```

---

## 4. Gestión de Cambios con Ansible (Dry-Run e Idempotencia)

Antes de aplicar cualquier cambio sobre el servidor de producción:

1. **Validación sintáctica:**
   ```bash
   ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/site.yml --syntax-check
   ```

2. **Modo Dry-Run (Check Mode):**
   ```bash
   ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/site.yml --check --diff
   ```
   *Nota:* Muestra los cambios previstos sin alterar el sistema operativo.

3. **Aplicación controlada por etiquetas (tags):**
   ```bash
   ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/site.yml --tags "security"
   ```
