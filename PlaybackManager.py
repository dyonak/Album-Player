"""
Playback Manager for Album Player.

Orchestrates audio output selection and playback routing.
Supports multiple output types (Sonos, Bluetooth) and is designed
to be extensible for future music sources (Apple Music, YouTube, etc.)
"""

from typing import Optional, Dict, Any, List
from AudioController import AudioController
from SonosController import SonosController
from BluetoothController import BluetoothController


class PlaybackManager:
    """
    Manages playback across multiple audio outputs.

    Selection logic:
    1. If Bluetooth speaker is connected -> use Bluetooth
    2. Otherwise -> use Sonos (default)

    This can be extended to support:
    - User preference override
    - Multiple Bluetooth devices
    - Other outputs (HDMI, line out, etc.)
    """

    def __init__(self):
        self._sonos: Optional[SonosController] = None
        self._bluetooth: Optional[BluetoothController] = None
        self._active_controller: Optional[AudioController] = None
        self._output_preference: Optional[str] = None  # 'sonos', 'bluetooth', or None (auto)

        self._initialize_controllers()

    def _initialize_controllers(self) -> None:
        """Initialize available audio controllers."""
        # Initialize Sonos (always available as fallback)
        try:
            self._sonos = SonosController()
            print(f"Sonos controller initialized: {self._sonos.is_connected()}")
        except Exception as e:
            print(f"Failed to initialize Sonos controller: {e}")
            self._sonos = None

        # Initialize Bluetooth controller
        try:
            self._bluetooth = BluetoothController()
            print(f"Bluetooth controller initialized: {self._bluetooth.is_connected()}")
        except Exception as e:
            print(f"Failed to initialize Bluetooth controller: {e}")
            self._bluetooth = None

        # Select initial active controller
        self._select_active_controller()

    def _select_active_controller(self) -> None:
        """Select the active controller based on availability and preference."""
        # Check user preference first
        if self._output_preference == 'bluetooth' and self._bluetooth and self._bluetooth.is_connected():
            self._active_controller = self._bluetooth
            print("Using Bluetooth output (user preference)")
            return
        elif self._output_preference == 'sonos' and self._sonos and self._sonos.is_connected():
            self._active_controller = self._sonos
            print("Using Sonos output (user preference)")
            return

        # Auto-select: Bluetooth if connected, otherwise Sonos
        if self._bluetooth and self._bluetooth.is_connected():
            self._active_controller = self._bluetooth
            print("Using Bluetooth output (auto-selected)")
        elif self._sonos and self._sonos.is_connected():
            self._active_controller = self._sonos
            print("Using Sonos output (auto-selected)")
        else:
            self._active_controller = None
            print("Warning: No audio output available")

    def refresh_outputs(self) -> None:
        """Re-check available outputs and update selection."""
        # Refresh Bluetooth connection status
        if self._bluetooth:
            self._bluetooth.refresh_connection()

        # Re-select active controller
        self._select_active_controller()

    def set_output_preference(self, output: Optional[str]) -> bool:
        """
        Set preferred output type.

        Args:
            output: 'sonos', 'bluetooth', or None for auto-select

        Returns:
            True if preference was set and output is available
        """
        if output not in (None, 'sonos', 'bluetooth'):
            print(f"Invalid output preference: {output}")
            return False

        self._output_preference = output
        self._select_active_controller()
        return self._active_controller is not None

    def get_output_preference(self) -> Optional[str]:
        """Get current output preference."""
        return self._output_preference

    def get_active_output(self) -> Optional[str]:
        """Get the name of the currently active output."""
        if self._active_controller is None:
            return None
        elif self._active_controller == self._sonos:
            return 'sonos'
        elif self._active_controller == self._bluetooth:
            return 'bluetooth'
        return None

    def get_available_outputs(self) -> List[Dict[str, Any]]:
        """Get list of available outputs with their status."""
        outputs = []

        if self._sonos:
            outputs.append({
                'type': 'sonos',
                'name': 'Sonos Speaker',
                'connected': self._sonos.is_connected(),
                'active': self._active_controller == self._sonos
            })

        if self._bluetooth:
            bt_device = self._bluetooth.get_connected_device()
            outputs.append({
                'type': 'bluetooth',
                'name': bt_device.name if bt_device else 'Bluetooth Speaker',
                'connected': self._bluetooth.is_connected(),
                'active': self._active_controller == self._bluetooth
            })

        return outputs

    # Delegate playback methods to active controller

    def play(self) -> None:
        """Resume playback."""
        if self._active_controller:
            self._active_controller.play()

    def pause(self) -> None:
        """Pause playback."""
        if self._active_controller:
            self._active_controller.pause()

    def stop(self) -> None:
        """Stop playback."""
        if self._active_controller:
            self._active_controller.stop()

    def next(self) -> None:
        """Skip to next track."""
        if self._active_controller:
            self._active_controller.next()

    def previous(self) -> None:
        """Go to previous track."""
        if self._active_controller:
            self._active_controller.previous()

    def volume(self, level: int) -> None:
        """Set volume level (0-100)."""
        if self._active_controller:
            self._active_controller.volume(level)

    def play_album(self, uri: str) -> None:
        """Play an album from its URI."""
        # Refresh output selection before playing
        self.refresh_outputs()

        if self._active_controller:
            self._active_controller.play_album(uri)
        else:
            print("Error: No audio output available for playback")

    def play_mp3(self, url: str) -> None:
        """Play an MP3 file from a URL."""
        if self._active_controller:
            self._active_controller.play_mp3(url)

    def now_playing(self) -> Dict[str, Any]:
        """Get information about the currently playing track."""
        if self._active_controller:
            return self._active_controller.now_playing()
        return {}

    def get_state(self) -> Optional[str]:
        """Get the current playback state."""
        if self._active_controller:
            return self._active_controller.get_state()
        return None

    def is_connected(self) -> bool:
        """Check if any output is connected."""
        return self._active_controller is not None and self._active_controller.is_connected()
