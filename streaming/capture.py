"""
Screen capture utilities for streaming.

This module provides helper functions for screen capture operations
used by the streaming system.
"""
import io
import base64
from typing import Optional, Tuple


def create_error_image(error_message: str, size: Tuple[int, int] = (800, 600)) -> bytes:
    """
    Create an error image with a message.

    Args:
        error_message: Error message to display
        size: Image size as (width, height)

    Returns:
        JPEG image bytes
    """
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", size, color=(50, 50, 50))
        draw = ImageDraw.Draw(img)
        draw.text((size[0]//2 - 100, size[1]//2 - 20), "Sin señal de video", fill=(255, 255, 255))
        draw.text((size[0]//2 - 150, size[1]//2 + 20), f"Error: {error_message[:50]}", fill=(255, 100, 100))

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        return buffer.getvalue()
    except Exception:
        # Fallback: empty JPEG
        return b''


def encode_frame_base64(frame_bytes: bytes) -> str:
    """
    Encode frame bytes as base64 data URL.

    Args:
        frame_bytes: JPEG image bytes

    Returns:
        Base64 encoded data URL string
    """
    frame_b64 = base64.b64encode(frame_bytes).decode('utf-8')
    return f"data:image/jpeg;base64,{frame_b64}"


def resize_image(img, max_width: int = 1280):
    """
    Resize image maintaining aspect ratio.

    Args:
        img: PIL Image object
        max_width: Maximum width for the resized image

    Returns:
        Resized PIL Image
    """
    from PIL import Image

    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        # Use modern Pillow API
        resample_filter = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
        return img.resize(new_size, resample_filter)
    
    return img


def capture_screen_mss(quality: int = 50, max_width: int = 1280) -> Optional[bytes]:
    """
    Capture screen using mss (cross-platform).

    Args:
        quality: JPEG quality (1-100)
        max_width: Maximum width for resizing

    Returns:
        JPEG bytes or None on error
    """
    try:
        import mss
        from PIL import Image

        with mss.mss() as sct:
            monitor = sct.monitors[0]  # Primary monitor
            screenshot = sct.grab(monitor)

            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

            # Resize for better performance
            img = resize_image(img, max_width)

            # Convert to JPEG
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            return buffer.getvalue()

    except Exception as e:
        print(f"Error capturing screen with mss: {e}")
        return None


def capture_screen_pillow(quality: int = 50, max_width: int = 1280) -> Optional[bytes]:
    """
    Capture screen using PIL ImageGrab (fallback).

    Args:
        quality: JPEG quality (1-100)
        max_width: Maximum width for resizing

    Returns:
        JPEG bytes or None on error
    """
    try:
        from PIL import ImageGrab

        # Capture screen
        img = ImageGrab.grab()

        # Resize for better performance
        img = resize_image(img, max_width)

        # Convert to JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        return buffer.getvalue()

    except Exception as e:
        print(f"Error capturing screen with PIL: {e}")
        return None
