"""
Bluetooth audio controller for Album Player.

Handles playback through Bluetooth speakers using:
- BluetoothManager for device connection
- SpotifyClient for Spotify API playback control
- spotifyd as Spotify Connect receiver
- PulseAudio for audio routing to Bluetooth sink
"""

import subprocess
import time
from typing import Optional, Dict, Any
from AudioController import AudioController
from BluetoothManager import BluetoothManager, BluetoothDevice

# SpotifyClient is optional
try:
    from SpotifyClient import SpotifyClient
    SPOTIFY_API_AVAILABLE = True
except ImportError:
    SPOTIFY_API_AVAILABLE = False
    SpotifyClient = None


class BluetoothController(AudioController):
    """
    Audio controller for Bluetooth speakers.

    Uses SpotifyClient to control playback via Spotify API, with spotifyd
    as the Spotify Connect receiver. Audio routes through PulseAudio
    to the connected Bluetooth speaker.
    """

    def __init__(self):
        self._bt_manager = BluetoothManager()
        self._connected_device: Optional[BluetoothDevice] = None
        self._spotify: Optional['SpotifyClient'] = None
        self._spotify_device_id: Optional[str] = None
        self._spotifyd_running = False

        # Check initial state
        self.refresh_connection()
        self._check_spotifyd()
        self._init_spotify_client()

    def _init_spotify_client(self) -> None:
        """Initialize Spotify API client."""
        if not SPOTIFY_API_AVAILABLE:
            print("SpotifyClient not available")
            return

        try:
            self._spotify = SpotifyClient()
            if self._spotify.is_authenticated():
                print("Spotify API authenticated")
                # Try to find the spotifyd device
                self._find_spotify_device()
            else:
                print("Spotify API not authenticated - run setup first")
        except Exception as e:
            print(f"Spotify client init failed: {e}")
            self._spotify = None

    def _find_spotify_device(self) -> Optional[str]:
        """Find the spotifyd device in Spotify Connect devices."""
        if not self._spotify:
            return None

        devices = self._spotify.get_devices()
        for device in devices:
            # spotifyd appears as "Album Player" (from spotifyd.conf)
            if "album player" in device.get('name', '').lower():
                self._spotify_device_id = device['id']
                print(f"Found Spotify device: {device['name']} ({device['id']})")
                return device['id']

        print("Spotify device 'Album Player' not found - is spotifyd running?")
        return None

    def refresh_connection(self) -> None:
        """Refresh Bluetooth connection status."""
        self._connected_device = self._bt_manager.get_connected_device()
        if self._connected_device:
            print(f"Bluetooth connected to: {self._connected_device.name}")
            self._set_bluetooth_audio_sink()

    def _check_spotifyd(self) -> bool:
        """Check if spotifyd is running."""
        try:
            result = subprocess.run(
                ["pgrep", "-x", "spotifyd"],
                capture_output=True,
                timeout=5
            )
            self._spotifyd_running = result.returncode == 0
            return self._spotifyd_running
        except:
            self._spotifyd_running = False
            return False

    def _start_spotifyd(self) -> bool:
        """Start spotifyd if not running."""
        if self._check_spotifyd():
            return True

        try:
            subprocess.Popen(
                ["spotifyd", "--no-daemon"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(3)  # Give it time to start and register
            return self._check_spotifyd()
        except FileNotFoundError:
            print("spotifyd not installed")
            return False
        except Exception as e:
            print(f"Failed to start spotifyd: {e}")
            return False

    def _set_bluetooth_audio_sink(self) -> bool:
        """Set the Bluetooth device as the default PulseAudio sink."""
        if not self._connected_device:
            return False

        try:
            result = subprocess.run(
                ["pactl", "list", "short", "sinks"],
                capture_output=True,
                text=True,
                timeout=5
            )

            bt_sink = None
            mac_formatted = self._connected_device.address.replace(":", "_")

            for line in result.stdout.split('\n'):
                if 'bluez' in line.lower() or mac_formatted in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        bt_sink = parts[1]
                        break

            if bt_sink:
                subprocess.run(
                    ["pactl", "set-default-sink", bt_sink],
                    timeout=5
                )
                print(f"Set Bluetooth audio sink: {bt_sink}")
                return True
            else:
                print("Bluetooth audio sink not found in PulseAudio")
                return False

        except Exception as e:
            print(f"Failed to set Bluetooth sink: {e}")
            return False

    def get_connected_device(self) -> Optional[BluetoothDevice]:
        """Get the currently connected Bluetooth device."""
        return self._connected_device

    def is_connected(self) -> bool:
        """
        Check if Bluetooth playback is available.

        Returns True only if:
        - Bluetooth speaker is connected
        - Spotify API is authenticated
        - spotifyd is running (or can be started)
        """
        self.refresh_connection()

        if not self._connected_device:
            return False

        if not self._spotify or not self._spotify.is_authenticated():
            print("Bluetooth connected but Spotify API not ready")
            return False

        return True

    def is_ready(self) -> bool:
        """Check if all components are ready for playback."""
        return (
            self._connected_device is not None and
            self._spotify is not None and
            self._spotify.is_authenticated() and
            self._spotifyd_running
        )

    def play(self) -> None:
        """Resume playback."""
        if self._spotify:
            self._spotify.play()

    def pause(self) -> None:
        """Pause playback."""
        if self._spotify:
            self._spotify.pause()

    def stop(self) -> None:
        """Stop playback."""
        if self._spotify:
            self._spotify.pause()

    def next(self) -> None:
        """Skip to next track."""
        if self._spotify:
            self._spotify.next_track()

    def previous(self) -> None:
        """Go to previous track."""
        if self._spotify:
            self._spotify.previous_track()

    def volume(self, level: int) -> None:
        """Set volume level (0-100)."""
        if self._spotify:
            self._spotify.set_volume(level)

    def play_album(self, uri: str) -> None:
        """
        Play an album via Spotify API on the spotifyd device.

        Args:
            uri: Spotify album URI or URL
        """
        if not self.is_connected():
            print("Bluetooth playback not available")
            return

        # Ensure spotifyd is running
        if not self._start_spotifyd():
            print("Cannot play: spotifyd not available")
            return

        # Find or refresh the Spotify device
        if not self._spotify_device_id:
            self._find_spotify_device()

        if not self._spotify_device_id:
            print("Cannot find spotifyd in Spotify devices")
            print("Tip: Open Spotify app and check if 'Album Player' device is visible")
            return

        # Ensure audio routes to Bluetooth
        self._set_bluetooth_audio_sink()

        # Play via Spotify API
        print(f"Playing via Bluetooth: {uri}")
        success = self._spotify.play_album(uri, device_id=self._spotify_device_id)

        if not success:
            print("Spotify API playback failed")

    def play_mp3(self, url: str) -> None:
        """
        Play an MP3 file from a URL.

        Uses mpv for local playback routed to Bluetooth.
        """
        if not self._connected_device:
            print("No Bluetooth speaker connected")
            return

        self._set_bluetooth_audio_sink()

        # Try mpv first, then ffplay
        for player in ["mpv", "ffplay"]:
            try:
                if player == "mpv":
                    subprocess.Popen(
                        ["mpv", "--no-video", "--really-quiet", url],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    subprocess.Popen(
                        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", url],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                print(f"Playing MP3 via {player}")
                return
            except FileNotFoundError:
                continue

        print("No MP3 player available (install mpv or ffmpeg)")

    def now_playing(self) -> Dict[str, Any]:
        """Get information about the currently playing track."""
        if self._spotify:
            return self._spotify.get_currently_playing()
        return {}

    def get_state(self) -> Optional[str]:
        """Get the current playback state."""
        if not self._spotify:
            return None

        playback = self._spotify.get_current_playback()
        if not playback:
            return None

        if playback.get('is_playing'):
            return "PLAYING"
        else:
            return "PAUSED"

    def clear_queue(self) -> None:
        """Clear the playback queue (not directly supported)."""
        pass


if __name__ == "__main__":
    # Test the Bluetooth controller
    print("Testing Bluetooth Controller")
    print("=" * 40)

    bt = BluetoothController()

    print(f"\nBluetooth device connected: {bt._connected_device is not None}")
    if bt._connected_device:
        print(f"  Device: {bt._connected_device.name}")

    print(f"Spotify API authenticated: {bt._spotify and bt._spotify.is_authenticated()}")
    print(f"spotifyd running: {bt._spotifyd_running}")
    print(f"Spotify device ID: {bt._spotify_device_id}")

    print(f"\nis_connected (ready for playback): {bt.is_connected()}")

    if bt._spotify and bt._spotify.is_authenticated():
        print("\nAvailable Spotify devices:")
        for device in bt._spotify.get_devices():
            active = " (active)" if device.get('is_active') else ""
            print(f"  - {device['name']} ({device['type']}){active}")
