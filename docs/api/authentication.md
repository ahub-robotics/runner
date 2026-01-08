# Autenticación de API - Robot Runner

## Descripción

Robot Runner implementa un sistema de autenticación de doble capa para proteger los endpoints de la API:

1. **Token de Autenticación**: Requerido en todas las peticiones a endpoints de API
2. **Machine ID + License Key**: Validación específica por máquina (endpoints específicos)

## Token de Autenticación

### ¿Qué es el Token?

El token de autenticación es una cadena única que identifica y autoriza a un cliente (orquestador) para realizar peticiones al servidor Robot Runner.

**Importante**:
- Cada Robot Runner tiene su propio token configurado en `config.json`
- El token se almacena de forma segura y se muestra oculto en la interfaz web
- Todas las peticiones a endpoints de API deben incluir este token

### Configuración del Token

#### En el archivo config.json

```json
{
    "token": "b82ababd99cb8c0fba61d8325ee4138c08b13745",
    "machine_id": "I3WFQVS5FDHS",
    "license_key": "BVXV9JC78STCV89333XVUV5B838LIU1VX4FT",
    ...
}
```

#### En la Interfaz Web

1. Inicia la aplicación: `python run.py`
2. Accede a `https://localhost:5055/settings` en tu navegador
3. Ingresa tu token para autenticarte
4. Edita el campo "Token de Autenticación" si es necesario
5. Guarda la configuración

## Cómo Usar el Token

**IMPORTANTE**: Por razones de seguridad, el token **SOLO** puede enviarse en el body JSON de la petición.

### Formato Requerido: Body JSON

El token DEBE incluirse en el body de la petición como JSON.

```python
import requests

# Para peticiones POST
response = requests.post(
    'https://robot.example.com/run',
    json={
        'token': 'b82ababd99cb8c0fba61d8325ee4138c08b13745',
        'robot_file': 'mi_robot.py',
        'params': {...}
    }
)

# Para peticiones GET (enviar token en el body)
response = requests.get(
    'https://robot.example.com/status',
    json={
        'token': 'b82ababd99cb8c0fba61d8325ee4138c08b13745',
        'machine_id': 'I3WFQVS5FDHS',
        'license_key': 'BVXV9JC78STCV89333XVUV5B838LIU1VX4FT'
    }
)
```

**Nota**: Las opciones anteriores de enviar el token por header (Authorization Bearer) o por query parameter han sido **deshabilitadas por seguridad**.

## Ejemplos Completos

### Ejemplo 1: Consultar Estado del Robot

```python
import requests

# Configuración
robot_url = 'https://38ppu1z6ze5c.automatehub.es'
token = 'b82ababd99cb8c0fba61d8325ee4138c08b13745'
machine_id = 'I3WFQVS5FDHS'
license_key = 'BVXV9JC78STCV89333XVUV5B838LIU1VX4FT'

# Petición con token en body JSON
response = requests.get(
    f'{robot_url}/status',
    json={
        'token': token,
        'machine_id': machine_id,
        'license_key': license_key
    }
)

if response.status_code == 200:
    status = response.json()
    print(f"Estado del robot: {status}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

### Ejemplo 2: Ejecutar un Robot

```python
import requests

# Configuración
robot_url = 'https://38ppu1z6ze5c.automatehub.es'
token = 'b82ababd99cb8c0fba61d8325ee4138c08b13745'

# Petición POST con token en body
response = requests.post(
    f'{robot_url}/run',
    json={
        'token': token,
        'robot_file': 'automation_script.py',
        'params': {
            'env': 'production',
            'retry': 3
        }
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Robot iniciado: {result['message']}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

### Ejemplo 3: Detener el Robot

```python
import requests

# Configuración
robot_url = 'https://38ppu1z6ze5c.automatehub.es'
token = 'b82ababd99cb8c0fba61d8325ee4138c08b13745'

# Petición GET con token en body JSON
response = requests.get(
    f'{robot_url}/stop',
    json={'token': token}
)

if response.status_code == 200:
    result = response.json()
    print(f"Robot detenido: {result['message']}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

## Códigos de Respuesta de Autenticación

### 200 OK
El token es válido y la petición fue procesada correctamente.

```json
{
    "message": "running"
}
```

### 400 Bad Request - Formato Inválido
La petición no envía el token en el formato JSON requerido.

```json
{
    "error": "Formato inválido",
    "message": "La petición debe enviar JSON en el body con el campo 'token'"
}
```

**Solución**: Envía el token en el body como JSON:
```python
response = requests.get(url, json={'token': 'tu_token'})
```

### 401 Unauthorized - Token Faltante
No se proporcionó un token en el body JSON.

```json
{
    "error": "Token de autenticación requerido",
    "message": "Debe proporcionar un token en el body JSON con el campo 'token'"
}
```

**Solución**: Incluye el campo `token` en el body JSON de tu petición.

### 403 Forbidden - Token Inválido
El token proporcionado no coincide con el token configurado.

```json
{
    "error": "Token inválido",
    "message": "El token proporcionado no es válido"
}
```

**Solución**: Verifica que estés usando el token correcto del `config.json`.

## Autenticación para API vs Web

El sistema de autenticación maneja dos tipos de clientes de forma diferente:

### Para Peticiones API (JSON)
**Método**: Token en body JSON
- Todas las peticiones deben incluir `{"token": "tu_token"}` en el body
- Ideal para integraciones programáticas y orquestadores

### Para Navegadores Web
**Método**: Sistema de login con sesiones
1. Accede a `/login` e ingresa tu token
2. La sesión se mantiene activa automáticamente
3. Puedes navegar por todas las páginas sin reenviar el token
4. Cierra sesión en `/logout` cuando termines

## Endpoints Protegidos

**TODOS** los endpoints del servidor requieren autenticación.

### Endpoints de API (Requieren Token JSON)

| Endpoint | Método | Requiere Token | Requiere Machine ID + License Key |
|----------|--------|----------------|-----------------------------------|
| `/status` | GET | ✅ Sí (JSON) | ✅ Sí |
| `/execution` | GET | ✅ Sí (JSON) | ❌ No |
| `/run` | POST | ✅ Sí (JSON) | ❌ No |
| `/stop` | GET | ✅ Sí (JSON) | ❌ No |
| `/pause` | GET | ✅ Sí (JSON) | ❌ No |
| `/resume` | GET | ✅ Sí (JSON) | ❌ No |
| `/block` | GET | ✅ Sí (JSON) | ❌ No |

### Endpoints de Interfaz Web (Requieren Login o Token JSON)

| Endpoint | Método | Autenticación | Descripción |
|----------|--------|---------------|-------------|
| `/login` | GET/POST | ⚪ Público | Página de login |
| `/logout` | GET/POST | ⚪ Público | Cerrar sesión |
| `/` | GET | ✅ Sesión o Token JSON | Página de inicio |
| `/connected` | GET/POST | ✅ Sesión o Token JSON | Dashboard del robot |
| `/connect` | GET/POST | ✅ Sesión o Token JSON | Configuración |

### Archivos Estáticos

Los archivos estáticos en `/static/` (CSS, JavaScript, imágenes) son servidos por Flask sin autenticación. Esto es necesario para que la interfaz web funcione correctamente. Los archivos estáticos no contienen información sensible y son requeridos para renderizar las páginas HTML protegidas.

## Cómo Acceder a la Web

### Opción 1: Desde un Navegador

1. Abre tu navegador y ve a `https://tu-servidor:5055/login`
2. Ingresa el token de autenticación (lo encuentras en `config.json`)
3. Haz clic en "LOGIN"
4. Ahora puedes navegar por todas las páginas:
   - `/` - Página de inicio
   - `/connected` - Dashboard
   - `/connect` - Configuración
5. Cuando termines, haz clic en "LOGOUT" para cerrar sesión

### Opción 2: Desde una API/Script

```python
import requests

# Para APIs, usa token en JSON
response = requests.get(
    'https://tu-servidor:5055/status',
    json={
        'token': 'tu_token',
        'machine_id': 'ID',
        'license_key': 'KEY'
    }
)
```

## Seguridad

### Mejores Prácticas

1. **Genera tokens seguros**: Usa tokens largos y aleatorios
   ```python
   import secrets
   token = secrets.token_hex(32)  # Token de 64 caracteres
   ```

2. **Usa HTTPS siempre**: Nunca envíes tokens sobre HTTP
   - Robot Runner usa HTTPS con certificados SSL
   - Cloudflare Tunnel proporciona SSL automático

3. **No compartas el token**: Es como una contraseña
   - No lo incluyas en logs
   - No lo commitas en git
   - No lo envíes por email/chat sin cifrar

4. **Rota el token periódicamente**: Cambia el token cada cierto tiempo
   ```bash
   # Edita config.json con un nuevo token desde la interfaz web
   python run.py  # Y actualiza desde /settings
   ```

5. **Envía el token en el body JSON**: Es el único método permitido
   ```python
   response = requests.get(url, json={'token': token})
   ```

6. **Usa login web para navegadores**: Para acceder desde el navegador, usa el sistema de login en `/login`

7. **Cierra sesión cuando termines**: Usa el botón "LOGOUT" para cerrar tu sesión web

8. **Sesiones seguras**: Las sesiones web usan cookies seguras (HTTPS only, HttpOnly, SameSite)

### Verificar Token desde Consola

Para probar que tu token funciona con curl:

```bash
# Con curl enviando JSON en el body
curl -X GET "https://robot.example.com/status" \
     -H "Content-Type: application/json" \
     -d '{
       "token": "TU_TOKEN",
       "machine_id": "ID",
       "license_key": "KEY"
     }'
```

### Token en Cloudflare Tunnel

Si usas Cloudflare Tunnel, el token debe enviarse en el body JSON:

```python
import requests

# URL del túnel de Cloudflare
robot_url = 'https://38ppu1z6ze5c.automatehub.es'
token = 'b82ababd99cb8c0fba61d8325ee4138c08b13745'

response = requests.get(
    f'{robot_url}/status',
    json={
        'token': token,
        'machine_id': 'ID',
        'license_key': 'KEY'
    }
)
```

## Troubleshooting

### Error: "Formato inválido"

**Causa**: No se envió el token en formato JSON

**Solución**:
```python
# Envía el token en el body como JSON
response = requests.get(url, json={'token': token})
```

### Error: "Token de autenticación requerido"

**Causa**: No se proporcionó el token en el body JSON

**Solución**:
```python
# Añade el token en el body JSON
response = requests.get(url, json={'token': token})
```

### Error: "Token inválido"

**Causa**: El token no coincide con el del servidor

**Solución**:
1. Verifica el token en `config.json` o en la interfaz web (/settings)
2. Asegúrate de copiar el token completo (sin espacios)
3. Verifica que no haya caracteres especiales o saltos de línea

### Error: Redirigido a /login al intentar acceder a una página

**Causa**: No has iniciado sesión en el navegador

**Solución**:
1. Accede a `/login`
2. Ingresa tu token de autenticación
3. Haz clic en "LOGIN"
4. Ahora podrás navegar por todas las páginas

### Error: "Token inválido" en página de login

**Causa**: El token ingresado no coincide con el del servidor

**Solución**:
1. Abre `config.json` o la interfaz web (/settings)
2. Copia el token exacto (sin espacios ni saltos de línea)
3. Pégalo en el formulario de login
4. Intenta de nuevo

### Error: Sesión expirada o perdida

**Causa**: La sesión se limpió o el servidor se reinició

**Solución**:
1. Vuelve a `/login`
2. Ingresa tu token nuevamente
3. La sesión se mantendrá hasta que hagas logout o cierres el navegador

### Error: SSL Certificate Verify Failed

**Causa**: Certificado SSL autofirmado

**Solución**:
```python
# Opción 1: Usar el certificado CA
response = requests.get(url, headers=headers, verify='/path/to/ca-cert.pem')

# Opción 2: Deshabilitar verificación (solo desarrollo)
response = requests.get(url, headers=headers, verify=False)
```

### El token se muestra en los logs

**Solución**: Asegúrate de no logear el token
```python
# ❌ MAL
print(f"Token: {token}")

# ✅ BIEN
print("Token: [REDACTED]")
```

## Migración desde Versiones Anteriores

### Migración desde versión sin autenticación por token

Si vienes de una versión anterior sin autenticación por token:

1. **Actualiza tu código** para incluir el token en el body JSON
2. **Configura el token** en `config.json` desde la interfaz web (/settings)
3. **Prueba tus peticiones** con el nuevo sistema

**Antes (sin token):**
```python
response = requests.get(
    'https://robot.example.com/status',
    params={'machine_id': 'ID', 'license_key': 'KEY'}
)
```

**Después (con token en body JSON):**
```python
response = requests.get(
    'https://robot.example.com/status',
    json={
        'token': 'TU_TOKEN',
        'machine_id': 'ID',
        'license_key': 'KEY'
    }
)
```

### Migración desde versión con token en header/query

Si vienes de una versión que permitía enviar el token por header o query parameter:

**Antes (token en header):**
```python
headers = {'Authorization': 'Bearer TU_TOKEN'}
response = requests.get('https://robot.example.com/status', headers=headers)
```

**Antes (token en query):**
```python
response = requests.get('https://robot.example.com/status?token=TU_TOKEN')
```

**Ahora (token en body JSON):**
```python
response = requests.get(
    'https://robot.example.com/status',
    json={'token': 'TU_TOKEN'}
)
```

### Migración de configuración web a Tkinter

Si antes editabas la configuración desde `/connect` en la web:

1. La configuración web ha sido **deshabilitada por seguridad**
2. Ahora SOLO puedes editar la configuración desde la interfaz web
3. Ejecuta `python run.py` y ve a `/settings` en tu navegador

## Soporte

Para más información:
- Ver [Documentación Técnica](TECHNICAL-DOCUMENTATION.md)
- Ver [Guía de Usuario](FUNCTIONAL-DOCUMENTATION.md)
- Ver [Documentación Técnica](TECHNICAL-DOCUMENTATION.md)

---

**Versión**: 2.3.0
**Última actualización**: 2025-12-19

## Changelog de Seguridad

### v2.3.0 (2025-12-19)
- **Sistema de Login Web**: Implementado sistema de autenticación con sesiones para navegadores
- **Acceso web habilitado**: Se puede acceder y editar la configuración desde la web después de hacer login
- **Logout funcional**: Botón de logout en todas las páginas web
- **Autenticación híbrida**: APIs usan token JSON, navegadores usan sesiones
- **Mejora en UX**: Ya no es necesario enviar el token en cada petición desde el navegador

### v2.2.0 (2025-12-19)
- **Token solo en JSON**: El token ahora SOLO puede enviarse en el body JSON (eliminadas opciones de header y query parameter)
- **Todas las rutas protegidas**: TODOS los endpoints requieren autenticación por token, incluyendo la interfaz web
- **Mejoras de seguridad**: Mayor control sobre el acceso al servidor y prevención de exposición de tokens en URLs
