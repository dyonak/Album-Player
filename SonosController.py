from soco import SoCo, discover
from soco.music_services import MusicService
from soco.plugins.sharelink import ShareLinkPlugin
import DBConnector
from time import sleep
import json
import config

class SonosController:
    def __init__(self):
        self.player = None
        self.config = config.Config()
        self.current_track = None
        self.state = None
        self.get_state()
        players = discover()
        self.player = None
        for p in players:
            if p.player_name == self.config.player:
                self.player = p
                break

    def clear_queue(self):
        self.player.clear_queue()

    def play(self):
        self.player.play()
        self.get_state()

    def pause(self):
        try:
          self.player.pause()
          self.get_state()
        except:
          return

    def stop(self):
        self.player.stop()
        self.get_state()

    def next(self):
        self.player.next()

    def previous(self):
        self.player.previous()

    def volume(self, volume):
        self.player.volume = volume
    
    def now_playing(self):
        return self.player.get_current_track_info()

    def play_mp3(self, link):
        self.config.reload()
        self.pause()
        sleep(0.2)
        self.clear_queue()
        sleep(0.2)
        self.volume(self.config.volume)
        sleep(0.2)
        self.player.play_uri(link)

    def get_state(self):
        try:
            transport_info = self.player.get_current_transport_info()
            self.state = transport_info.get('current_transport_state')

            if self.state == 'PLAYING':
                print(f"{sonos.player_name} is currently playing.")
            elif self.state == 'PAUSED_PLAYBACK':
                print(f"{sonos.player_name} is currently paused.")
            elif self.state == 'STOPPED':
                print(f"{sonos.player_name} is currently stopped.")
            elif self.state == 'TRANSITIONING':
                print(f"{sonos.player_name} is transitioning between states.")
            else:
                print(f"Unknown state: {self.state}")
            
            return transport_info

        except:
            return None

    def play_album(self, uri):
        print(self.now_playing()['uri'])
        print(uri)
        self.config.reload()
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
  # sharelink = ShareLinkPlugin(player)
  # sharelink.add_share_link_to_queue("https://open.spotify.com/album/14IYDXybb1XKu51QHDryak")
  # sc.play()
  # sleep(5)
  # sc.pause()

  # album = sc.now_playing()["album"]
  # print(sc.now_playing())

  # service = MusicService(SERVICE)
  # sc.clear_queue()
