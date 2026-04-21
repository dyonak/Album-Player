from flask import Flask, render_template, request, jsonify, g, send_file
from Registrar import Registrar
import json
import random
import logging
import DBConnector
from SonosController import SonosController
from gevent.pywsgi import WSGIServer
import os
from config import Config

# Bluetooth is optional - may not be available on all systems
try:
    from BluetoothManager import BluetoothManager
    bt = BluetoothManager()
    BLUETOOTH_AVAILABLE = True
except Exception as e:
    print(f"Bluetooth not available: {e}")
    bt = None
    BLUETOOTH_AVAILABLE = False

# SpotifyClient for OAuth setup
try:
    from SpotifyClient import SpotifyClient
    spotify_client = SpotifyClient()
    SPOTIFY_CLIENT_AVAILABLE = True
except Exception as e:
    print(f"SpotifyClient not available: {e}")
    spotify_client = None
    SPOTIFY_CLIENT_AVAILABLE = False


app = Flask(__name__)
registrar = Registrar()
sc = SonosController()

# Configure logging
logging.basicConfig(level=logging.ERROR)

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


# --- Bluetooth Routes ---

@app.route('/bluetooth')
def bluetooth():
    """Bluetooth management page."""
    if not BLUETOOTH_AVAILABLE:
        return render_template('bluetooth.html',
                               powered=False,
                               devices=[],
                               paired_devices=[],
                               connected_device=None,
                               bluetooth_unavailable=True)

    powered = bt.is_powered()
    devices = bt.get_devices() if powered else []
    paired_devices = [d for d in devices if d.paired]
    connected_device = bt.get_connected_device() if powered else None

    return render_template('bluetooth.html',
                           powered=powered,
                           devices=devices,
                           paired_devices=paired_devices,
                           connected_device=connected_device,
                           bluetooth_unavailable=False)


@app.route('/bluetooth/power', methods=['POST'])
def bluetooth_power():
    """Toggle Bluetooth power."""
    if not BLUETOOTH_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Bluetooth not available'}), 503
    try:
        if bt.is_powered():
            bt.power_off()
        else:
            bt.power_on()
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Bluetooth power error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/bluetooth/scan', methods=['POST'])
def bluetooth_scan():
    """Scan for Bluetooth devices."""
    if not BLUETOOTH_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Bluetooth not available'}), 503
    try:
        devices = bt.scan(duration=10)
        return jsonify({
            'status': 'success',
            'devices': [{'address': d.address, 'name': d.name, 'paired': d.paired} for d in devices]
        })
    except Exception as e:
        logging.error(f"Bluetooth scan error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/bluetooth/pair', methods=['POST'])
def bluetooth_pair():
    """Pair with a Bluetooth device."""
    if not BLUETOOTH_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Bluetooth not available'}), 503
    try:
        data = request.get_json()
        address = data.get('address')
        if not address:
            return jsonify({'status': 'error', 'error': 'No address provided'}), 400

        if bt.pair(address):
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'error': 'Pairing failed'}), 500
    except Exception as e:
        logging.error(f"Bluetooth pair error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/bluetooth/connect', methods=['POST'])
def bluetooth_connect():
    """Connect to a paired Bluetooth device."""
    if not BLUETOOTH_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Bluetooth not available'}), 503
    try:
        data = request.get_json()
        address = data.get('address')
        if not address:
            return jsonify({'status': 'error', 'error': 'No address provided'}), 400

        if bt.connect(address):
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'error': 'Connection failed'}), 500
    except Exception as e:
        logging.error(f"Bluetooth connect error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/bluetooth/disconnect', methods=['POST'])
def bluetooth_disconnect():
    """Disconnect from a Bluetooth device."""
    if not BLUETOOTH_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Bluetooth not available'}), 503
    try:
        data = request.get_json()
        address = data.get('address')
        if not address:
            return jsonify({'status': 'error', 'error': 'No address provided'}), 400

        if bt.disconnect(address):
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'error': 'Disconnect failed'}), 500
    except Exception as e:
        logging.error(f"Bluetooth disconnect error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/bluetooth/remove', methods=['POST'])
def bluetooth_remove():
    """Remove/unpair a Bluetooth device."""
    if not BLUETOOTH_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'Bluetooth not available'}), 503
    try:
        data = request.get_json()
        address = data.get('address')
        if not address:
            return jsonify({'status': 'error', 'error': 'No address provided'}), 400

        if bt.remove(address):
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'error': 'Remove failed'}), 500
    except Exception as e:
        logging.error(f"Bluetooth remove error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# --- Spotify OAuth Routes ---

@app.route('/spotify/setup')
def spotify_setup():
    """Spotify OAuth setup page."""
    if not SPOTIFY_CLIENT_AVAILABLE:
        return render_template('spotify_setup.html',
                               available=False,
                               authenticated=False,
                               auth_url=None,
                               devices=[])

    authenticated = spotify_client.is_authenticated()
    auth_url = spotify_client.get_auth_url() if not authenticated else None
    devices = spotify_client.get_devices() if authenticated else []

    return render_template('spotify_setup.html',
                           available=True,
                           authenticated=authenticated,
                           auth_url=auth_url,
                           devices=devices)


@app.route('/spotify/callback')
def spotify_callback():
    """Handle Spotify OAuth callback."""
    if not SPOTIFY_CLIENT_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'SpotifyClient not available'}), 503

    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return render_template('spotify_setup.html',
                               available=True,
                               authenticated=False,
                               auth_url=spotify_client.get_auth_url(),
                               devices=[],
                               error=f"Authorization error: {error}")

    if code:
        if spotify_client.complete_auth(code):
            return render_template('spotify_setup.html',
                                   available=True,
                                   authenticated=True,
                                   auth_url=None,
                                   devices=spotify_client.get_devices(),
                                   success="Spotify connected successfully!")
        else:
            return render_template('spotify_setup.html',
                                   available=True,
                                   authenticated=False,
                                   auth_url=spotify_client.get_auth_url(),
                                   devices=[],
                                   error="Failed to complete authorization")

    return render_template('spotify_setup.html',
                           available=True,
                           authenticated=spotify_client.is_authenticated(),
                           auth_url=spotify_client.get_auth_url(),
                           devices=[])


@app.route('/spotify/auth', methods=['POST'])
def spotify_auth():
    """Submit OAuth code manually (for headless setup)."""
    if not SPOTIFY_CLIENT_AVAILABLE:
        return jsonify({'status': 'error', 'error': 'SpotifyClient not available'}), 503

    data = request.get_json()
    code = data.get('code', '').strip()

    if not code:
        return jsonify({'status': 'error', 'error': 'No code provided'}), 400

    if spotify_client.complete_auth(code):
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'error': 'Authorization failed'}), 500


@app.route('/spotify/status')
def spotify_status():
    """Get Spotify API status."""
    if not SPOTIFY_CLIENT_AVAILABLE:
        return jsonify({
            'available': False,
            'authenticated': False,
            'devices': []
        })

    return jsonify({
        'available': True,
        'authenticated': spotify_client.is_authenticated(),
        'devices': spotify_client.get_devices() if spotify_client.is_authenticated() else []
    })


if __name__ == '__main__':
    run_app()
