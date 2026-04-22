from soco import SoCo, discover
from soco.plugins.sharelink import ShareLinkPlugin
from AudioController import AudioController
import DBConnector
from time import sleep
from typing import Optional, Dict, Any
import config


class SonosController(AudioController):
    """Audio controller for Sonos speakers."""

    def __init__(self):
        self.player: Optional[SoCo] = None
        self.config = config.Config()
        self.current_track = None
        self.state: Optional[str] = None
        self._discover_player()
        self.get_state()

    def _discover_player(self) -> None:
        """Find and connect to the configured Sonos player."""
        players = discover()
        if players:
            for p in players:
                if p.player_name == self.config.player:
                    self.player = p
                    print(f"Connected to Sonos player: {self.config.player}")
                    break
        if not self.player:
            print(f"Warning: Sonos player '{self.config.player}' not found")

    def is_connected(self) -> bool:
        """Check if connected to a Sonos player."""
        return self.player is not None

    def clear_queue(self) -> None:
        """Clear the Sonos queue."""
        if self.player:
            self.player.clear_queue()

    def play(self) -> None:
        """Resume playback."""
        if self.player:
            self.player.play()
            self.get_state()

    def pause(self) -> None:
        """Pause playback."""
        try:
            if self.player:
                self.player.pause()
                self.get_state()
        except:
            return

    def stop(self) -> None:
        """Stop playback."""
        try:
            if self.player:
                self.player.stop()
                self.get_state()
        except:
            return

    def next(self) -> None:
        """Skip to next track."""
        if self.player:
            self.player.next()

    def previous(self) -> None:
        """Go to previous track."""
        if self.player:
            self.player.previous()

    def volume(self, level: int) -> None:
        """Set volume level (0-100)."""
        if self.player:
            self.player.volume = level

    def now_playing(self) -> Dict[str, Any]:
        """Get information about the currently playing track."""
        if self.player:
            return self.player.get_current_track_info()
        return {}

    def play_mp3(self, link: str) -> None:
        """Play an MP3 file from a URL."""
        if not self.player:
            return
        self.config.reload()
        self.pause()
        sleep(0.2)
        self.clear_queue()
        sleep(0.2)
        self.volume(self.config.volume)
        sleep(0.2)
        self.player.play_uri(link)

    def get_state(self) -> Optional[str]:
        """Get the current playback state."""
        try:
            if not self.player:
                return None
            transport_info = self.player.get_current_transport_info()
            self.state = transport_info.get('current_transport_state')

            if self.state == 'PLAYING':
                print(f"{self.config.player} is currently playing.")
            elif self.state == 'PAUSED_PLAYBACK':
                print(f"{self.config.player} is currently paused.")
            elif self.state == 'STOPPED':
                print(f"{self.config.player} is currently stopped.")
            elif self.state == 'TRANSITIONING':
                print(f"{self.config.player} is transitioning between states.")
            else:
                print(f"Unknown state: {self.state}")

            return self.state
        except:
            return None

    def play_album(self, uri: str) -> None:
        """Play an album from its Spotify URI."""
        self.config.reload()

        # Re-discover if the configured player has changed since startup
        if not self.player or self.player.player_name != self.config.player:
            self._discover_player()

        if not self.player:
            print("No Sonos player connected")
            return

        print(f"Current: {self.now_playing().get('uri', 'None')}")
        print(f"Requested: {uri}")
        self.pause()
        sleep(0.2)
        self.clear_queue()
        sleep(0.2)
        self.stop()
        sleep(0.2)
        self.volume(self.config.volume)
        sleep(0.2)

        sharelink = ShareLinkPlugin(self.player)
        sharelink.add_share_link_to_queue(uri)
        sleep(0.2)
        self.player.play_from_queue(0)

        DBConnector.update_play_count(uri)
        self.get_state()


if __name__ == "__main__":
    sc = SonosController()
    sc.get_state()
    print(sc.state)
    print(sc.now_playing())
