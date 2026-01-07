#!/usr/bin/env python3
"""
Emisor de video en tiempo real.
Captura la pantalla y transmite via WebSocket a los clientes conectados.
"""

import asyncio
import base64
import io
import argparse
from typing import Set

try:
    import websockets
    from websockets.server import serve
except ImportError:
    print("Instalando websockets...")
    import subprocess
    subprocess.check_call(["pip", "install", "websockets", "--break-system-packages"])
    import websockets
    from websockets.server import serve

try:
    from PIL import ImageGrab
except ImportError:
    print("Instalando Pillow...")
    import subprocess
    subprocess.check_call(["pip", "install", "Pillow", "--break-system-packages"])
    from PIL import ImageGrab

try:
    import mss
except ImportError:
    print("Instalando mss...")
    import subprocess
    subprocess.check_call(["pip", "install", "mss", "--break-system-packages"])
    import mss


class ScreenStreamer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765, fps: int = 15, quality: int = 50,
                 ssl_certfile: str = None, ssl_keyfile: str = None):
        self.host = host
        self.port = port
        self.fps = fps
        self.quality = quality
        self.ssl_certfile = ssl_certfile
        self.ssl_keyfile = ssl_keyfile
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False
        self.server = None
        self.broadcast_task = None

    @property
    def is_running(self):
        """Retorna si el streamer está activo."""
        return self.running

    def stop(self):
        """Detiene el streaming."""
        self.running = False
        if self.broadcast_task:
            self.broadcast_task.cancel()
        # Cerrar todas las conexiones de clientes
        for client in self.clients.copy():
            try:
                asyncio.create_task(client.close())
            except:
                pass
        
    def capture_screen(self) -> bytes:
        """Captura la pantalla y devuelve los bytes de la imagen JPEG."""
        try:
            # Usar mss para captura multiplataforma (funciona en Linux sin display)
            with mss.mss() as sct:
                monitor = sct.monitors[0]  # Monitor principal
                screenshot = sct.grab(monitor)

                # Convertir a PIL Image
                from PIL import Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                # Redimensionar para mejor rendimiento
                max_width = 1280
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_size = (max_width, int(img.height * ratio))
                    # Usar el método moderno de Pillow 10+
                    resample_filter = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
                    img = img.resize(new_size, resample_filter)

                # Convertir a JPEG
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=self.quality, optimize=True)
                return buffer.getvalue()
        except Exception as e:
            print(f"Error capturando pantalla: {e}")
            import traceback
            traceback.print_exc()
            # Crear imagen de error
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (800, 600), color=(50, 50, 50))
            draw = ImageDraw.Draw(img)
            draw.text((300, 280), "Sin señal de video", fill=(255, 255, 255))
            draw.text((250, 320), f"Error: {str(e)[:50]}", fill=(255, 100, 100))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=80)
            return buffer.getvalue()
    
    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        """Registra un nuevo cliente."""
        self.clients.add(websocket)
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        print(f"✓ Cliente conectado: {client_info} (Total: {len(self.clients)})")
        
    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        """Elimina un cliente."""
        self.clients.discard(websocket)
        print(f"✗ Cliente desconectado (Total: {len(self.clients)})")
    
    async def broadcast_frame(self):
        """Envía frames a todos los clientes conectados."""
        while self.running:
            if self.clients:
                try:
                    # Capturar pantalla
                    frame_data = await asyncio.get_event_loop().run_in_executor(
                        None, self.capture_screen
                    )
                    
                    # Codificar en base64
                    frame_b64 = base64.b64encode(frame_data).decode('utf-8')
                    message = f"data:image/jpeg;base64,{frame_b64}"
                    
                    # Enviar a todos los clientes
                    websockets_to_remove = set()
                    for client in self.clients.copy():
                        try:
                            await client.send(message)
                        except websockets.exceptions.ConnectionClosed:
                            websockets_to_remove.add(client)
                        except Exception as e:
                            print(f"Error enviando a cliente: {e}")
                            websockets_to_remove.add(client)
                    
                    # Limpiar clientes desconectados
                    for ws in websockets_to_remove:
                        await self.unregister_client(ws)
                        
                except Exception as e:
                    print(f"Error en broadcast: {e}")
            
            # Control de FPS
            await asyncio.sleep(1 / self.fps)
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        """Maneja la conexión de un cliente."""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                # Manejar mensajes del cliente (ping/pong, comandos, etc.)
                if message == "ping":
                    await websocket.send("pong")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def start(self):
        """Inicia el servidor de streaming."""
        self.running = True

        # Configurar SSL si se proporcionaron certificados
        ssl_context = None
        protocol = "ws"
        if self.ssl_certfile and self.ssl_keyfile:
            import ssl
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)
            protocol = "wss"

        print("=" * 60)
        print("  EMISOR DE VIDEO EN TIEMPO REAL")
        print("=" * 60)
        print(f"  Host: {self.host}")
        print(f"  Puerto: {self.port}")
        print(f"  FPS: {self.fps}")
        print(f"  Calidad JPEG: {self.quality}%")
        print(f"  SSL: {'Habilitado' if ssl_context else 'Deshabilitado'}")
        print("=" * 60)
        print(f"\n  WebSocket URL: {protocol}://{self.host}:{self.port}")
        print("\n  Esperando conexiones...\n")

        # Iniciar tarea de broadcast
        broadcast_task = asyncio.create_task(self.broadcast_frame())

        # Iniciar servidor WebSocket con o sin SSL
        async with serve(self.handle_client, self.host, self.port, ssl=ssl_context):
            await asyncio.Future()  # Ejecutar indefinidamente


def main():
    parser = argparse.ArgumentParser(description="Emisor de video en tiempo real")
    parser.add_argument("--host", default="0.0.0.0", help="Host del servidor (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8765, help="Puerto del servidor (default: 8765)")
    parser.add_argument("--fps", type=int, default=15, help="Frames por segundo (default: 15)")
    parser.add_argument("--quality", type=int, default=50, help="Calidad JPEG 1-100 (default: 50)")
    
    args = parser.parse_args()
    
    streamer = ScreenStreamer(
        host=args.host,
        port=args.port,
        fps=args.fps,
        quality=args.quality
    )
    
    try:
        asyncio.run(streamer.start())
    except KeyboardInterrupt:
        print("\n\nServidor detenido.")


if __name__ == "__main__":
    main()
