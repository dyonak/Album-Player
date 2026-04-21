"""
Spotify Web API client for Album Player.

Handles OAuth authentication and playback control for Spotify Connect devices.
This enables playing albums on local devices (like spotifyd) via the Spotify API.

Note: Requires Spotify Premium for playback control.
"""

import os
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional, Dict, List, Any
import config


class SpotifyClient:
    """
    Spotify Web API client for controlling playback.

    Uses OAuth for user authentication. On first run, user must authorize
    via browser. Tokens are cached for subsequent runs.
    """

    # Spotify API scopes needed for playback control
    SCOPES = [
        "user-read-playback-state",
        "user-modify-playback-state",
        "user-read-currently-playing"
    ]

    def __init__(self, cache_path: str = ".spotify_cache", redirect_uri: str = None):
        self._config = config.Config()
        self._cache_path = cache_path
        self._sp: Optional[spotipy.Spotify] = None
        self._device_id: Optional[str] = None

        # Redirect URI - configurable via parameter, config, or env var
        # IMPORTANT: This must match exactly what's in your Spotify Developer Dashboard
        self._redirect_uri = redirect_uri or self._get_redirect_uri()

        self._initialize()

    def _get_redirect_uri(self) -> str:
        """Get redirect URI from config or environment."""
        # Check environment variable first
        if os.environ.get('SPOTIFY_REDIRECT_URI'):
            return os.environ.get('SPOTIFY_REDIRECT_URI')

        # Check config
        uri = getattr(self._config, 'spotify_redirect_uri', None)
        if uri:
            return uri

        # Default - use http://127.0.0.1 (Spotify allows HTTP for localhost/127.0.0.1)
        # Note: The redirect goes to your browser machine, not the Pi.
        # You'll need to copy the code from the URL after authorization.
        return "http://127.0.0.1:8888/callback"

    def _initialize(self) -> None:
        """Initialize Spotify client with OAuth."""
        try:
            # Get credentials from config
            client_id = getattr(self._config, 'service_api_id', None)
            client_secret = getattr(self._config, 'service_api_secret', None)

            if not client_id or not client_secret:
                print("Spotify API credentials not found in config")
                return

            redirect_uri = self._redirect_uri
            print(f"Spotify redirect URI: {redirect_uri}")

            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=" ".join(self.SCOPES),
                cache_path=self._cache_path,
                open_browser=False  # Don't auto-open browser on headless device
            )

            self._sp = spotipy.Spotify(auth_manager=auth_manager)

            # Test connection
            try:
                self._sp.current_user()
                print("Spotify API connected successfully")
            except spotipy.SpotifyException as e:
                if "token" in str(e).lower() or "auth" in str(e).lower():
                    print("Spotify OAuth not authorized yet. Run authorize_spotify() to set up.")
                    self._sp = None
                else:
                    raise

        except Exception as e:
            print(f"Spotify client initialization failed: {e}")
            self._sp = None

    def is_authenticated(self) -> bool:
        """Check if we have valid Spotify authentication."""
        if not self._sp:
            return False
        try:
            self._sp.current_user()
            return True
        except:
            return False

    def get_redirect_uri(self) -> str:
        """Get the redirect URI being used."""
        return self._redirect_uri

    def get_auth_url(self) -> Optional[str]:
        """Get the OAuth authorization URL for user to visit."""
        try:
            client_id = getattr(self._config, 'service_api_id', None)
            client_secret = getattr(self._config, 'service_api_secret', None)

            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=self._redirect_uri,
                scope=" ".join(self.SCOPES),
                cache_path=self._cache_path,
                open_browser=False
            )

            return auth_manager.get_authorize_url()
        except Exception as e:
            print(f"Error getting auth URL: {e}")
            return None

    def complete_auth(self, auth_code: str) -> bool:
        """Complete OAuth flow with authorization code."""
        try:
            client_id = getattr(self._config, 'service_api_id', None)
            client_secret = getattr(self._config, 'service_api_secret', None)

            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=self._redirect_uri,
                scope=" ".join(self.SCOPES),
                cache_path=self._cache_path,
                open_browser=False
            )

            # Exchange code for token
            auth_manager.get_access_token(auth_code)

            # Reinitialize with the new token
            self._sp = spotipy.Spotify(auth_manager=auth_manager)

            # Test
            self._sp.current_user()
            print("Spotify OAuth completed successfully")
            return True

        except Exception as e:
            print(f"OAuth completion failed: {e}")
            return False

    def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of available Spotify Connect devices."""
        if not self._sp:
            return []

        try:
            result = self._sp.devices()
            return result.get('devices', [])
        except Exception as e:
            print(f"Error getting devices: {e}")
            return []

    def find_device(self, name_contains: str = "Album Player") -> Optional[Dict[str, Any]]:
        """Find a Spotify Connect device by name."""
        devices = self.get_devices()
        for device in devices:
            if name_contains.lower() in device.get('name', '').lower():
                return device
        return None

    def transfer_playback(self, device_id: str, force_play: bool = False) -> bool:
        """Transfer playback to a specific device."""
        if not self._sp:
            return False

        try:
            self._sp.transfer_playback(device_id=device_id, force_play=force_play)
            self._device_id = device_id
            return True
        except Exception as e:
            print(f"Error transferring playback: {e}")
            return False

    def play_album(self, uri: str, device_id: Optional[str] = None) -> bool:
        """
        Play an album on a Spotify Connect device.

        Args:
            uri: Spotify album URI (spotify:album:xxx) or URL
            device_id: Target device ID (uses cached device if not specified)

        Returns:
            True if playback started successfully
        """
        if not self._sp:
            print("Spotify client not authenticated")
            return False

        # Normalize URI
        spotify_uri = self._normalize_uri(uri)
        if not spotify_uri:
            print(f"Invalid Spotify URI: {uri}")
            return False

        # Use provided device_id or cached one
        target_device = device_id or self._device_id

        try:
            # Start playback
            self._sp.start_playback(
                device_id=target_device,
                context_uri=spotify_uri
            )
            print(f"Playing {spotify_uri} on device {target_device}")
            return True

        except spotipy.SpotifyException as e:
            if "NO_ACTIVE_DEVICE" in str(e):
                print("No active Spotify device. Please open Spotify on a device first.")
            elif "PREMIUM_REQUIRED" in str(e):
                print("Spotify Premium required for playback control.")
            else:
                print(f"Playback error: {e}")
            return False
        except Exception as e:
            print(f"Error starting playback: {e}")
            return False

    def _normalize_uri(self, uri: str) -> Optional[str]:
        """Convert various Spotify URI formats to spotify:type:id format."""
        if uri.startswith("spotify:"):
            return uri

        # Handle https://open.spotify.com/album/xxx format
        if "open.spotify.com" in uri:
            parts = uri.rstrip('/').split('/')
            if len(parts) >= 2:
                item_type = parts[-2]
                item_id = parts[-1].split('?')[0]
                return f"spotify:{item_type}:{item_id}"

        return None

    def pause(self) -> bool:
        """Pause playback."""
        if not self._sp:
            return False
        try:
            self._sp.pause_playback(device_id=self._device_id)
            return True
        except:
            return False

    def play(self) -> bool:
        """Resume playback."""
        if not self._sp:
            return False
        try:
            self._sp.start_playback(device_id=self._device_id)
            return True
        except:
            return False

    def next_track(self) -> bool:
        """Skip to next track."""
        if not self._sp:
            return False
        try:
            self._sp.next_track(device_id=self._device_id)
            return True
        except:
            return False

    def previous_track(self) -> bool:
        """Go to previous track."""
        if not self._sp:
            return False
        try:
            self._sp.previous_track(device_id=self._device_id)
            return True
        except:
            return False

    def set_volume(self, volume_percent: int) -> bool:
        """Set volume (0-100)."""
        if not self._sp:
            return False
        try:
            self._sp.volume(volume_percent, device_id=self._device_id)
            return True
        except:
            return False

    def get_current_playback(self) -> Optional[Dict[str, Any]]:
        """Get current playback state."""
        if not self._sp:
            return None
        try:
            return self._sp.current_playback()
        except:
            return None

    def get_currently_playing(self) -> Dict[str, Any]:
        """Get currently playing track info."""
        if not self._sp:
            return {}

        try:
            result = self._sp.current_playback()
            if not result or not result.get('item'):
                return {}

            item = result['item']
            return {
                'title': item.get('name', 'Unknown'),
                'artist': ', '.join(a['name'] for a in item.get('artists', [])),
                'album': item.get('album', {}).get('name', 'Unknown'),
                'uri': item.get('uri', ''),
                'position': str(result.get('progress_ms', 0) // 1000),
                'duration': str(item.get('duration_ms', 0) // 1000),
                'is_playing': result.get('is_playing', False)
            }
        except Exception as e:
            print(f"Error getting current playback: {e}")
            return {}


if __name__ == "__main__":
    # Test/setup script
    client = SpotifyClient()

    if not client.is_authenticated():
        print("\nSpotify OAuth Setup Required")
        print("=" * 40)
        auth_url = client.get_auth_url()
        if auth_url:
            print(f"\n1. Visit this URL in a browser:\n{auth_url}")
            print("\n2. After authorizing, you'll be redirected to localhost:8888/callback")
            print("   Copy the 'code' parameter from the URL")
            print("\n3. Enter the code here:")
            code = input("Code: ").strip()
            if code:
                if client.complete_auth(code):
                    print("Authorization successful!")
                else:
                    print("Authorization failed.")
    else:
        print("Spotify client is authenticated")

        print("\nAvailable devices:")
        for device in client.get_devices():
            active = " (active)" if device.get('is_active') else ""
            print(f"  - {device['name']} ({device['type']}){active}")
