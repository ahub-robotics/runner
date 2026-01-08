# Manual Tests

Scripts de prueba manual para verificar funcionalidad específica del Robot Runner.

## Archivos

- **test_streaming_quick.py**: Test rápido de streaming (verifica que no crashee)
- **test_streaming_start_stop.py**: Test de inicio/detención de streaming
- **test_streaming_complete.py**: Test completo de streaming con todas las operaciones
- **test_screen_capture.py**: Test de captura de pantalla directa

## Uso

Estos scripts son para pruebas manuales durante desarrollo. Asumen:
- Servidor corriendo en https://localhost:5001
- Token configurado en el script
- Certificados SSL válidos (o verify=False)

Para usar:
```bash
python tests/manual/test_streaming_quick.py
```

## Nota

Estos tests NO son parte de la suite de tests automatizados (pytest).
Son útiles para debugging y validación manual de características específicas.
