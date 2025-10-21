# Registrar.py
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import logging
import os
import DBConnector

logging.basicConfig(level=logging.INFO)

class Registrar:
    def __init__(self, config_file="./config.json"):
        # Try to get credentials from encrypted environment variables first
        client_id, client_secret = self._get_credentials_from_env()

        # Fall back to config.json if env vars not present
        if not client_id or not client_secret:
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                client_id = data.get("service_api_id")
                client_secret = data.get("service_api_secret")
            except FileNotFoundError:
                logging.error(f"Config file not found: {config_file}")
                data = {}
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON in config file: {config_file}")
                data = {}

        if not client_id or not client_secret:
            raise ValueError("Spotify credentials not found in environment variables or config.json")

        self.spotify_auth = SpotifyClientCredentials(client_id, client_secret)
        self.spotify = spotipy.Spotify(client_credentials_manager=self.spotify_auth)

    def _get_credentials_from_env(self):
        """
        Decrypt Spotify credentials from environment variables.
        Returns (client_id, client_secret) or (None, None) if not present.
        """
        encrypted_id = os.getenv("ENCRYPTED_SPOTIFY_ID")
        encrypted_secret = os.getenv("ENCRYPTED_SPOTIFY_SECRET")
        encryption_key = os.getenv("ENCRYPTION_KEY")

        # If any are missing, return None (will fall back to config.json)
        if not all([encrypted_id, encrypted_secret, encryption_key]):
            return None, None

        try:
            from cryptography.fernet import Fernet
            cipher = Fernet(encryption_key.encode())
            client_id = cipher.decrypt(encrypted_id.encode()).decode()
            client_secret = cipher.decrypt(encrypted_secret.encode()).decode()
            logging.info("✓ Successfully loaded credentials from encrypted environment variables")
            return client_id, client_secret
        except Exception as e:
            logging.error(f"Failed to decrypt credentials: {e}")
            return None, None


    def lookup_album(self, album_title):
        """
        Looks up an album on Spotify, retrieves its details, and calculates the total play time.

        Args:
            album_title (str): The title of the album to search for.

        Returns:
            dict: A dictionary containing album details, including total play time, or None if an error occurs.
        """
        try:
            results = self.spotify.search(q=album_title, limit=1, type='album')
            if not results['albums']['items']:
                logging.warning(f"No results found for album: {album_title}")
                return None

            album = results['albums']['items'][0]
            album_id = album['id']
            album_name = album['name']
            artist_name = album['artists'][0]['name']
            release_date = album['release_date']
            spotify_uri = album['uri']
            album_art = album['images'][0]['url']
            print(album_art)

            # Get album tracks
            tracks_results = self.spotify.album_tracks(album_id)
            tracks = tracks_results['items']

            # Calculate total duration
            total_duration_ms = sum(track['duration_ms'] for track in tracks)
            total_duration_seconds = total_duration_ms / 1000
            total_minutes = int(total_duration_seconds // 60)
            total_seconds = int(total_duration_seconds % 60)

            logging.info(f"Album found: {album_name} by {artist_name}")
            logging.info(f"Total duration: {total_minutes} minutes, {total_seconds} seconds")

            return {
                'artist': artist_name,
                'album_name': album_name,
                'release_date': release_date,
                'spotify_uri': spotify_uri,
                'total_duration_seconds': total_duration_seconds,
                'album_art': album_art
            }

        except Exception as e:
            logging.error(f"Error looking up album: {e}")
            return None

    def lookup_albums(self, album_title):
        """
        Looks up an albums given a search term. Wrangle the metadata and return a list of dicts.

        Args:
            album_title (str): The title of the album to search for.

        Returns:
            dict: A dictionary containing album details, including total play time, or None if an error occurs.
        """
        try:
            results = self.spotify.search(q=album_title, limit=5, type='album')
            if not results['albums']['items']:
                logging.warning(f"No results found for album: {album_title}")
                return None

            albums = []

            for result in results['albums']['items']:
                print(result)
                album_id = result['id']
                album_name = result['name']
                artist_name = result['artists'][0]['name']
                release_date = result['release_date']
                spotify_uri = result['uri']
                album_art = result['images'][0]['url']

                # Get album tracks
                tracks_results = self.spotify.album_tracks(album_id)
                tracks = tracks_results['items']

                # Calculate total duration
                total_duration_ms = sum(track['duration_ms'] for track in tracks)
                total_duration_seconds = total_duration_ms / 1000

                logging.info(f"Album found: {album_name} by {artist_name}")
                logging.info(f"Total duration: {total_duration_seconds} seconds")

                albums.append(
                    {
                    'artist': artist_name,
                    'album_name': album_name,
                    'release_date': release_date,
                    'spotify_uri': spotify_uri,
                    'total_duration_seconds': total_duration_seconds,
                    'album_art': album_art
                    }
                )

            return albums

        except Exception as e:
            logging.error(f"Error looking up album: {e}")
            return None

    def lookup_tag(self, tag):
        """
        Lookup an nfc tag to see if it's currently in the db.

        If it is, return the spotify uri. If not return None.
        """
        if tag is None:
            logging.error("Cannot lookup tag: tag is None")
            return

        result = DBConnector.get_album(tag)

        if result:
            return result

        return None

    def add_album_to_db(self, album_data, nfc_id):
        """
        Adds an album to the database.

        Args:
            album_data (dict): A dictionary containing album details (as returned by lookup_album).
            nfc_id (str): The NFC ID associated with the album.
        """
        if album_data is None:
            logging.error("Cannot add album to database: album_data is None")
            return
        
        try:
            DBConnector.add_album(
                album_data['artist'],
                album_data['album_name'],
                album_data['release_date'],
                album_data['spotify_uri'],
                nfc_id,
                album_data['total_duration_seconds'],
                album_data['album_art']
            )
            logging.info(f"Album '{album_data['album_name']}' added to database with NFC ID: {nfc_id}")
        except Exception as e:
            logging.error(f"Error adding album to database: {e}")

    def register_album(self, album):
        # Register the album with the system
        self.album = album
        print(f"Album registered: {self.album}")

if __name__ == "__main__":
    r = Registrar()
    albums = r.lookup_albums("Nirvana")
    print(albums)
    for album in albums:
        print(album)
