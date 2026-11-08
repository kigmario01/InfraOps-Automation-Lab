# Guía de Preparación para Entrevistas Técnicas
## SysAdmin Junior & DevOps Junior

Esta guía contiene preguntas y respuestas técnicas basadas en la experiencia práctica desarrollada en el proyecto **InfraOps Automation Lab**.

---

### 1. ¿Qué es la idempotencia en Ansible y por qué es fundamental?
> **Respuesta:**  
> La idempotencia es la propiedad de una operación por la cual ejecutarla múltiples veces produce exactamente el mismo resultado final en el sistema que ejecutarla una sola vez, sin provocar efectos secundarios no deseados.  
> En este proyecto, los playbooks y roles de Ansible verifican primero si un paquete está instalado, un usuario ya existe o una configuración de `sshd_config` ya coincide. Si el estado ya es el deseado, Ansible no realiza ningún cambio (`ok`), protegiendo la estabilidad del servidor.

---

### 2. ¿Cómo diagnosticaste el rendimiento y recursos en tu servidor Linux?
> **Respuesta:**  
> Implementé tanto scripts en Bash como una herramienta CLI modular en Python (`infraops_cli.py`):
> - **CPU:** Con `top -bn1` y cálculo de idle/load average a 1, 5 y 15 minutos en `/proc/loadavg`.
> - **Memoria:** Analizando MemTotal vs MemAvailable desde `/proc/meminfo` o mediante `free -h`.
> - **Disco:** Evaluando porcentaje de uso e inodos con `df -h /` y `df -i`.
> - **Red:** Verificando sockets en escucha con `ss -tuln` y midiendo latencia TCP/DNS hacia puertas de enlace y DNS públicos.

---

### 3. ¿Por qué separaste los scripts en Bash y herramientas en Python?
> **Respuesta:**  
> - **Bash:** Es ideal para tareas inmediatas a nivel de sistema operativo (verificaciones de arranque, rotación de respaldos con tar/gzip/sha256, pipes rápidos con comandos UNIX como `awk`, `grep` y `sed`).
> - **Python:** Es ideal para lógica estructurada: parseo de JSON, generación de reportes ejecutivos en HTML/Markdown, manejo de sockets TCP con timeouts exactos, cálculo de fechas de expiración de certificados SSL y despacho de alertas a Webhooks HTTP.

---

### 4. ¿Qué medidas de seguridad básica aplicaste en el servidor?
> **Respuesta:**  
> 1. **SSH Hardening:** Deshabilité el login directo de `root` (`PermitRootLogin no`) y la autenticación por contraseña (`PasswordAuthentication no`), exigiendo llaves SSH (ed25519/rsa).
> 2. **Permisos de archivo:** Forcé permisos `0700` en `~/.ssh` y `0600` en `authorized_keys`.
> 3. **Firewall:** Configuré `ufw` con política por defecto `deny incoming`, abriendo explícitamente solo los puertos de servicio (SSH:22, Web:8080, Observabilidad:3001).
> 4. **Fail2ban:** Monitoreo activo contra ataques de fuerza bruta en los logs de autenticación.
> 5. **Sysctl Kernel Hardening:** Deshabilitación de redirecciones ICMP y activación de TCP SYN cookies contra ataques SYN flood.

---

### 5. ¿Cómo aseguraste la continuidad del negocio y qué estrategia de respaldo usaste?
> **Respuesta:**  
> Desarrollé el script `backup_automation.sh` con los siguientes controles de nivel empresarial:
> - **Lockfile:** Previene ejecuciones simultáneas mediante `/tmp/infraops_backup.lock`.
> - **Verificación:** Inmediatamente después de empaquetar, ejecuta `tar -tzf` para garantizar que el archivo comprimido no esté corrupto y genera un hash `SHA-256`.
> - **Retención:** Purga automáticamente archivos con más de 7 días (`find -mtime +7`).
> - **Simulacro de restauración:** Cuenta con un comando `--restore` para verificar la recuperación en directorios de prueba.

---

### 6. ¿Cómo implementaste el flujo de Integración Continua (CI)?
> **Respuesta:**  
> Mediante GitHub Actions (`.github/workflows/ci.yml`), cada push o pull request ejecuta:
> 1. `flake8` para calidad y estilo de código Python.
> 2. `pytest` con cobertura de código para los diagnósticos y chequeadores de red.
> 3. `shellcheck` sobre todos los scripts Bash para detectar variables no declaradas o pipes inseguros.
> 4. `ansible-playbook --syntax-check` para prevenir fallos sintácticos en los playbooks.
> 5. `docker compose config` para validar la sintaxis de los archivos de contenedores.
