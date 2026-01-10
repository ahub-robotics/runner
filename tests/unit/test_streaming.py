"""
Unit tests for streaming module.

Tests ScreenStreamer, capture utilities, and Celery tasks.
"""
import time
from unittest.mock import MagicMock, Mock, patch, AsyncMock
import pytest


# ============================================================================
# Tests for streaming.streamer
# ============================================================================

class TestScreenStreamer:
    """Tests for ScreenStreamer class."""

    def test_streamer_init(self):
        """Test ScreenStreamer initialization."""
        from streaming.streamer import ScreenStreamer

        streamer = ScreenStreamer(
            host="localhost",
            port=8765,
            fps=15,
            quality=50
        )

        assert streamer.host == "localhost"
        assert streamer.port == 8765
        assert streamer.fps == 15
        assert streamer.quality == 50
        assert streamer.running is False
        assert len(streamer.clients) == 0

    def test_streamer_is_running(self):
        """Test is_running property."""
        from streaming.streamer import ScreenStreamer

        streamer = ScreenStreamer()
        assert streamer.is_running is False

        streamer.running = True
        assert streamer.is_running is True

    def test_streamer_stop(self):
        """Test stopping streamer."""
        from streaming.streamer import ScreenStreamer

        streamer = ScreenStreamer()
        streamer.running = True
        streamer.stop()

        assert streamer.running is False

    @patch('mss.mss')
    @patch('PIL.Image')
    def test_capture_screen_success(self, mock_image, mock_mss):
        """Test successful screen capture."""
        from streaming.streamer import ScreenStreamer

        # Mock screenshot
        mock_screenshot = MagicMock()
        mock_screenshot.size = (1920, 1080)
        mock_screenshot.bgra = b'fake_image_data' * 1000

        # Mock mss
        mock_sct = MagicMock()
        mock_sct.monitors = [{'top': 0, 'left': 0, 'width': 1920, 'height': 1080}]
        mock_sct.grab.return_value = mock_screenshot
        mock_mss.return_value.__enter__.return_value = mock_sct

        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.width = 1920
        mock_img.height = 1080
        mock_image.frombytes.return_value = mock_img

        # Mock resize
        mock_resized = MagicMock()
        mock_img.resize.return_value = mock_resized

        # Mock save
        import io
        mock_buffer = io.BytesIO(b'fake_jpeg_data')
        with patch('io.BytesIO', return_value=mock_buffer):
            streamer = ScreenStreamer()
            result = streamer.capture_screen()

        assert result is not None
        assert isinstance(result, bytes)

    @patch('mss.mss')
    def test_capture_screen_error(self, mock_mss):
        """Test screen capture with error."""
        from streaming.streamer import ScreenStreamer

        # Make mss raise an exception
        mock_mss.side_effect = Exception("Screen capture failed")

        streamer = ScreenStreamer()
        result = streamer.capture_screen()

        # Should return error image
        assert result is not None
        assert isinstance(result, bytes)


# ============================================================================
# Tests for streaming.capture
# ============================================================================

class TestCapture:
    """Tests for capture utility functions."""

    def test_create_error_image(self):
        """Test creating error image."""
        from streaming.capture import create_error_image

        result = create_error_image("Test error", size=(800, 600))
        
        assert result is not None
        assert isinstance(result, bytes)

    def test_encode_frame_base64(self):
        """Test encoding frame to base64."""
        from streaming.capture import encode_frame_base64

        frame_bytes = b'fake_jpeg_data'
        result = encode_frame_base64(frame_bytes)

        assert result.startswith('data:image/jpeg;base64,')
        assert len(result) > len('data:image/jpeg;base64,')

    @patch('PIL.Image')
    def test_resize_image_large(self, mock_image_module):
        """Test resizing large image."""
        from streaming.capture import resize_image

        # Mock image
        mock_img = MagicMock()
        mock_img.width = 2000
        mock_img.height = 1500

        # Mock resized image
        mock_resized = MagicMock()
        mock_img.resize.return_value = mock_resized

        # Mock Image.Resampling
        mock_image_module.Resampling.LANCZOS = 1

        result = resize_image(mock_img, max_width=1280)

        # Should call resize
        mock_img.resize.assert_called_once()
        assert result == mock_resized

    def test_resize_image_small(self):
        """Test not resizing small image."""
        from streaming.capture import resize_image

        # Mock image
        mock_img = MagicMock()
        mock_img.width = 800
        mock_img.height = 600

        result = resize_image(mock_img, max_width=1280)

        # Should not resize
        assert result == mock_img

    @patch('mss.mss')
    @patch('PIL.Image')
    def test_capture_screen_mss_success(self, mock_image, mock_mss):
        """Test screen capture with mss."""
        from streaming.capture import capture_screen_mss

        # Mock screenshot
        mock_screenshot = MagicMock()
        mock_screenshot.size = (1920, 1080)
        mock_screenshot.bgra = b'fake_data' * 1000

        # Mock mss
        mock_sct = MagicMock()
        mock_sct.monitors = [{'top': 0, 'left': 0, 'width': 1920, 'height': 1080}]
        mock_sct.grab.return_value = mock_screenshot
        mock_mss.return_value.__enter__.return_value = mock_sct

        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.width = 800
        mock_image.frombytes.return_value = mock_img

        # Mock save
        import io
        mock_buffer = io.BytesIO(b'fake_jpeg')
        with patch('io.BytesIO', return_value=mock_buffer):
            result = capture_screen_mss(quality=50)

        assert result is not None
        assert isinstance(result, bytes)

    @patch('mss.mss')
    def test_capture_screen_mss_error(self, mock_mss):
        """Test screen capture error handling."""
        from streaming.capture import capture_screen_mss

        # Make mss raise exception
        mock_mss.side_effect = Exception("Capture failed")

        result = capture_screen_mss()

        assert result is None


# ============================================================================
# Tests for streaming.tasks
# ============================================================================

class TestStreamingTasks:
    """Tests for Celery streaming tasks."""

    def test_start_streaming_task_success(self, mock_state_backend):
        """Test starting streaming task."""
        from streaming.tasks import start_streaming_task

        with patch('shared.state.state.get_state_manager') as mock_get_manager, \
             patch('time.sleep') as mock_sleep:  # Mock sleep to avoid blocking

            mock_manager = MagicMock()
            mock_manager.hgetall.return_value = {}  # No active streaming
            mock_manager.hset.return_value = None

            # Make the loop exit immediately by triggering stop_requested
            mock_manager.get.side_effect = [
                None,  # First check (no stop requested)
                'true'  # Second check (stop requested)
            ]

            mock_get_manager.return_value = mock_manager

            # Call task's run method
            result = start_streaming_task.run(
                host='0.0.0.0',
                port=8765,
                fps=15,
                quality=50
            )

            assert result['status'] == 'stopped'
            assert 'message' in result
            mock_manager.hset.assert_called()

    def test_start_streaming_task_already_running(self):
        """Test starting streaming when already active."""
        from streaming.tasks import start_streaming_task

        with patch('shared.state.state.get_state_manager') as mock_get_manager:

            mock_manager = MagicMock()
            # Simulate active streaming
            mock_manager.hgetall.return_value = {'active': 'true'}
            mock_get_manager.return_value = mock_manager

            result = start_streaming_task.run()

            assert result['status'] == 'already_running'
            assert 'message' in result

    def test_start_streaming_task_error(self):
        """Test streaming task error handling."""
        from streaming.tasks import start_streaming_task

        with patch('shared.state.state.get_state_manager') as mock_get_manager:

            # Make get_state_manager raise exception
            mock_get_manager.side_effect = Exception("State error")

            result = start_streaming_task.run()

            assert result['status'] == 'error'
            assert 'message' in result

    def test_stop_streaming_task_success(self):
        """Test stopping streaming task."""
        from streaming.tasks import stop_streaming_task

        with patch('shared.state.state.get_state_manager') as mock_get_manager:

            mock_manager = MagicMock()
            # Simulate active streaming
            mock_manager.hgetall.return_value = {'active': 'true'}
            mock_manager.set.return_value = None
            mock_get_manager.return_value = mock_manager

            result = stop_streaming_task.run()

            assert result['status'] == 'stopping'
            assert 'message' in result
            mock_manager.set.assert_called_with('streaming:stop_requested', 'true')

    def test_stop_streaming_task_not_running(self):
        """Test stopping when no streaming active."""
        from streaming.tasks import stop_streaming_task

        with patch('shared.state.state.get_state_manager') as mock_get_manager:

            mock_manager = MagicMock()
            # No active streaming
            mock_manager.hgetall.return_value = {}
            mock_get_manager.return_value = mock_manager

            result = stop_streaming_task.run()

            assert result['status'] == 'not_running'

    def test_get_streaming_status_active(self):
        """Test getting status when streaming is active."""
        from streaming.tasks import get_streaming_status

        with patch('shared.state.state.get_state_manager') as mock_get_manager:

            mock_manager = MagicMock()
            mock_manager.hgetall.return_value = {
                'active': 'true',
                'task_id': 'task123',
                'host': '0.0.0.0',
                'port': '8765',
                'fps': '15',
                'quality': '50',
                'started_at': '1234567890.0'
            }
            mock_get_manager.return_value = mock_manager

            result = get_streaming_status.run()

            assert result['active'] is True
            assert result['task_id'] == 'task123'
            assert result['port'] == 8765
            assert result['fps'] == 15
            assert result['quality'] == 50

    def test_get_streaming_status_inactive(self):
        """Test getting status when no streaming."""
        from streaming.tasks import get_streaming_status

        with patch('shared.state.state.get_state_manager') as mock_get_manager:

            mock_manager = MagicMock()
            mock_manager.hgetall.return_value = {}
            mock_get_manager.return_value = mock_manager

            result = get_streaming_status.run()

            assert result['active'] is False
            assert result['clients'] == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestStreamingIntegration:
    """Integration tests for streaming module."""

    def test_imports_work(self):
        """Test that all imports work correctly."""
        from streaming import ScreenStreamer
        from streaming import tasks
        from streaming import capture

        assert ScreenStreamer is not None
        assert tasks is not None
        assert capture is not None

    def test_streaming_exports(self):
        """Test module exports."""
        import streaming

        assert hasattr(streaming, 'ScreenStreamer')
        assert 'ScreenStreamer' in streaming.__all__
