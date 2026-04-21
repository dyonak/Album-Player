"""
Abstract base class for audio output controllers.

This defines the interface that all audio controllers must implement,
allowing the Album Player to work with different output devices
(Sonos, Bluetooth speakers, local audio, etc.)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class AudioController(ABC):
    """Abstract base class for audio playback controllers."""

    @abstractmethod
    def play(self) -> None:
        """Resume playback."""
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause playback."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop playback."""
        pass

    @abstractmethod
    def next(self) -> None:
        """Skip to next track."""
        pass

    @abstractmethod
    def previous(self) -> None:
        """Go to previous track."""
        pass

    @abstractmethod
    def volume(self, level: int) -> None:
        """Set volume level (0-100)."""
        pass

    @abstractmethod
    def play_album(self, uri: str) -> None:
        """
        Play an album from its URI (e.g., Spotify URI).

        Args:
            uri: The album URI (e.g., spotify:album:xxx or https://open.spotify.com/album/xxx)
        """
        pass

    @abstractmethod
    def play_mp3(self, url: str) -> None:
        """
        Play an MP3 file from a URL.
        Used for notification sounds (detected, registered, timeout).

        Args:
            url: URL to the MP3 file
        """
        pass

    @abstractmethod
    def now_playing(self) -> Dict[str, Any]:
        """
        Get information about the currently playing track.

        Returns:
            Dict with keys: title, artist, album, uri, position, duration
        """
        pass

    @abstractmethod
    def get_state(self) -> Optional[str]:
        """
        Get the current playback state.

        Returns:
            One of: 'PLAYING', 'PAUSED', 'STOPPED', or None
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the controller is connected to its output device.

        Returns:
            True if connected and ready to play
        """
        pass

    def clear_queue(self) -> None:
        """Clear the playback queue. Optional - not all controllers need this."""
        pass
