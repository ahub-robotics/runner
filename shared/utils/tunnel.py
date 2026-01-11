"""
Tunnel Utilities.

Provides helper functions for Cloudflare tunnel management:
    - get_tunnel_hostname: Normalize tunnel hostname from config
"""


def get_tunnel_hostname(config):
    """
    Obtiene el hostname del túnel normalizado desde la configuración.

    Maneja dos casos:
    1. tunnel_subdomain ya incluye el dominio completo (ej: "robot1.automatehub.es")
    2. tunnel_subdomain es solo el prefijo (ej: "robot1")

    Args:
        config (dict): Configuración con tunnel_subdomain y/o machine_id

    Returns:
        str: Hostname completo (ej: "robot1.automatehub.es") o 'N/A' si no está configurado

    Examples:
        >>> get_tunnel_hostname({'tunnel_subdomain': 'robot1.automatehub.es'})
        'robot1.automatehub.es'

        >>> get_tunnel_hostname({'tunnel_subdomain': 'ROBOT1'})
        'robot1.automatehub.es'

        >>> get_tunnel_hostname({'machine_id': 'ROBOT1'})
        'robot1.automatehub.es'

        >>> get_tunnel_hostname({'tunnel_subdomain': ''})
        'N/A'
    """
    # Obtener tunnel_subdomain o machine_id
    subdomain_value = config.get('tunnel_subdomain', '').strip()
    if not subdomain_value:
        subdomain_value = config.get('machine_id', '').strip()

    if not subdomain_value:
        return 'N/A'

    # Normalizar a minúsculas
    subdomain_value = subdomain_value.lower()

    # Si ya incluye el dominio, devolverlo tal cual
    if '.automatehub.es' in subdomain_value:
        return subdomain_value

    # Si es solo el prefijo, añadir el dominio
    return f"{subdomain_value}.automatehub.es"