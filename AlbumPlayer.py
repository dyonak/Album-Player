# TODO:
# - Add tracks to the db for tracking (skipped tracks, play counting)
# - Improve WiFi provisioning integration
#
#Structure:
#   -NFCPoller.py - Handles NFC polling and tag detection
#   -SonosController.py - Handles Sonos API interactions
#   -SpotifyController.py - Handles Spotify API interactions
#   -AlbumPlayer.py - Main script that integrates everything
#   -DBConnector.py - Handles database connections and queries
#   -config.py - Configuration file for API keys and settings

from time import sleep, time
import requests
from NFCPoller import NFCPoller
from Registrar import Registrar
from PlaybackManager import PlaybackManager
import json
import socket
import config

HOSTNAME = socket.gethostname()
config = config.Config()

if __name__ == "__main__":

    nfc = NFCPoller()
    pm = PlaybackManager()  # Manages Sonos and Bluetooth output selection
    reg = Registrar()

    # Grace period tracking for tag removal
    tag_absent_start_time = None
    GRACE_PERIOD_SECONDS = 5.0
    last_playing_tag = None  # Track the last tag that was actually playing

    while True:
        nfc.poll()
        print(f'Poll complete\nCurrent:{nfc.tag}\nPrevious:{nfc.last_tag}')
        sleep(0.8) #Wait long enough for the device timeout

        #No tag present but there was a tag playing before
        if nfc.tag == None and last_playing_tag:
            # Start the grace period timer if not already started
            if tag_absent_start_time is None:
                tag_absent_start_time = time()
                print(f"Tag removed, starting {GRACE_PERIOD_SECONDS}s grace period...")
            else:
                # Check if grace period has elapsed
                elapsed_time = time() - tag_absent_start_time
                if elapsed_time >= GRACE_PERIOD_SECONDS:
                    print(f"Grace period elapsed ({elapsed_time:.1f}s), stopping!")
                    pm.pause()
                    last_playing_tag = None  # Clear the playing tag
                    tag_absent_start_time = None  # Reset for next time
                else:
                    print(f"Grace period: {elapsed_time:.1f}s / {GRACE_PERIOD_SECONDS}s")
            continue

        # Tag is present again, reset the grace period timer
        if nfc.tag is not None and tag_absent_start_time is not None:
            print("Tag detected again, canceling grace period")
            tag_absent_start_time = None

        #No tag found, make sure nothing is playing and move on
        if nfc.tag == None:
            continue

        #This is the same tag that's been playing, no change needed
        if nfc.tag == last_playing_tag:
            continue
    

        result = reg.lookup_tag(nfc.tag)

        if result != None:
            pm.play_album(result[4])
            last_playing_tag = nfc.tag  # Remember this tag is now playing
        else:
            pm.play_mp3(f"http://{HOSTNAME}:{config.port}/audio/detected.mp3")
            album = None
            playing = []
            while not album:
                playing.append(pm.now_playing())
                #Scan currently playing, capture a snapshot when it's playing
                #Wait a few seconds and capture another snapshot
                #If it's the same track and it's been playing consistently add this album
                sleep(3.0)
                if len(playing) > 2 and (int(playing[-1]['position'][-2:]) - int(playing[-3]['position'][-2:])) > 5 and playing[-2]['artist'] == playing[-1]['artist']:
                    #Album has been playing for over 10 seconds, this seems intentional
                    album = reg.lookup_album(playing[-1]['artist'] + " " + playing[-1]['album'])
                    reg.add_album_to_db(album, nfc.tag)
                    pm.play_mp3(f"http://{HOSTNAME}:{config.port}/audio/registered.mp3")

                    #Pause long enough for the registered message to play
                    sleep(5.0)

                    print("Album registered: " + album['artist'] + " " + album['album_name'])
                    result = reg.lookup_tag(nfc.tag)
                    if result != None:
                        pm.play_album(result[4])
                        last_playing_tag = nfc.tag  # Remember this tag is now playing

                if len(playing) > 30: #We've been waiting over 1.5 minutes, let the user know the registration process has timed out
                    pm.play_mp3(f"http://{HOSTNAME}:{config.port}/audio/timeout.mp3")
                    break