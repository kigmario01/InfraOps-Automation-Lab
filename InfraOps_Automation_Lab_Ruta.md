# InfraOps Automation Lab

## Ruta práctica de aprendizaje y proyecto de portafolio

**Objetivo:** construir una infraestructura empresarial pequeña,
funcional y automatizada que permita administrar, configurar, desplegar,
supervisar y mantener servidores Linux mediante herramientas de
automatización.

El proyecto está orientado a fortalecer un perfil junior en:

-   Administración de sistemas Linux (SysAdmin).
-   Infraestructura TI.
-   DevOps junior.
-   Administración de servidores.
-   Automatización de infraestructura.

La idea es demostrar habilidades mediante un laboratorio funcional y
documentado en GitHub, no limitarse a enumerar cursos o herramientas.

------------------------------------------------------------------------

## 1. Descripción del proyecto

**Nombre:** InfraOps Automation Lab

**Propósito:** automatizar tareas habituales de administración de
infraestructura, reducir intervenciones manuales y verificar que los
servidores y servicios mantengan una configuración esperada.

### Funcionalidades objetivo

1.  Inventario de servidores y recursos.
2.  Administración remota mediante SSH.
3.  Instalación y configuración automatizada de paquetes.
4.  Creación de usuarios, grupos y permisos.
5.  Aplicación de configuraciones básicas de seguridad.
6.  Despliegue de servicios mediante Docker Compose.
7.  Diagnóstico de CPU, memoria, disco y conectividad.
8.  Monitoreo de disponibilidad y alertas.
9.  Generación de informes de infraestructura.
10. Validaciones automáticas del código y las configuraciones.

### Stack tecnológico

  -----------------------------------------------------------------------
  Tecnología                          Uso en el proyecto
  ----------------------------------- -----------------------------------
  Ubuntu Server                       Sistema operativo de los nodos

  Ansible                             Automatización y configuración de
                                      servidores

  Python                              Scripts de diagnóstico,
                                      comprobación y reportes

  Bash                                Automatización de tareas del
                                      sistema

  Docker / Docker Compose             Despliegue de servicios

  SSH                                 Administración remota segura

  Git / GitHub                        Control de versiones y portafolio

  GitHub Actions                      Validaciones automáticas (CI)

  Zabbix o herramienta equivalente    Monitoreo y alertas

  NetBox (fase opcional)              Inventario de infraestructura y
                                      direcciones IP
  -----------------------------------------------------------------------

**Orden recomendado:** comenzar con Linux y Ansible; después incorporar
Python y Docker; finalmente, monitoreo y CI. No es necesario instalar
todas las herramientas desde el primer día.

------------------------------------------------------------------------

## 2. Arquitectura del laboratorio

La primera versión debe aprovechar el servidor Ubuntu existente y los
servicios Docker que ya estén desplegados. Debido a que el equipo
dispone de recursos limitados, se debe medir el consumo antes de
incorporar nuevos contenedores o máquinas virtuales.

### Componentes

  Componente       Responsabilidad
  ---------------- ----------------------------------------------
  Ubuntu Server    Nodo inicial de control y administración
  Ansible          Ejecutar configuraciones y tareas repetibles
  Python           Ejecutar diagnósticos y generar informes
  Docker           Ejecutar servicios aislados
  SSH              Conectar con los servidores administrados
  GitHub           Almacenar código y documentación
  GitHub Actions   Ejecutar comprobaciones automatizadas

A medida que el laboratorio crezca, se puede agregar un segundo servidor
Linux de pruebas, preferiblemente virtualizado o en otro equipo. No se
debe asumir que el servidor principal tiene recursos suficientes para
ejecutar todas las herramientas simultáneamente.

### Principio de seguridad

No modificar indiscriminadamente el servidor principal. El trabajo se
realizará por etapas:

1.  Inventariar el estado actual.
2.  Ejecutar diagnósticos de solo lectura.
3.  Probar cambios en un entorno controlado.
4.  Aplicar cambios pequeños y verificables.
5.  Documentar cómo validar y revertir cada cambio.

No almacenar contraseñas, tokens, claves privadas ni secretos en el
repositorio. Para gestionar secretos de Ansible se incorporará Ansible
Vault cuando corresponda.

------------------------------------------------------------------------

## 3. Ruta práctica de cuatro semanas

Cada misión está pensada para durar entre **20 y 40 minutos** y producir
un resultado comprobable. Si aparece un error real, se detiene la misión
y se diagnostica antes de continuar.

### Semana 1 --- Administración Linux

**Objetivo:** preparar y comprender la infraestructura que se va a
administrar.

  -----------------------------------------------------------------------
  Misión                  Actividad               Resultado esperado
  ----------------------- ----------------------- -----------------------
  1                       Identificar recursos,   Inventario técnico
                          servicios y             inicial
                          configuración del       
                          servidor                

  2                       Administrar usuarios,   Ejercicios documentados
                          grupos y permisos       de permisos

  3                       Automatizar tareas con  Primer script funcional
                          Bash                    

  4                       Revisar SSH y seguridad Acceso remoto
                          básica                  verificado y medidas
                                                  documentadas
  -----------------------------------------------------------------------

### Semana 2 --- Ansible

**Objetivo:** administrar servidores sin repetir manualmente las mismas
tareas.

  -----------------------------------------------------------------------
  Misión                  Actividad               Resultado esperado
  ----------------------- ----------------------- -----------------------
  5                       Instalar y configurar   Entorno de control
                          Ansible                 funcional

  6                       Crear inventarios de    Inventario de hosts
                          servidores              

  7                       Crear playbooks para    Primer playbook
                          instalar y configurar   ejecutable
                          servicios               

  8                       Implementar roles y     Automatización
                          validar idempotencia    reutilizable
  -----------------------------------------------------------------------

**Concepto clave:** un playbook idempotente puede ejecutarse varias
veces y mantiene el estado deseado sin realizar cambios innecesarios
cuando el sistema ya está configurado correctamente.

### Semana 3 --- Python y Docker

**Objetivo:** construir herramientas propias para administrar
infraestructura.

  -----------------------------------------------------------------------
  Misión                  Actividad               Resultado esperado
  ----------------------- ----------------------- -----------------------
  9                       Crear un script Python  Diagnóstico de recursos
                          para diagnosticar el    
                          servidor                

  10                      Consultar               Comprobación de
                          disponibilidad de       conectividad
                          servicios               

  11                      Automatizar despliegues Servicio desplegado de
                          con Docker Compose      forma reproducible

  12                      Generar informes de     Reporte legible y
                          infraestructura         verificable
  -----------------------------------------------------------------------

### Semana 4 --- Monitoreo y DevOps

**Objetivo:** convertir el laboratorio en un proyecto demostrable.

  -----------------------------------------------------------------------
  Misión                  Actividad               Resultado esperado
  ----------------------- ----------------------- -----------------------
  13                      Integrar monitoreo de   Métricas visibles
                          infraestructura         

  14                      Configurar alertas      Notificación ante una
                                                  condición definida

  15                      Crear pruebas           Flujo CI funcional
                          automáticas con GitHub  
                          Actions                 

  16                      Documentar arquitectura Repositorio listo para
                          y resultados            revisión
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 4. Estructura propuesta del repositorio

``` text
InfraOps-Automation-Lab/
│
├── ansible/
│   ├── inventory/
│   ├── playbooks/
│   ├── roles/
│   └── ansible.cfg
│
├── python/
│   ├── monitoring/
│   ├── diagnostics/
│   └── reports/
│
├── bash/
│   ├── backups.sh
│   └── health_check.sh
│
├── docker/
│   └── compose.yaml
│
├── monitoring/
│
├── tests/
│
├── .github/
│   └── workflows/
│
├── docs/
│   ├── architecture.md
│   ├── installation.md
│   └── evidence/
│
├── .gitignore
└── README.md
```

La estructura puede evolucionar a medida que se implementen las
funcionalidades. No es necesario crear carpetas vacías desde el inicio.

### Contenido mínimo del README

-   Descripción y objetivos del proyecto.
-   Diagrama de arquitectura.
-   Tecnologías y versiones utilizadas.
-   Requisitos previos.
-   Instrucciones de instalación y ejecución.
-   Ejemplos de comandos.
-   Pruebas realizadas y resultados.
-   Capturas o evidencias de funcionamiento.
-   Limitaciones conocidas y mejoras futuras.

------------------------------------------------------------------------

## 5. Competencias que el proyecto permitirá demostrar

Estas competencias solo deben agregarse al CV cuando estén implementadas
y puedas explicar su funcionamiento.

  Competencia        Evidencia verificable
  ------------------ ---------------------------------------------
  Linux Server       Administración y configuración documentadas
  Ansible            Inventarios, roles y playbooks funcionales
  Python             Scripts propios de diagnóstico
  Bash               Automatización de tareas del sistema
  Docker             Servicios desplegados con Compose
  GitHub Actions     Validaciones automáticas ejecutadas
  SSH                Administración remota segura
  Monitoreo          Métricas, paneles y alertas comprobadas
  Seguridad básica   Controles y configuraciones documentados

### Ejemplo de descripción para el CV

> Desarrollo de laboratorio de automatización de infraestructura TI
> mediante Ansible, Python y Docker, implementando administración de
> servidores Linux, despliegue automatizado de servicios, diagnóstico de
> infraestructura, monitoreo y validación de configuraciones.

Ajustar esta descripción a las funcionalidades realmente terminadas. No
presentar como experiencia laboral una práctica personal o académica;
identificarla como proyecto de portafolio.

------------------------------------------------------------------------

## 6. Primera misión: inventario técnico del servidor

**Duración estimada:** 30 minutos.

**Objetivo:** identificar los recursos disponibles y los servicios
activos antes de instalar o modificar componentes.

Ejecutar los siguientes comandos en el servidor Ubuntu:

``` bash
echo "=== SISTEMA ==="
hostnamectl

echo "=== RECURSOS ==="
free -h
df -h /

echo "=== PROCESADOR ==="
lscpu | grep -E 'Model name|CPU\\(s\\)'

echo "=== SERVICIOS DOCKER ==="
docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
```

### Qué se busca identificar

-   Sistema operativo y versión.
-   Memoria disponible y utilizada.
-   Espacio libre en disco.
-   Modelo y cantidad de CPU.
-   Contenedores activos, estado y puertos publicados.
-   Posibles limitaciones o conflictos antes de desplegar herramientas
    adicionales.

### Criterio de aceptación

La misión se considera terminada cuando:

1.  Se recopilaron los resultados de todos los comandos.
2.  Se documentó el inventario técnico.
3.  Se identificaron los servicios que no deben interrumpirse.
4.  Se determinó dónde ejecutar Ansible sin afectar las aplicaciones
    existentes.

**No instalar ni modificar nada durante esta primera misión.** Compartir
los resultados para revisarlos antes de continuar.

------------------------------------------------------------------------

## 7. Criterios de calidad del proyecto

Cada automatización nueva debe cumplir, en la medida que corresponda,
con estos criterios:

-   **Repetibilidad:** poder ejecutar el procedimiento más de una vez.
-   **Idempotencia:** evitar cambios innecesarios cuando el estado ya es
    correcto.
-   **Validación:** comprobar que la tarea produjo el resultado
    esperado.
-   **Manejo de errores:** informar fallos de forma clara y no
    ocultarlos.
-   **Seguridad:** proteger credenciales, limitar privilegios y evitar
    exponer servicios innecesariamente.
-   **Trazabilidad:** registrar cambios y utilizar commits pequeños.
-   **Documentación:** explicar requisitos, ejecución, resultados y
    reversión.
-   **Pruebas:** verificar los scripts y playbooks antes de aplicarlos
    en el servidor principal.

### Convención de commits sugerida

Usar Conventional Commits, por ejemplo:

``` text
feat: add initial server inventory
feat: add linux health check script
feat: configure ansible inventory
fix: correct service availability check
docs: document lab architecture
test: validate ansible playbooks
```

------------------------------------------------------------------------

## 8. Resultado final esperado

Al completar la primera versión del laboratorio deberás poder demostrar,
en una entrevista técnica:

1.  Cómo inventariar un servidor Linux.
2.  Cómo administrar un servidor remotamente mediante SSH.
3.  Cómo automatizar configuraciones con Ansible.
4.  Cómo desarrollar scripts de administración con Python y Bash.
5.  Cómo desplegar servicios mediante Docker Compose.
6.  Cómo verificar disponibilidad y detectar fallos.
7.  Cómo documentar y versionar la infraestructura.
8.  Cómo validar cambios antes de aplicarlos.

**La prioridad es terminar un laboratorio pequeño, estable y bien
documentado.** Es preferible demostrar cuatro automatizaciones
funcionales y verificables que presentar diez herramientas instaladas
sin una integración clara.
