import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.spi import PN532_SPI
import time

# # Create SPI connection
# spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
# cs_pin = DigitalInOut(board.D8)

# # Create an instance of the PN532 class
# pn532 = PN532_SPI(spi, cs_pin, debug=False)
# ic, ver, rev, support = pn532.firmware_version

# #print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
# # Configure PN532 to communicate with MiFare cards
# pn532.SAM_configuration()

class NFCPoller:
    def __init__(self):
        self.spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        self.cs_pin = DigitalInOut(board.D8)
        self.nfc_adapter = PN532_SPI(self.spi, self.cs_pin, debug=False)
        self.ic, self.ver, self.rev, self.support = self.nfc_adapter.firmware_version
        self.tag = None
        self.last_tag = None
        self.nfc_adapter.SAM_configuration()

    def poll(self):
        # Start polling for NFC tags
        #print("Checking for tag...")
        self.last_tag = self.tag
        self.tag = self.nfc_adapter.read_passive_target(timeout=0.5)
        print(f'From Poller\nCurrent:{self.tag}\nPrevious:{self.last_tag}')

if __name__ == "__main__":
    nfc = NFCPoller()
    while True:
        time.sleep(1.0)
        nfc.poll()


# print("Waiting for RFID/NFC card...")
# while True:
#     # Check if a card is available to read
#     uid = pn532.read_passive_target(timeout=0.5)
#     print(".", end="")
#     # Try again if no card is available.
#     if uid is None:
#         continue
#     print(uid)
#     print("Found card with UID:", [hex(i) for i in uid])