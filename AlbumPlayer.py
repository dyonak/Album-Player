#TODO:
# Remove Add Album from web
# Remove non-user relevant config items from web (spotify id/secret)
# Expirement with balega os wifi connect, can this also prompt for a sonos speaker name I can connect to?
# Build a docker image for the config/dependencies/python/wifi connect - ideal state I think?
# Add tracks to the db? Could be good for tracking purposes - which tracks are getting skipped, when albums are removed from player, track play counting
#
#Structure:
#   -NFCPoller.py - Handles NFC polling and tag detection
#   -SonosController.py - Handles Sonos API interactions
#   -SpotifyController.py - Handles Spotify API interactions
#   -AlbumPlayer.py - Main script that integrates everything
#   -DBConnector.py - Handles database connections and queries
#   -config.py - Configuration file for API keys and settings

from time import sleep
import requests
from NFCPoller import NFCPoller
from DBConnector import DBConnector
from Registrar import Registrar
from SonosController import SonosController
import Webapp
import json
import socket

configfile = open('./config.json')
data = json.load(configfile)
SERVICE = data["service"]
VOLUME = data["volume"]
PLAYER = data["player"]
PORT = data["port"]
HOSTNAME = socket.gethostname()

if __name__ == "__main__":

    nfc = NFCPoller()
    db = DBConnector()
    sc = SonosController()
    reg = Registrar()

    while True:
        nfc.poll()
        print(f'Poll complete\nCurrent:{nfc.tag}\nPrevious:{nfc.last_tag}')
        sleep(1.0) #Wait long enough for the device timeout

        #No tag present but previous poll had a tag, album was removed - stop the playing
        if nfc.tag == None and nfc.last_tag:
            print("Stopping!")
            sc.pause()
            continue

        #No tag found, make sure nothing is playing and move on
        if nfc.tag == None:
            continue

        #This is the same tag that's been on the player, no change needed
        if nfc.tag == nfc.last_tag:
            continue
    

        result = reg.lookup_tag(nfc.tag)

        if result != None:
            sc.play_album(result[4])
        else:
            sc.play_mp3(f"http://{HOSTNAME}:3029/audio/detected.mp3")
            album = None
            playing = []
            while not album:
                playing.append(sc.now_playing())
                #Scan currently playing, capture a snapshot when it's playing
                #Wait a few seconds and capture another snapshot
                #If it's the same track and it's been playing consistently add this album
                sleep(3.0)
                if len(playing) > 2 and (int(playing[-1]['position'][-2:]) - int(playing[-3]['position'][-2:])) > 5 and playing[-2]['artist'] == playing[-1]['artist']:
                    #Album has been playing for over 10 seconds, this seems intentional
                    album = reg.lookup_album(playing[-1]['artist'] + " " + playing[-1]['album'])
                    reg.add_album_to_db(album, nfc.tag)
                    sc.play_mp3(f"http://{HOSTNAME}:3029/audio/registered.mp3")

                    #Pause long enough for the registered message to play
                    sleep(5.0)

                    print("Album registered: " + album['artist'] + " " + album['album_name'])
                    result = reg.lookup_tag(nfc.tag)
                    if result != None:
                        sc.play_album(result[4])

                if len(playing) > 30: #We've been waiting over 1.5 minutes, let the user know the registration process has timed out
                    sc.play_mp3(f"http://{HOSTNAME}:3029/audio/timeout.mp3")
                    break