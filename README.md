# NFC album player project

## Products
-PN532 NFC Reader - tried a few, I haven't formed a strong preference on model

-Raspberry Pi - I've run the project on bot a Pi 4 1gb and a Pi Zero 2, recommend using the zero 2 as it's got plenty of resources to cover the need here.

## Steps to Setup
Use Raspberry Pi Imager to setup Pi OS Lite 64

Wire up nfc reader to pi with SPI
http://wiki.sunfounder.cc/index.php?title=PN532_NFC_Module_for_Raspberry_Pi&ref=6doe1gqh2qgn

sudo apt update/upgrade

raspi-config > Interfaces -> Enable SPI

SPI section of the second link (SPI Communication Instructions for Raspberry Pi)
-Substitute the official libnfc from github instead of this  - http://dl.bintray.com/nfc-tools/sources/libnfc-1.7.1.tar.bz2

Install pip

sudo apt install git
mkdir albumplayer
pull down github album-player project (git clone)
python3 -m venv my_venv
source ./my_venv/bin/activate
pip install -r requirements.txt

Test Registrar.py/Webapp.py

Install nfc module
pip install nfcpy
pip3 install adafruit-circuitpython-pn532

At this point the following should work 
```
import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.spi import PN532_SPI

# Create SPI connection
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs_pin = DigitalInOut(board.D8)

# Create an instance of the PN532 class
pn532 = PN532_SPI(spi, cs_pin, debug=False)
ic, ver, rev, support = pn532.firmware_version

print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
# Configure PN532 to communicate with MiFare cards
pn532.SAM_configuration()

print("Waiting for RFID/NFC card...")
while True:
    # Check if a card is available to read
    uid = pn532.read_passive_target(timeout=0.5)
    print(".", end="")
    # Try again if no card is available.
    if uid is None:
        continue
    print("Found card with UID:", [hex(i) for i in uid])
```

The above may have been dependent on another install from
git clone https://github.com/hoanhan101/pn532.git
and the corresponding 'make init' command listed there
-I'd try without it and do this as a last resort if needed

Setup code - pull down this repo, setup venv, pip install -r requirements.txt
Run Webapp.py and check http://album:3029
-Important: On the config tab set the player name for the sonos speaker you want to play albums to. This speaker is also used to play audio files that contain registration instructions.
Run AlbumPlayer.py and scan cards, go through the registration process

Copy albumweb and albumplayer service files to /etc/system/systemd/
-sudo systemctl enable name.service for each of them
-sudo systemctl daemon-reload

Ref:
https://blog.stigok.com/2017/10/12/setting-up-a-pn532-nfc-module-on-a-raspberry-pi-using-i2c.html
http://wiki.sunfounder.cc/index.php?title=PN532_NFC_Module_for_Raspberry_Pi&ref=6doe1gqh2qgn

## Docker setup
Install 64 bit lite os

sudo apt update

sudo apt upgrade

sudo rasip-config > Interfaces > Enable SPI

curl -fsSL https://get.docker.com -o get-docker.sh

chmod +x get-docker.sh

sudo sh ./get-docker.sh

sudo usermod -aG docker [user_name]

exit and reconnect to ssh (needs to be done to re-validate your user's groups)
```
mkdir ~/albumplayerdb && cd ~/albumplayerdb
docker run -d --restart always --privileged --net=host --volume ${PWD}:/app/db dyonak/albumplayer:latest
```

- Verify this by going to hostname.local:3029 in a browser on the same network
- You should also see NFC cards getting read in the output if you put one near the reader



## Usage
All of this is assuming you've built some type of device that allows for an album with an NFC sticker tag, or other similar object with a NFC tag, to be placed so that it can be read by the NFC reader that you've configured. 

- Tag the album with the nfc tag (I like to place my tags about 1" inside the album cover, up 1" from the bottom of the album sleeve)
- Place the album on the "player" so the tag lines up with the reader
- You'll be prompted on the configured speaker to play the album on your configured speaker
- Open Sonos and play that album on the configured speaker
- The registration will poll several times ensuring that an album has been playing for over 10 seconds, if so it add this album to the database
- After registration the album begins playing
- You can remove the album at any time to stop playback

Once registered anytime you place that album back on the device it will begin to play.
