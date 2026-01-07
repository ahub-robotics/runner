# Changelog de Seguridad - Robot Runner

## Versión 2.1.0 (2025-12-19)

### 🔒 Autenticación por Token Añadida

Se ha implementado un sistema de autenticación por token para proteger todos los endpoints de la API.

#### Cambios Implementados

1. **Middleware de Autenticación** (`src/app.py`)
   - Nuevo decorador `@require_token` que valida el token en todas las peticiones
   - Soporta tres métodos de autenticación:
     - Header `Authorization: Bearer <token>`
     - Parámetro de query `?token=<token>`
     - Body JSON `{"token": "<token>"}`

2. **Endpoints Protegidos**
   Todos los endpoints de API ahora requieren token:
   - ✅ `/status` - Consultar estado del robot
   - ✅ `/execution` - Estado de ejecución actual
   - ✅ `/run` - Iniciar ejecución de robot
   - ✅ `/stop` - Detener ejecución actual
   - ✅ `/pause` - Pausar ejecución
   - ✅ `/resume` - Reanudar ejecución pausada
   - ✅ `/block` - Bloquear robot manualmente

3. **Endpoints NO Protegidos**
   Los endpoints de UI no requieren token (acceso local):
   - `/` - Página de inicio
   - `/connect` - Formulario de configuración
   - `/connected` - Dashboard

4. **Interfaz Gráfica Mejorada** (`src/gui.py`)
   - Campo de token ahora se muestra oculto con asteriscos (`show="*"`)
   - Botón "👁️ Mostrar / 🙈 Ocultar" para alternar visibilidad
   - Logs de visibilidad en el panel de logs

5. **Códigos de Estado HTTP**
   - `401 Unauthorized` - Token no proporcionado
   - `403 Forbidden` - Token inválido
   - `200 OK` - Token válido, petición exitosa

#### Documentación Añadida

- **[docs/API-AUTHENTICATION.md](API-AUTHENTICATION.md)** - Guía completa de autenticación
  - Cómo configurar el token
  - Ejemplos de uso en Python
  - Tres métodos de envío del token
  - Troubleshooting
  - Mejores prácticas de seguridad

- **[scripts/test_authentication.py](../scripts/test_authentication.py)** - Script de prueba
  - Verifica que la autenticación funcione correctamente
  - Prueba los tres métodos de envío del token
  - Prueba casos de error (sin token, token inválido)

#### Migración desde Versiones Anteriores

Si vienes de una versión anterior sin autenticación:

**Antes (v2.0.0):**
```python
response = requests.get('https://robot.example.com/status')
```

**Después (v2.1.0):**
```python
headers = {'Authorization': 'Bearer tu-token'}
response = requests.get('https://robot.example.com/status', headers=headers)
```

#### Configuración del Token

**Opción 1: Desde la GUI**
1. Ejecutar `python run_gui.py`
2. Ir a pestaña "⚙️ Configuración"
3. Ver/editar el campo "Token de Autenticación"
4. Usar el botón "👁️ Mostrar" para ver el token
5. Guardar configuración

**Opción 2: Desde config.json**
```json
{
    "token": "b82ababd99cb8c0fba61d8325ee4138c08b13745",
    ...
}
```

#### Probar la Autenticación

```bash
# Iniciar el servidor
python run_gui.py  # O python run.py --server-only

# En otra terminal, ejecutar tests
python scripts/test_authentication.py
```

Deberías ver:
```
=== Test 1: Petición SIN token ===
✅ CORRECTO: Servidor rechazó petición sin token (401)

=== Test 2: Petición con token INVÁLIDO ===
✅ CORRECTO: Servidor rechazó token inválido (403)

=== Test 3: Token válido en HEADER Authorization ===
✅ CORRECTO: Servidor aceptó token válido en header (200)

...

🎉 ¡Todos los tests pasaron!
```

#### Mejores Prácticas

1. **Genera tokens seguros**
   ```python
   import secrets
   token = secrets.token_hex(32)  # 64 caracteres
   ```

2. **Usa HTTPS siempre**
   - Robot Runner usa SSL/TLS por defecto
   - Cloudflare Tunnel proporciona SSL automático

3. **Rota el token periódicamente**
   - Cambia el token cada cierto tiempo
   - Actualiza en todos los orquestadores

4. **No compartas el token**
   - Es como una contraseña
   - No lo incluyas en logs
   - No lo commitas en git

5. **Usa el header Authorization**
   - Es la forma más estándar y segura
   - Preferible sobre query parameters

#### Impacto en Orquestadores

Los orquestadores que se conecten al Robot Runner deben actualizar su código:

```python
# Código de ejemplo para orquestadores
import requests

class RobotClient:
    def __init__(self, robot_url, token):
        self.robot_url = robot_url
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}'}

    def get_status(self, machine_id, license_key):
        response = requests.get(
            f'{self.robot_url}/status',
            headers=self.headers,
            params={
                'machine_id': machine_id,
                'license_key': license_key
            },
            verify='/path/to/ca-cert.pem'  # O verify=False para desarrollo
        )
        return response.json()

    def run_robot(self, robot_file, params):
        response = requests.post(
            f'{self.robot_url}/run',
            headers=self.headers,
            json={
                'robot_file': robot_file,
                'params': params
            },
            verify='/path/to/ca-cert.pem'
        )
        return response.json()

# Uso
client = RobotClient(
    robot_url='https://38ppu1z6ze5c.automatehub.es',
    token='b82ababd99cb8c0fba61d8325ee4138c08b13745'
)

status = client.get_status('I3WFQVS5FDHS', 'BVXV9JC78STCV...')
print(f"Estado: {status}")
```

#### Backward Compatibility

⚠️ **BREAKING CHANGE**: Esta versión NO es compatible con versiones anteriores.

Todos los clientes que hagan peticiones al Robot Runner deben actualizar su código para incluir el token de autenticación.

Si necesitas soporte para versiones antiguas:
1. Usa la versión 2.0.0 (sin autenticación por token)
2. O actualiza todos tus orquestadores para soportar tokens

#### Troubleshooting

**Error: "Token de autenticación requerido"**
- Causa: No se proporcionó el token
- Solución: Añade el token en header, query o body

**Error: "Token inválido"**
- Causa: El token no coincide con el del servidor
- Solución: Verifica el token en `config.json` o la GUI

**Error: SSL Certificate Verify Failed**
- Causa: Certificado SSL autofirmado
- Solución: Usa `verify='/path/to/ca-cert.pem'` o `verify=False` (solo desarrollo)

#### Archivos Modificados

```
src/app.py                         # Añadido decorador @require_token
src/gui.py                         # Token oculto con asteriscos + botón toggle
requirements.txt                   # No cambios (usa customtkinter ya existente)
docs/API-AUTHENTICATION.md         # Nueva documentación completa
docs/SECURITY-CHANGELOG.md         # Este archivo
scripts/test_authentication.py     # Nuevo script de pruebas
README.md                          # Actualizado con info de seguridad
```

#### Referencias

- [Documentación de Autenticación](API-AUTHENTICATION.md)
- [Interfaz Gráfica Tkinter](GUI-TKINTER.md)
- [Documentación Técnica](TECHNICAL-DOCUMENTATION.md)

---

## Versiones Anteriores

### Versión 2.0.0 (2025-12-18)
- Nueva interfaz gráfica con CustomTkinter
- Soporte para túnel de Cloudflare
- Gestión de servidor y túnel desde GUI
- Sin autenticación por token (⚠️ inseguro)

### Versión 1.x
- Interfaz web con webview
- Autenticación solo por machine_id y license_key
- Sin autenticación adicional por token

---

**Nota**: A partir de la versión 2.1.0, se recomienda usar tokens seguros y rotarlos periódicamente para maximizar la seguridad.
