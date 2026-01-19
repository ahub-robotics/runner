# 🌐 Configuración de Túneles Cloudflare

**Guía completa para configurar túneles Cloudflare Zero Trust en Robot Runner**

---

## 📋 Tabla de Contenidos

- [Introducción](#introducción)
- [Requisitos Previos](#requisitos-previos)
- [Instalación de Cloudflared](#instalación-de-cloudflared)
- [Configuración Rápida](#configuración-rápida)
- [Configuración por Máquina](#configuración-por-máquina)
- [Múltiples Máquinas](#múltiples-máquinas)
- [Gestión desde la UI](#gestión-desde-la-ui)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Introducción

Los **túneles Cloudflare** permiten exponer tu Robot Runner de forma segura sin necesidad de:
- Abrir puertos en el firewall
- Configurar port forwarding
- Exponer direcciones IP públicas
- Configurar VPNs complejas

### Ventajas

✅ **Seguro**: Tráfico cifrado end-to-end
✅ **Simple**: No requiere configuración de red
✅ **Rápido**: Red global de Cloudflare
✅ **Gratuito**: Plan Free incluye túneles ilimitados
✅ **Escalable**: Múltiples máquinas con diferentes subdominios

---

## Requisitos Previos

### 1. Cuenta Cloudflare

1. Crear cuenta en [Cloudflare](https://dash.cloudflare.com/sign-up)
2. Añadir un dominio (o usar subdominio de Cloudflare)
3. Ir a **Zero Trust** → **Networks** → **Tunnels**

### 2. Dominio Configurado

Para este ejemplo, usaremos `automatehub.es` como dominio base.

---

## Instalación de Cloudflared

### Windows

```powershell
# Opción 1: Winget
winget install --id Cloudflare.cloudflared

# Opción 2: Chocolatey
choco install cloudflared

# Opción 3: Descarga manual
# https://github.com/cloudflare/cloudflared/releases
```

### macOS

```bash
# Homebrew
brew install cloudflared
```

### Linux

```bash
# Debian/Ubuntu
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Red Hat/CentOS
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm
sudo rpm -i cloudflared-linux-x86_64.rpm
```

### Verificar Instalación

```bash
cloudflared --version
# Debería mostrar: cloudflared version 2024.x.x
```

---

## Configuración Rápida

### Opción 1: Script Automático (Recomendado)

```bash
# Ejecutar script interactivo
python setup_tunnel.py
```

El script te pedirá:
1. **Hostname**: Subdominio para el túnel (ej: `robot-1`)
2. **Puerto**: Puerto local del servidor (ej: `5001` o `8088`)
3. **Credenciales**: Seleccionar una de 3 opciones

#### Opciones de Credenciales

**Opción 1: Pegar JSON (Recomendado)**
```json
{
  "AccountTag": "your-account-tag",
  "TunnelSecret": "your-tunnel-secret",
  "TunnelID": "3d7de42c-4a8a-4447-b14f-053cc485ce6b",
  "Endpoint": ""
}
```

**Opción 2: Cargar desde archivo**
- Proporcionar ruta al archivo `.json` de credenciales

**Opción 3: Autenticar con Cloudflare**
- Abre navegador para autenticar
- Lista túneles existentes
- Explica limitación de descargar credenciales

### Opción 2: Configuración Manual

#### 1. Crear Túnel

```bash
cloudflared tunnel login
cloudflared tunnel create robotrunner
```

Esto genera:
- Archivo de credenciales: `~/.cloudflared/{tunnel-id}.json`
- ID del túnel

#### 2. Configurar config.yml

Crear `~/.cloudflared/config.yml`:

```yaml
tunnel: 3d7de42c-4a8a-4447-b14f-053cc485ce6b
credentials-file: /home/user/.cloudflared/3d7de42c-4a8a-4447-b14f-053cc485ce6b.json

ingress:
  - hostname: robot-1.automatehub.es
    service: https://localhost:5001
    originRequest:
      noTLSVerify: true
  - service: http_status:404
```

#### 3. Crear Ruta DNS

```bash
cloudflared tunnel route dns robotrunner robot-1.automatehub.es
```

#### 4. Iniciar Túnel

```bash
cloudflared tunnel run robotrunner
```

---

## Configuración por Máquina

### Conceptos Clave

**Un túnel puede servir múltiples hostnames**, pero cada hostname apunta a una sola máquina.

```
Túnel: robotrunner (ID: 3d7de42c-4a8a-4447-b14f-053cc485ce6b)
├── robot-1.automatehub.es → Máquina 1 (Mac, puerto 5001)
├── robot-2.automatehub.es → Máquina 2 (Windows, puerto 8088)
└── robot-3.automatehub.es → Máquina 3 (Linux, puerto 5001)
```

### Configuración en config.json

#### Máquina 1 (Mac)

```json
{
  "machine_id": "ROBOT-MAC-01",
  "tunnel_subdomain": "robot-1.automatehub.es",
  "tunnel_id": "3d7de42c-4a8a-4447-b14f-053cc485ce6b",
  "port": "5001"
}
```

#### Máquina 2 (Windows)

```json
{
  "machine_id": "ROBOT-WIN-01",
  "tunnel_subdomain": "robot-2.automatehub.es",
  "tunnel_id": "3d7de42c-4a8a-4447-b14f-053cc485ce6b",
  "port": "8088"
}
```

### Estructura de Archivos

Cada máquina necesita:

**1. Credenciales del Túnel**
```
~/.cloudflared/
└── 3d7de42c-4a8a-4447-b14f-053cc485ce6b.json
```

**2. Configuración del Túnel**
```
~/.cloudflared/
└── config.yml
```

**3. Configuración de Robot Runner**
```
~/Robot/
└── config.json
```

---

## Múltiples Máquinas

### Escenario: 10 Máquinas Simultáneas

Todas pueden compartir el **mismo tunnel_id** pero con **subdominios diferentes**:

| Máquina | Subdominio | Config.json |
|---------|------------|-------------|
| Mac Office | `mac-office.automatehub.es` | `tunnel_subdomain: "mac-office.automatehub.es"` |
| Windows Prod 1 | `win-prod-01.automatehub.es` | `tunnel_subdomain: "win-prod-01.automatehub.es"` |
| Windows Prod 2 | `win-prod-02.automatehub.es` | `tunnel_subdomain: "win-prod-02.automatehub.es"` |
| ... | ... | ... |

### Pasos

1. **Copiar credenciales a todas las máquinas**
   ```bash
   # Desde máquina origen
   scp ~/.cloudflared/*.json usuario@maquina-destino:~/.cloudflared/
   ```

2. **Configurar cada máquina**
   ```bash
   # En cada máquina
   python setup_tunnel.py
   # Usar subdominio único
   ```

3. **Iniciar túneles**
   ```bash
   # Desde UI o CLI
   python run.py --start-tunnel
   ```

### ⚠️ Importante

- **Cada máquina necesita un subdominio único**
- **Puedes compartir el tunnel_id**
- **No puedes tener dos máquinas con el mismo hostname simultáneamente**

---

## Gestión desde la UI

### Acceder a Configuración

1. Abrir Robot Runner: `https://localhost:5001`
2. Ir a **Ajustes** (Settings)
3. Sección **Cloudflare Tunnel**

### Campos de Configuración

**Tunnel Subdomain:**
```
robot-1.automatehub.es
```
O solo el prefijo:
```
robot-1
```
_(Se añadirá automáticamente `.automatehub.es`)_

**Tunnel ID:**
```
3d7de42c-4a8a-4447-b14f-053cc485ce6b
```

**Puerto:**
```
5001
```

### Gestionar Túnel

**Iniciar Túnel:**
```
POST /tunnel/start
```
Botón "Iniciar Túnel" en UI

**Detener Túnel:**
```
POST /tunnel/stop
```
Botón "Detener Túnel" en UI

**Ver Estado:**
```
GET /tunnel/status
```
Se actualiza automáticamente en UI

---

## Troubleshooting

### Error: "El túnel ya está activo"

**Problema:** Intentas iniciar un túnel que ya está corriendo.

**Solución:**
```bash
# Ver procesos
# Windows
tasklist | findstr cloudflared

# Mac/Linux
pgrep -f cloudflared

# Detener túnel
python run.py --stop-tunnel
```

### Error: "Configuración de túnel no encontrada"

**Problema:** Falta el archivo `~/.cloudflared/config.yml`

**Solución:**
```bash
python setup_tunnel.py
```

### Error: "Archivo de credenciales no encontrado"

**Problema:** Falta el archivo `.json` de credenciales.

**Solución:**
1. Obtener credenciales del dashboard de Cloudflare
2. Ejecutar `python setup_tunnel.py`
3. Seleccionar Opción 1 y pegar JSON

### Error: "error parsing tunnel ID"

**Problema:** El `config.yml` no tiene el formato correcto.

**Solución:**
```bash
# Verificar contenido
cat ~/.cloudflared/config.yml

# Regenerar
python setup_tunnel.py
```

### Túnel inicia pero no funciona

**Problema:** Configuración de hostname/puerto incorrecta.

**Verificar:**
```bash
# Ver logs del túnel
# Windows
cloudflared tunnel --loglevel debug run {tunnel-id}

# Mac/Linux
cloudflared tunnel --loglevel debug run robotrunner
```

**Revisar:**
1. ¿El hostname en `config.yml` coincide con el DNS?
2. ¿El puerto es correcto?
3. ¿El servidor está corriendo en ese puerto?

### Múltiples máquinas se desconectan entre sí

**Problema:** Están usando el mismo hostname.

**Solución:**
- Cada máquina debe tener un `tunnel_subdomain` único
- Ejemplo: `robot-1.automatehub.es`, `robot-2.automatehub.es`

---

## FAQ

### ¿Puedo usar varios túneles simultáneamente?

✅ **SÍ** - Puedes tener múltiples máquinas con el mismo `tunnel_id` pero diferentes subdominios.

### ¿Necesito un tunnel_id por máquina?

❌ **NO** - Puedes compartir el mismo `tunnel_id` entre todas las máquinas.

### ¿Cuántos subdominios puedo usar?

✅ **Ilimitados** (en el plan Free de Cloudflare)

### ¿El túnel consume muchos recursos?

❌ **NO** - Cloudflared usa ~20-50 MB RAM y CPU mínima.

### ¿Funciona sin internet?

❌ **NO** - Los túneles requieren conexión a internet para funcionar.

### ¿Puedo usar mi propio dominio?

✅ **SÍ** - Añade tu dominio a Cloudflare y úsalo para los túneles.

### ¿Cómo obtengo las credenciales de un túnel existente?

⚠️ **LIMITACIÓN** - Cloudflare NO permite descargar credenciales de túneles existentes.

**Opciones:**
1. Crear un nuevo túnel
2. Usar las credenciales originales (si las guardaste)
3. Copiar el archivo `.json` desde otra máquina

### ¿Qué pasa si cambio el puerto del servidor?

🔄 **ACTUALIZACIÓN AUTOMÁTICA** - La UI regenera el `config.yml` y reinicia el túnel automáticamente.

### ¿Puedo tener SSL y túnel al mismo tiempo?

✅ **SÍ** - El túnel soporta tanto HTTP como HTTPS origen.

---

## Comandos Útiles

### Ver estado del túnel
```bash
python run.py --tunnel-status
```

### Iniciar túnel
```bash
python run.py --start-tunnel
```

### Detener túnel
```bash
python run.py --stop-tunnel
```

### Configurar túnel
```bash
python run.py --setup-tunnel
```

### Ver configuración actual
```bash
python run.py --show-config
```

---

## Referencias

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflared GitHub](https://github.com/cloudflare/cloudflared)
- [Zero Trust Dashboard](https://dash.cloudflare.com/)

---

**Última actualización:** 2026-01-19
**Versión:** 2.0.0