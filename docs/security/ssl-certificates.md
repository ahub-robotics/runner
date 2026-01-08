# 🏢 Certificate Authority (CA) - Robot Runner

Sistema de certificados SSL basado en CA propia para conexiones HTTPS seguras entre robots y orquestador.

## 📋 Índice

1. [Descripción general](#descripción-general)
2. [Estructura de archivos](#estructura-de-archivos)
3. [Configuración inicial (una vez)](#configuración-inicial-una-vez)
4. [Agregar nuevo robot](#agregar-nuevo-robot)
5. [Configurar orquestador](#configurar-orquestador)
6. [Operaciones comunes](#operaciones-comunes)
7. [Solución de problemas](#solución-de-problemas)

---

## 📖 Descripción general

### ¿Por qué usar CA propia?

**Con CA:**
- ✅ Un solo certificado en el orquestador (ca-cert.pem)
- ✅ Cada robot tiene su propio certificado con su IP
- ✅ Agregar robots: NO requiere actualizar orquestador
- ✅ Cambiar IPs: Solo regenerar cert del robot afectado
- ✅ Escalable a infinitos robots

**Sin CA (método anterior):**
- ❌ Certificado compartido con todas las IPs
- ❌ Agregar robot: Actualizar orquestador
- ❌ Cambiar IP: Regenerar y redistribuir todo
- ❌ No escalable

### Conceptos clave

```
┌─────────────────┐
│   CA Raíz       │  ← Autoridad que firma certificados
│   ca-cert.pem   │    (creada UNA VEZ)
│   ca-key.pem    │
└────────┬────────┘
         │ Firma cada certificado
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐
│Robot 1 │ │Robot2│ │Robot 3 │ │Robot N │
│cert.pem│ │cert  │ │cert    │ │cert    │
│IP:.100 │ │.200  │ │.50     │ │.xxx    │
└────────┘ └──────┘ └────────┘ └────────┘

┌──────────────────────────────────┐
│      Orquestador                 │
│  Solo tiene: ca-cert.pem         │
│  → Confía en TODOS los robots    │
│    firmados por esa CA           │
└──────────────────────────────────┘
```

---

## 📁 Estructura de archivos

```
robotrunner_windows/
├── ca-key.pem                 # 🔐 Clave privada CA (CRÍTICO - GUARDAR SEGURO)
├── ca-cert.pem                # 📜 Certificado público CA (compartir con orquestador)
├── ca-cert.srl                # 📋 Serial numbers (autogenerado)
├── ca-config.cnf              # ⚙️  Configuración CA
├── CA-INFO.txt                # 📄 Información de la CA
│
├── cert.pem                   # 📜 Certificado del robot actual
├── key.pem                    # 🔐 Clave privada del robot actual
│
├── certs/                     # 📁 Certificados generados
│   ├── robot-1/
│   │   ├── robot-1-cert.pem
│   │   ├── robot-1-key.pem
│   │   ├── robot-1.csr
│   │   ├── openssl.cnf
│   │   └── CERT-INFO.txt
│   ├── robot-2/
│   └── robot-3/
│
├── create_ca.sh               # 🛠️ Script: Crear CA (ejecutar UNA VEZ)
├── generate_robot_cert.sh     # 🛠️ Script: Generar cert de robot
└── CA-README.md               # 📖 Esta documentación
```

---

## 🚀 Configuración inicial (una vez)

### Paso 1: Crear la Certificate Authority

```bash
./create_ca.sh
```

**Resultado:**
- `ca-key.pem` - Clave privada de la CA (¡MANTENER SEGURA!)
- `ca-cert.pem` - Certificado público de la CA

**⚠️ IMPORTANTE:**
- `ca-key.pem` es crítico - guárdalo en un lugar seguro
- Si pierdes `ca-key.pem`, deberás recrear toda la infraestructura
- Haz backup de `ca-key.pem` en múltiples ubicaciones seguras

### Paso 2: Instalar CA en el orquestador

```bash
# Copiar certificado de la CA al orquestador
scp ca-cert.pem user@orchestrator:/opt/certs/robot-ca.pem

# O si el orquestador está en la misma máquina
sudo mkdir -p /opt/certs
sudo cp ca-cert.pem /opt/certs/robot-ca.pem
sudo chmod 644 /opt/certs/robot-ca.pem
```

**Opcional - Instalar a nivel sistema (Linux):**
```bash
# En el servidor del orquestador (Ubuntu/Debian)
sudo cp ca-cert.pem /usr/local/share/ca-certificates/robot-ca.crt
sudo update-ca-certificates

# En el servidor del orquestador (RedHat/CentOS)
sudo cp ca-cert.pem /etc/pki/ca-trust/source/anchors/robot-ca.crt
sudo update-ca-trust
```

### Paso 3: Configurar código del orquestador

```python
import requests

# Configuración global
ROBOT_CA_CERT = '/opt/certs/robot-ca.pem'

# Opción 1: Usar en cada petición
def get_robot_status(robot_ip, machine_id, license_key):
    response = requests.get(
        f'https://{robot_ip}:5055/status',
        params={
            'machine_id': machine_id,
            'license_key': license_key
        },
        verify=ROBOT_CA_CERT  # ← Valida con la CA
    )
    return response.json()

# Opción 2: Usar con Session (más eficiente)
class RobotClient:
    def __init__(self, ca_cert='/opt/certs/robot-ca.pem'):
        self.session = requests.Session()
        self.session.verify = ca_cert

    def get_status(self, robot_ip, machine_id, license_key):
        return self.session.get(
            f'https://{robot_ip}:5055/status',
            params={
                'machine_id': machine_id,
                'license_key': license_key
            }
        ).json()

# Uso
client = RobotClient()
status = client.get_status('192.168.1.100', 'MACHINE_ID', 'LICENSE_KEY')
```

---

## 🤖 Agregar nuevo robot

### Generar certificado para el robot

```bash
# Sintaxis básica
./generate_robot_cert.sh <nombre-robot> <ip-principal> [ip-adicional...]

# Ejemplos
./generate_robot_cert.sh robot-1 192.168.1.100
./generate_robot_cert.sh robot-2 10.0.0.50
./generate_robot_cert.sh robot-3 192.168.1.200 10.0.0.200  # Múltiples IPs
```

**Resultado:**
- Genera certificado único para ese robot
- Copia `cert.pem` y `key.pem` a la raíz del proyecto
- Guarda archivos originales en `certs/robot-X/`

### Empaquetar la aplicación

```bash
# PyInstaller incluye automáticamente cert.pem y key.pem
pyinstaller app.spec
```

**El ejecutable generado contendrá:**
- ✅ `cert.pem` (certificado del robot)
- ✅ `key.pem` (clave privada del robot)
- ✅ Todo el código de la aplicación

### Distribuir

```bash
# El ejecutable está listo para distribuir
# Copia a la máquina del robot y ejecuta

# Ejemplo Windows
RobotRunner.exe

# Ejemplo Linux/Mac
./RobotRunner
```

**🎉 El orquestador NO necesita cambios - funciona automáticamente**

---

## ⚙️ Configurar orquestador

### Archivo de configuración (orquestador)

```python
# config.py
ROBOT_CA_CERT = '/opt/certs/robot-ca.pem'

# orchestrator.py
import requests
from config import ROBOT_CA_CERT

class RobotOrchestrator:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = ROBOT_CA_CERT

    def check_robot(self, robot_ip, machine_id, license_key):
        """Verificar estado de un robot"""
        try:
            response = self.session.get(
                f'https://{robot_ip}:5055/status',
                params={
                    'machine_id': machine_id,
                    'license_key': license_key
                },
                timeout=5
            )
            return response.json()
        except requests.exceptions.SSLError as e:
            print(f"❌ SSL Error con {robot_ip}: {e}")
            return None
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout con {robot_ip}")
            return None
        except Exception as e:
            print(f"❌ Error con {robot_ip}: {e}")
            return None

    def run_robot(self, robot_ip, machine_id, license_key, data):
        """Ejecutar tarea en un robot"""
        response = self.session.post(
            f'https://{robot_ip}:5055/run',
            params={
                'machine_id': machine_id,
                'license_key': license_key
            },
            json=data,
            timeout=10
        )
        return response.json()

# Uso
orchestrator = RobotOrchestrator()

# Funciona con CUALQUIER robot firmado por la CA
status1 = orchestrator.check_robot('192.168.1.100', 'ID1', 'KEY1')
status2 = orchestrator.check_robot('192.168.1.200', 'ID2', 'KEY2')
status3 = orchestrator.check_robot('10.0.0.50', 'ID3', 'KEY3')
```

---

## 🛠️ Operaciones comunes

### Ver información de la CA

```bash
# Ver detalles del certificado de la CA
openssl x509 -in ca-cert.pem -text -noout

# Ver fechas de validez
openssl x509 -in ca-cert.pem -noout -dates

# Ver subject
openssl x509 -in ca-cert.pem -noout -subject

# Ver fingerprint
openssl x509 -in ca-cert.pem -noout -fingerprint -sha256
```

### Ver información de certificado de robot

```bash
# Ver detalles
openssl x509 -in cert.pem -text -noout

# Ver IPs configuradas (SAN)
openssl x509 -in cert.pem -noout -ext subjectAltName

# Verificar cadena de confianza
openssl verify -CAfile ca-cert.pem cert.pem
```

### Regenerar certificado de un robot existente

Si un robot cambia de IP:

```bash
# 1. Generar nuevo certificado con la nueva IP
./generate_robot_cert.sh robot-1 192.168.2.100  # Nueva IP

# 2. Reempaquetar solo ese robot
pyinstaller app.spec

# 3. Redistribuir solo ese robot
# El orquestador NO necesita cambios
```

### Listar todos los certificados generados

```bash
# Listar robots
ls -1 certs/

# Ver información de todos
for robot in certs/*/; do
    echo "=== $(basename $robot) ==="
    cat "${robot}CERT-INFO.txt"
    echo ""
done
```

### Backup de la CA

```bash
# Crear backup de archivos críticos
tar -czf ca-backup-$(date +%Y%m%d).tar.gz \
    ca-key.pem \
    ca-cert.pem \
    ca-cert.srl \
    ca-config.cnf \
    CA-INFO.txt

# Mover a ubicación segura
mv ca-backup-*.tar.gz /path/to/secure/location/
```

---

## 🐛 Solución de problemas

### Error: "certificate verify failed: self signed certificate in certificate chain"

**Causa:** El orquestador no tiene `ca-cert.pem` o no está configurado correctamente.

**Solución:**
```bash
# 1. Verificar que ca-cert.pem existe en el orquestador
ls -l /opt/certs/robot-ca.pem

# 2. Verificar permisos
sudo chmod 644 /opt/certs/robot-ca.pem

# 3. Verificar código
# Debe usar: verify='/opt/certs/robot-ca.pem'
```

### Error: "hostname 'X.X.X.X' doesn't match"

**Causa:** La IP usada para conectar no está en los SAN del certificado del robot.

**Solución:**
```bash
# 1. Ver IPs configuradas en el certificado
openssl x509 -in cert.pem -noout -ext subjectAltName

# 2. Regenerar certificado incluyendo la IP correcta
./generate_robot_cert.sh robot-1 192.168.1.100 10.0.0.50

# 3. Reempaquetar y redistribuir ese robot
```

### Error: "certificate has expired"

**Causa:** El certificado del robot expiró (válido 365 días).

**Solución:**
```bash
# 1. Verificar fecha de expiración
openssl x509 -in cert.pem -noout -enddate

# 2. Regenerar certificado
./generate_robot_cert.sh robot-1 192.168.1.100

# 3. Reempaquetar y redistribuir
```

### Error: "No se encontró la CA" al generar certificado de robot

**Causa:** No existe `ca-key.pem` o `ca-cert.pem`.

**Solución:**
```bash
# Crear la CA primero
./create_ca.sh
```

### La CA expiró (después de 10 años)

**Causa:** La CA tiene validez de 10 años.

**Solución:**
```bash
# 1. Crear nueva CA
./create_ca.sh

# 2. Regenerar TODOS los certificados de robots
for robot_ip in 192.168.1.100 192.168.1.200 10.0.0.50; do
    ./generate_robot_cert.sh robot-X $robot_ip
    # Empaquetar y redistribuir cada uno
done

# 3. Actualizar ca-cert.pem en el orquestador
scp ca-cert.pem user@orchestrator:/opt/certs/robot-ca.pem
```

### Verificar conexión SSL desde línea de comandos

```bash
# Test con openssl
openssl s_client -connect 192.168.1.100:5055 \
    -CAfile ca-cert.pem \
    -showcerts

# Test con curl
curl -v https://192.168.1.100:5055/status \
    --cacert ca-cert.pem \
    --get \
    --data-urlencode "machine_id=TEST" \
    --data-urlencode "license_key=TEST"
```

---

## 📚 Recursos adicionales

### Archivos importantes

- `CA-INFO.txt` - Información de la CA generada
- `certs/robot-X/CERT-INFO.txt` - Información de cada robot
- `ca-config.cnf` - Configuración de la CA
- `certs/robot-X/openssl.cnf` - Configuración de cada robot

### Scripts disponibles

- `create_ca.sh` - Crear Certificate Authority
- `generate_robot_cert.sh` - Generar certificado de robot

### Seguridad

**Archivos CRÍTICOS (mantener seguros):**
- ❗ `ca-key.pem` - Clave privada de la CA
- ❗ `key.pem` - Clave privada del robot (en cada robot)

**Archivos PÚBLICOS (compartir):**
- ✅ `ca-cert.pem` - Certificado de la CA (instalar en orquestador)
- ✅ `cert.pem` - Certificado del robot (empaquetado en la app)

**Buenas prácticas:**
1. Guardar `ca-key.pem` en múltiples ubicaciones seguras
2. Hacer backups regulares de la CA
3. Rotar certificados antes de que expiren
4. Mantener log de certificados generados
5. No compartir `ca-key.pem` - solo usarlo para firmar

---

## 🎯 Resumen rápido

```bash
# === SETUP INICIAL (UNA VEZ) ===

# 1. Crear CA
./create_ca.sh

# 2. Instalar en orquestador
scp ca-cert.pem user@orchestrator:/opt/certs/robot-ca.pem

# 3. Configurar código orquestador
# verify='/opt/certs/robot-ca.pem'

# === AGREGAR ROBOT ===

# 1. Generar certificado
./generate_robot_cert.sh robot-1 192.168.1.100

# 2. Empaquetar
pyinstaller app.spec

# 3. Distribuir
# ✅ El orquestador NO necesita cambios

# === CAMBIAR IP DE ROBOT ===

# 1. Regenerar certificado
./generate_robot_cert.sh robot-1 192.168.2.100  # Nueva IP

# 2. Reempaquetar y redistribuir solo ese robot
# ✅ El orquestador NO necesita cambios
```

---

**🎉 ¡Sistema de CA configurado! Ahora puedes escalar a infinitos robots sin tocar el orquestador.**
