from flask import Flask, render_template, request, jsonify, g, send_file
from Registrar import Registrar
import json
import random
import logging  # Import the logging module
import DBConnector
from SonosController import SonosController
from gevent.pywsgi import WSGIServer
import os
from config import Config


app = Flask(__name__)
registrar = Registrar()
sc = SonosController()

# Configure logging
logging.basicConfig(level=logging.ERROR)  # Set the logging level to ERROR or DEBUG if needed

def run_app():
    config = Config()
    #dev testing only, use WSGI server below
    app.run(host="0.0.0.0", port=config.port, debug=True)

    #prod server
    #http_server = WSGIServer(('0.0.0.0', int(config.port)), app)
    #http_server.serve_forever()

@app.route('/')
def index():
    albums = DBConnector.get_all_albums()
    return render_template('index.html', albums=albums)

@app.route('/audio/<filename>')
def serve_music(filename):
    file_path = os.path.join("./audio", filename)
    if os.path.exists(file_path) and filename.endswith('.mp3'):
        return send_file(file_path, mimetype='audio/mpeg')
    else:
        return "File not found or invalid format", 404

@app.route('/delete_album/<path:album_uri>', methods=['DELETE'])
def delete_album(album_uri):
    try:
        DBConnector.delete_album(album_uri)
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error deleting album: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/config')
def config():
    config = Config()
    config.reload()
    #Turn the config attributes into a list for passing to the jinja template
    configdict = vars(config)
    return render_template('config.html', config=configdict)

@app.route('/save', methods=['POST'])
def save_config():
    data = request.get_json()
    with open('config.json', 'w') as f:
        json.dump(data, f, indent=4)
    return jsonify({'status': 'success'})

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/search', methods=['POST'])
def search():
    search_term = request.form['search_term']
    albums = registrar.lookup_albums(search_term)
    existing_albums = DBConnector.get_all_albums()
    
    # Convert existing_albums to a list of dictionaries with artist and album_name
    existing_albums_list = [{'artist': album.get('artist', ''), 'album_name': album.get('album', ''), 'spotify_uri': album.get('spotify_uri', '')} for album in existing_albums]
    return jsonify({'albums': albums, 'existing_albums': existing_albums_list})

@app.route('/add_album', methods=['POST'])
def add_album():
    album_data = request.get_json()
    nfc_id = random.randrange(99999999)
    try:
        # Extract data from album_data
        artist = album_data['artist']
        album_name = album_data['album_name']
        release_date = album_data['release_date']
        spotify_uri = album_data['spotify_uri']
        album_length = album_data['total_duration_seconds']
        album_art = album_data['album_art']

        # Call db.add_album with all required arguments
        DBConnector.add_album(artist, album_name, release_date, spotify_uri, nfc_id, album_length, album_art)
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error adding album: {e}")
        return jsonify({'status': 'error'})

@app.route('/play_album/<path:album_uri>', methods=['GET'])
def play_album(album_uri):
    sc.get_state()
    if sc.state == "PLAYING":
        sc.pause()
        return jsonify({'status':'success'})
    try:
        sc.play_album(album_uri)
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error playing album: {e}")
        return jsonify({'status': 'error'})

if __name__ == '__main__':
    run_app()
