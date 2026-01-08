"""
Streaming Feed Endpoints.

Provides video streaming endpoints:
    - GET /stream/feed: Server-Sent Events video feed
    - GET /stream-view: HTML viewer page
"""
import time
import base64
from flask import Blueprint, Response, render_template
from api.auth import require_auth, require_auth_sse
from shared.state.redis_state import redis_state
from streaming.streamer import ScreenStreamer
from shared.config.loader import get_resource_path


# Create blueprint
streaming_feed_bp = Blueprint('streaming_feed', __name__)


@streaming_feed_bp.route('/stream/feed')
@require_auth_sse
def stream_feed():
    """
    GET /stream/feed - Feed de video mediante Server-Sent Events.

    Este endpoint sirve el stream de video a través de HTTP usando SSE,
    lo que permite que funcione con cualquier IP y a través del túnel.

    Verifica el estado de streaming desde Redis y captura frames localmente.

    Returns:
        Response: Server-Sent Events stream with base64-encoded JPEG frames
    """
    def generate_frames():
        """Genera frames del streaming si está activo según Redis."""
        # Crear streamer local para captura de frames
        local_streamer = None
        current_fps = 15
        current_quality = 75

        # Contador de intentos fallidos consecutivos
        inactive_count = 0
        max_inactive = 3  # Terminar después de 3 segundos inactivo

        print("[STREAM-FEED] Nueva conexión SSE establecida")

        try:
            while True:
                try:
                    # Verificar estado en Redis
                    redis_client = redis_state._get_redis_client()
                    state = redis_client.hgetall('streaming:state')

                    is_active = state and state.get(b'active') == b'true'

                    if is_active:
                        # Reset contador si está activo
                        inactive_count = 0

                        # Obtener configuración desde Redis
                        fps_str = state.get(b'fps', b'15').decode('utf-8')
                        quality_str = state.get(b'quality', b'75').decode('utf-8')
                        new_fps = int(fps_str)
                        new_quality = int(quality_str)

                        # Crear o recrear streamer si cambió la configuración
                        if not local_streamer or current_fps != new_fps or current_quality != new_quality:
                            if local_streamer:
                                print(f"[STREAM-FEED] Recreando streamer (fps={new_fps}, quality={new_quality})")
                            else:
                                print(f"[STREAM-FEED] Creando streamer (fps={new_fps}, quality={new_quality})")

                            local_streamer = ScreenStreamer(
                                port=8765,  # No se usa
                                quality=new_quality,
                                fps=new_fps,
                                ssl_certfile=get_resource_path('ssl/cert.pem'),
                                ssl_keyfile=get_resource_path('ssl/key.pem')
                            )
                            current_fps = new_fps
                            current_quality = new_quality

                        try:
                            # Actualizar timestamp de actividad de clientes
                            redis_client.set('streaming:last_client_activity', str(time.time()), ex=60)

                            # Capturar frame
                            frame_data = local_streamer.capture_screen()

                            # Codificar en base64
                            frame_b64 = base64.b64encode(frame_data).decode('utf-8')
                            message = f"data:image/jpeg;base64,{frame_b64}"

                            # Enviar como evento SSE
                            yield f"data: {message}\n\n"

                            # Control de FPS dinámico
                            time.sleep(1 / current_fps)

                        except GeneratorExit:
                            # Cliente desconectado
                            print("[STREAM-FEED] Cliente desconectado del feed")
                            break
                        except Exception as e:
                            print(f"[STREAM-FEED] Error generando frame: {e}")
                            yield f"data: error\n\n"
                            time.sleep(0.5)
                    else:
                        # Streaming inactivo según Redis
                        inactive_count += 1

                        # Limpiar streamer local si existe
                        if local_streamer:
                            local_streamer = None
                            print("[STREAM-FEED] Streamer local liberado")

                        if inactive_count >= max_inactive:
                            # Enviar mensaje final y terminar la conexión
                            print("[STREAM-FEED] Stream inactivo, cerrando conexión SSE")
                            yield f"data: stream_stopped\n\n"
                            break

                        # Enviar mensaje de inactivo mientras esperamos
                        yield f"data: inactive\n\n"
                        time.sleep(1)

                except GeneratorExit:
                    # Cliente cerró la conexión
                    print("[STREAM-FEED] Conexión cerrada por el cliente")
                    break
                except Exception as e:
                    print(f"[STREAM-FEED] Error en generador: {e}")
                    break

        finally:
            # Limpiar streamer local al finalizar
            if local_streamer:
                local_streamer = None
                print("[STREAM-FEED] Streamer local limpiado (finally)")

    return Response(
        generate_frames(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@streaming_feed_bp.route('/stream-view')
@require_auth
def stream_view():
    """
    GET /stream-view - Vista dedicada para el streaming de pantalla.

    Returns:
        HTML: Página completa para visualizar el streaming
    """
    return render_template('stream_view.html')
