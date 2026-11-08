# Arquitectura del Laboratorio: InfraOps Automation Lab

Este documento detalla el diseño de arquitectura, los flujos de comunicación y los componentes de automatización implementados en **InfraOps Automation Lab**.

---

## 1. Visión General de la Arquitectura

El laboratorio está diseñado siguiendo el principio de **separación de responsabilidades** y **consumo eficiente de recursos**, permitiendo administrar tanto servidores físicos como instancias virtualizadas o contenedores de prueba.

```mermaid
graph TD
    subgraph Control_Station["Nodo de Control / Estación DevOps"]
        CLI["infraops CLI (Python 3)"]
        AnsibleCtrl["Ansible Engine (Playbooks & Roles)"]
        GitRepo["Git Repository & CI (GitHub Actions)"]
    end

    subgraph Managed_Node["Servidor Linux Administrado (Ubuntu Server)"]
        SSH["OpenSSH Server (Port 22 Hardened)"]
        UFW["Firewall UFW & Fail2ban"]
        Cron["Cron Daemon (Backups automáticos)"]
        
        subgraph Docker_Runtime["Docker Engine & Compose Stack"]
            WebApp["Nginx Web App (/healthz) - Port 8080"]
            UptimeKuma["Uptime Kuma (Observabilidad) - Port 3001"]
            NodeExp["Node Exporter (Telemetría) - Port 9100"]
        end
    end

    subgraph Alerts_Channel["Canales de Notificación"]
        Webhook["Webhooks (Discord / Slack / Telegram)"]
    end

    AnsibleCtrl -->|SSH / Puertos 22/2222| SSH
    CLI -->|HTTP Probes / TCP Sockets| WebApp
    CLI -->|Status & Latencia| UptimeKuma
    CLI -->|Host Metrics| NodeExp
    CLI -->|Alerta en fallo| Webhook
    Cron -->|Tar + SHA256 + Rotación| Managed_Node
```

---

## 2. Componentes del Stack

| Componente | Rol en la Infraestructura | Tecnologías |
| :--- | :--- | :--- |
| **Control & Orquestación** | Ejecutar configuraciones declarativas e idempotentes. | Ansible 2.15+, Python 3.10+ |
| **Seguridad Perimetral** | Restringir accesos, prevenir ataques de fuerza bruta y bloquear puertos no autorizados. | UFW, Fail2ban, SSH Hardening |
| **Servicios Desplegados** | Aplicación web proxy y panel de observabilidad de bajo consumo (<250MB RAM). | Docker Compose, Nginx Alpine, Uptime Kuma |
| **Motor de Diagnóstico** | Inspección en tiempo real de CPU, RAM, discos, sockets y certificados SSL. | Python Standard Library (`sys_diagnostics`, `network_probe`) |
| **Observabilidad & Alertas** | Monitoreo sintético de endpoints y alertas automáticas vía Webhooks. | `service_checker.py`, `alert_manager.py` |
| **Continuidad del Negocio** | Respaldo comprimido con suma criptográfica SHA256 y retención de 7 días. | `backup_automation.sh` |

---

## 3. Flujo de Trabajo de Automatización (Ansible)

El despliegue sigue un ciclo escalonado que garantiza la estabilidad del sistema antes de aplicar configuraciones avanzadas:

```mermaid
sequenceDiagram
    autonumber
    participant Admin as SysAdmin / CI
    participant Ansible as Ansible Playbook
    participant Node as Servidor Ubuntu
    participant Docker as Docker Engine

    Admin->>Ansible: ansible-playbook site.yml
    Ansible->>Node: 01_system_bootstrap (Paquetes base, usuario sysadmin, sudo)
    Node-->>Ansible: Estado verificado (Idempotente)
    Ansible->>Node: 02_security_hardening (UFW, Fail2ban, sshd_config restricted)
    Node-->>Ansible: Reglas de firewall activas
    Ansible->>Node: 03_docker_setup (Docker CE, containerd, daemon.json)
    Node->>Docker: Inicializa servicio Docker
    Ansible->>Docker: 04_app_deploy (Docker Compose up -d)
    Docker-->>Ansible: Contenedores saludables (healthy)
    Ansible->>Node: 05_backup_config (Cron de respaldo programado)
    Ansible-->>Admin: Ejecución Exitosa (0 Fallos)
```

---

## 4. Estrategia de Respaldo y Recuperación (DRP)

1. **Captura:** Cada ejecución respalda la configuración de Docker Compose, variables de entorno y datos persistentes.
2. **Compresión:** Genera un archivo tarball comprimido con `gzip` (`infraops_backup_YYYYMMDD_HHMMSS.tar.gz`).
3. **Verificación:** Inmediatamente valida la integridad del archivo mediante `tar -tzf` y calcula el hash `SHA-256`.
4. **Rotación:** Aplica política de retención automática purgando respaldos con más de 7 días de antigüedad.
5. **Recuperación:** Soporta comando de restauración automatizado (`backup_automation.sh --restore <archivo> <destino>`).
