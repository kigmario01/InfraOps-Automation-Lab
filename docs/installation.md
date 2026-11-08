# Guía de Instalación y Puesta en Marcha

Esta guía proporciona las instrucciones paso a paso para desplegar **InfraOps Automation Lab** en un servidor Ubuntu real, en una máquina virtual local, o usando el entorno simulado (Sandbox con Docker).

---

## 1. Requisitos Previos

- **Nodo de Control (tu máquina o estación de trabajo):**
  - Python 3.10 o superior.
  - Git.
  - Ansible (para entornos Linux/WSL/macOS).
  - Docker & Docker Compose (opcional para correr sandbox o servicios locales).
- **Servidor Destino (Nodo administrado):**
  - Ubuntu Server 20.04 / 22.04 / 24.04 LTS.
  - Acceso SSH con usuario con privilegios `sudo`.
  - Conexión a Internet para descargar paquetes.

---

## 2. Preparación del Entorno Local

1. Clona el repositorio:
   ```bash
   git clone <URL_DEL_REPOSITORIO> InfraOps-Automation-Lab
   cd InfraOps-Automation-Lab
   ```

2. Crea y activa un entorno virtual de Python:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias de Python:
   ```bash
   pip install -r requirements.txt
   ```

---

## 3. Opción A: Despliegue en Servidor Ubuntu Real

1. Configura la dirección IP de tu servidor en el inventario:
   Edita `ansible/inventory/hosts.ini`:
   ```ini
   [managed_nodes]
   mi-servidor ansible_host=192.168.1.100 ansible_user=sysadmin ansible_ssh_private_key_file=~/.ssh/id_ed25519
   ```

2. Verifica la conectividad con Ansible:
   ```bash
   ansible all -i ansible/inventory/hosts.ini -m ping
   ```

3. Ejecuta el orquestador completo:
   ```bash
   ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/site.yml
   ```

4. Ejecuta el inventario técnico y diagnóstico:
   ```bash
   bash bash/01_server_inventory.sh
   python python/infraops_cli.py report --output-dir reports
   ```

---

## 4. Opción B: Uso del Entorno de Pruebas (Docker Sandbox)

Si no dispones de un segundo servidor físico, puedes levantar dos nodos Ubuntu virtuales completos con SSH:

1. Inicia el sandbox con Docker Compose:
   ```bash
   make lab-up
   # o: docker compose -f sandbox/docker-compose.lab.yml up -d
   ```

2. Verifica que los nodos estén escuchando:
   ```bash
   ssh -p 2222 sysadmin@localhost  # Password: SysAdminLab2026!
   ```

3. Ejecuta los playbooks de Ansible contra los nodos sandbox:
   ```bash
   ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/site.yml --limit sandbox
   ```

4. Para apagar el laboratorio sandbox:
   ```bash
   make lab-down
   ```

---

## 5. Verificación de Servicios

Una vez completado el despliegue, verifica los servicios en los siguientes puertos:
- **Nginx Web Landing:** `http://<IP_SERVIDOR>:8080`
- **Health Endpoint:** `http://<IP_SERVIDOR>:8080/healthz`
- **Uptime Kuma Dashboard:** `http://<IP_SERVIDOR>:3001`
- **Node Exporter Metrics:** `http://<IP_SERVIDOR>:9100/metrics`
