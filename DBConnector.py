import sqlite3
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

db_name = "./db/albums.db"

def connect():
    """Establish a connection to the database."""
    try:
        connection = sqlite3.connect(db_name)
        create_table(connection)
        return connection
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database: {e}")
        raise

def close():
    """Close the database connection."""
    if connection:
        try:
            connection.close()
            connection = None
        except sqlite3.Error as e:
            logging.error(f"Error closing database connection: {e}")

def execute_query(query, params=()):
    with sqlite3.connect('./db/albums.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

def create_table(connection):
    """Create the albums table if it doesn't exist."""
    cursor = connection.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist TEXT NOT NULL,
                album TEXT NOT NULL,
                release_date TEXT,
                spotify_uri TEXT UNIQUE,
                nfc_id TEXT UNIQUE,
                play_count INTEGER DEFAULT 0,
                last_played_date TEXT,
                album_length INTEGER,
                date_added TEXT DEFAULT CURRENT_TIMESTAMP,
                album_art TEXT
            )
        ''')
        connection.commit()
    except sqlite3.Error as e:
        logging.error(f"Error creating table: {e}")
        connection.rollback()
        raise

def add_album(artist, album, release_date, spotify_uri, nfc_id, album_length, album_art):
    """Add a new album to the database."""
    connection = connect()
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO albums (artist, album, release_date, spotify_uri, nfc_id, album_length, album_art)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (artist, album, release_date, spotify_uri, nfc_id, album_length, album_art))
        connection.commit()
    except sqlite3.Error as e:
        logging.error(f"Error adding album: {e}")
        connection.rollback()
        raise

def update_play_count(spotify_uri):
    """Update the play count and last played date for an album."""
    connection = connect()
    cursor = connection.cursor()
    try:
        cursor.execute('''
            UPDATE albums
            SET play_count = play_count + 1,
                last_played_date = ?
            WHERE spotify_uri = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), spotify_uri))
        connection.commit()
    except sqlite3.Error as e:
        logging.error(f"Error updating play count: {e}")
        connection.rollback()
        raise

def get_album(nfc_id):
    """Retrieve an album by its NFC ID."""
    connection = connect()
    cursor = connection.cursor()
    try:
        cursor.execute('''
            SELECT * FROM albums WHERE nfc_id = ?
        ''', (nfc_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        logging.error(f"Error getting album: {e}")
        raise

def delete_album(spotify_uri):
    """Delete an album from the database."""
    connection = connect()
    cursor = connection.cursor()
    try:
        cursor.execute('''
            DELETE FROM albums WHERE spotify_uri = ?
        ''', (spotify_uri,))
        connection.commit()
    except sqlite3.Error as e:
        logging.error(f"Error deleting album: {e}")
        connection.rollback()
        raise

def get_all_albums():
    """Retrieve all albums from the database."""
    connection = connect()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM albums ORDER BY artist, album")
        albums = cursor.fetchall()
        album_list = []
        for album in albums:
            album_dict = {
                'id': album[0],
                'artist': album[1],
                'album': album[2],
                'release_date': album[3],
                'spotify_uri': album[4],
                'nfc_id': album[5],
                'play_count': album[6],
                'last_played_date': album[7],
                'album_length': album[8],
                'date_added': album[9],
                'album_art': album[10]
            }
            album_list.append(album_dict)
        return album_list
    except sqlite3.Error as e:
        logging.error(f"Error getting all albums: {e}")
        raise

if __name__=="__main__":
    albums = get_all_albums()
    print(albums)
    #db.add_album("test", "test", "2021", "spotify:playlist:37i9dQZF1E8GTM5dxZeoc2", bytearray(b'7\x8fM\x05'), 50, "https://wiki.project1999.com/images/C_druid.gif")