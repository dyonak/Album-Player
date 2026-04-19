#!/usr/bin/env python3
"""
WiFi Provisioning with Captive Portal for Album Player

Simple flow:
1. On boot, check if we have internet connectivity
2. If yes, exit (nothing to do)
3. If no, start AP mode with captive portal
4. While in AP mode, check every 5 minutes for known networks
5. When user configures WiFi via portal, connect and exit
6. Captive portal auto-opens on mobile devices (iOS/Android)
"""

import subprocess
import time
import threading
import os
import sys
import signal
from flask import Flask, request, render_template_string, redirect, make_response

# --- Configuration ---
AP_SSID = "AlbumPlayerWifiConfig"
AP_PASSWORD = "playjams"  # At least 8 characters
AP_IP = "192.168.42.1"
AP_SUBNET = "255.255.255.0"
AP_DHCP_RANGE_START = "192.168.42.10"
AP_DHCP_RANGE_END = "192.168.42.50"
FLASK_PORT = 80  # Port 80 required for captive portal detection
KNOWN_NETWORK_CHECK_INTERVAL = 300  # 5 minutes
INTERNET_CHECK_URL = "http://connectivitycheck.gstatic.com/generate_204"

# --- Global State ---
wifi_iface = None
ap_active = False
credentials_received = threading.Event()
received_ssid = None
received_password = None
shutdown_flag = threading.Event()

# --- Flask App ---
app = Flask(__name__)

# Clean, mobile-friendly HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Album Player WiFi Setup</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            padding: 32px;
            width: 100%;
            max-width: 380px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            font-size: 24px;
            color: #333;
            margin-bottom: 8px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            font-size: 14px;
            text-align: center;
            margin-bottom: 24px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }
        select, input[type="text"], input[type="password"] {
            width: 100%;
            padding: 14px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.2s;
        }
        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
        }
        .password-container {
            position: relative;
        }
        .toggle-password {
            position: absolute;
            right: 14px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #666;
            cursor: pointer;
            font-size: 14px;
        }
        button[type="submit"] {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button[type="submit"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        button[type="submit"]:active {
            transform: translateY(0);
        }
        .manual-entry {
            text-align: center;
            margin-top: 16px;
        }
        .manual-entry a {
            color: #667eea;
            font-size: 14px;
        }
        .error {
            background: #fee;
            color: #c00;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .success {
            background: #efe;
            color: #060;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            text-align: center;
        }
        .networks-list {
            max-height: 200px;
            overflow-y: auto;
        }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Album Player</h1>
        <p class="subtitle">Connect to your WiFi network</p>

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}

        {% if success %}
        <div class="success">{{ success }}</div>
        {% else %}
        <form method="POST" action="/connect">
            <div class="form-group">
                <label for="ssid">WiFi Network</label>
                <select name="ssid" id="ssid" required>
                    <option value="">Select a network...</option>
                    {% for network in networks %}
                    <option value="{{ network }}">{{ network }}</option>
                    {% endfor %}
                    <option value="__manual__">Enter manually...</option>
                </select>
            </div>

            <div class="form-group hidden" id="manual-ssid-group">
                <label for="manual_ssid">Network Name (SSID)</label>
                <input type="text" name="manual_ssid" id="manual_ssid" placeholder="Enter network name">
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <div class="password-container">
                    <input type="password" name="password" id="password" placeholder="Enter WiFi password">
                    <button type="button" class="toggle-password" onclick="togglePassword()">Show</button>
                </div>
            </div>

            <button type="submit">Connect</button>
        </form>
        {% endif %}
    </div>

    <script>
        document.getElementById('ssid').addEventListener('change', function() {
            var manualGroup = document.getElementById('manual-ssid-group');
            if (this.value === '__manual__') {
                manualGroup.classList.remove('hidden');
                document.getElementById('manual_ssid').required = true;
            } else {
                manualGroup.classList.add('hidden');
                document.getElementById('manual_ssid').required = false;
            }
        });

        function togglePassword() {
            var pwd = document.getElementById('password');
            var btn = document.querySelector('.toggle-password');
            if (pwd.type === 'password') {
                pwd.type = 'text';
                btn.textContent = 'Hide';
            } else {
                pwd.type = 'password';
                btn.textContent = 'Show';
            }
        }
    </script>
</body>
</html>
"""

CONNECTING_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connecting...</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            max-width: 380px;
        }
        h1 { color: #333; margin-bottom: 16px; }
        p { color: #666; }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #e0e0e0;
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Connecting...</h1>
        <div class="spinner"></div>
        <p>Connecting to <strong>{{ ssid }}</strong></p>
        <p style="margin-top: 16px; font-size: 14px;">
            This page will close automatically.<br>
            If it doesn't, you can close it manually.
        </p>
    </div>
</body>
</html>
"""


def run_cmd(cmd, check=True, timeout=30):
    """Run a shell command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"  stderr: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {' '.join(cmd)}")
        return None
    except Exception as e:
        print(f"Command error: {e}")
        return None


def get_wifi_interface():
    """Find the wireless interface name."""
    output = run_cmd(["iw", "dev"], check=False)
    if output:
        for line in output.split('\n'):
            if 'Interface' in line:
                return line.split()[-1]

    # Fallback: check common names
    for iface in ['wlan0', 'wlan1', 'wlp2s0', 'wlp3s0']:
        if os.path.exists(f"/sys/class/net/{iface}/wireless"):
            return iface

    return None


def check_internet():
    """Check if we have internet connectivity."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--connect-timeout", "5", INTERNET_CHECK_URL],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip() == "204"
    except:
        return False


def scan_networks():
    """Scan for available WiFi networks."""
    global wifi_iface

    # Trigger a fresh scan
    run_cmd(["nmcli", "device", "wifi", "rescan"], check=False, timeout=10)
    time.sleep(2)

    # Get list of networks
    output = run_cmd(
        ["nmcli", "-t", "-f", "SSID,SIGNAL", "device", "wifi", "list"],
        check=False,
        timeout=10
    )

    networks = []
    seen = set()

    if output:
        for line in output.split('\n'):
            if ':' in line:
                parts = line.split(':')
                ssid = parts[0].strip()
                if ssid and ssid not in seen and ssid != AP_SSID:
                    seen.add(ssid)
                    networks.append(ssid)

    return networks


def connect_to_wifi(ssid, password):
    """Connect to a WiFi network using NetworkManager."""
    global wifi_iface

    print(f"Attempting to connect to '{ssid}'...")

    # Delete any existing connection with this name
    run_cmd(["nmcli", "connection", "delete", ssid], check=False)

    # Create and activate new connection
    if password:
        result = run_cmd([
            "nmcli", "device", "wifi", "connect", ssid,
            "password", password,
            "ifname", wifi_iface
        ], check=False, timeout=30)
    else:
        result = run_cmd([
            "nmcli", "device", "wifi", "connect", ssid,
            "ifname", wifi_iface
        ], check=False, timeout=30)

    if result is None:
        print(f"Failed to connect to '{ssid}'")
        return False

    # Wait for connection to establish and verify internet
    time.sleep(5)

    for i in range(3):
        if check_internet():
            print(f"Successfully connected to '{ssid}' with internet!")
            return True
        time.sleep(2)

    print(f"Connected to '{ssid}' but no internet detected")
    return False


def check_known_networks():
    """Check if any known/saved networks are available and connect."""
    global wifi_iface

    print("Checking for known networks...")

    # Get list of saved connections
    saved = run_cmd(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"], check=False)
    saved_wifi = []

    if saved:
        for line in saved.split('\n'):
            if ':802-11-wireless' in line:
                name = line.split(':')[0]
                if name != "captive-portal-ap":
                    saved_wifi.append(name)

    if not saved_wifi:
        print("No saved WiFi connections found")
        return False

    print(f"Saved WiFi connections: {saved_wifi}")

    # Scan for available networks
    available = scan_networks()
    print(f"Available networks: {available}")

    # Try to connect to any saved network that's available
    for saved_name in saved_wifi:
        if saved_name in available:
            print(f"Found saved network '{saved_name}', attempting connection...")
            result = run_cmd([
                "nmcli", "connection", "up", saved_name
            ], check=False, timeout=30)

            if result is not None:
                time.sleep(5)
                if check_internet():
                    print(f"Connected to known network '{saved_name}'!")
                    return True

    print("Could not connect to any known network")
    return False


def start_access_point():
    """Start the WiFi access point for captive portal."""
    global wifi_iface, ap_active

    print(f"Starting access point '{AP_SSID}' on {wifi_iface}...")

    # Stop any existing AP connection
    run_cmd(["nmcli", "connection", "delete", "captive-portal-ap"], check=False)

    # Bring down the interface first
    run_cmd(["nmcli", "device", "disconnect", wifi_iface], check=False)
    time.sleep(1)

    # Create hotspot
    result = run_cmd([
        "nmcli", "connection", "add",
        "type", "wifi",
        "con-name", "captive-portal-ap",
        "ifname", wifi_iface,
        "ssid", AP_SSID,
        "mode", "ap",
        "ipv4.method", "shared",
        "ipv4.addresses", f"{AP_IP}/24",
        "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.psk", AP_PASSWORD
    ], check=False)

    if result is None:
        print("Failed to create AP connection")
        return False

    # Activate the connection
    result = run_cmd(["nmcli", "connection", "up", "captive-portal-ap"], check=False)

    if result is None:
        print("Failed to activate AP")
        return False

    time.sleep(2)

    # Start dnsmasq for better DHCP/DNS control
    start_dnsmasq()

    ap_active = True
    print(f"Access point '{AP_SSID}' started on {AP_IP}")
    return True


def stop_access_point():
    """Stop the access point."""
    global ap_active

    print("Stopping access point...")

    stop_dnsmasq()
    run_cmd(["nmcli", "connection", "down", "captive-portal-ap"], check=False)
    run_cmd(["nmcli", "connection", "delete", "captive-portal-ap"], check=False)

    ap_active = False
    print("Access point stopped")


def start_dnsmasq():
    """Start dnsmasq for DHCP and DNS hijacking (captive portal detection)."""
    # Kill any existing dnsmasq
    run_cmd(["pkill", "-9", "dnsmasq"], check=False)
    time.sleep(1)

    # Write dnsmasq config
    config = f"""
interface={wifi_iface}
bind-interfaces
dhcp-range={AP_DHCP_RANGE_START},{AP_DHCP_RANGE_END},{AP_SUBNET},24h
dhcp-option=option:router,{AP_IP}
dhcp-option=option:dns-server,{AP_IP}

# Captive portal detection - redirect all DNS to us
address=/#/{AP_IP}
"""

    config_path = "/tmp/dnsmasq-captive.conf"
    with open(config_path, 'w') as f:
        f.write(config)

    # Start dnsmasq
    result = run_cmd([
        "dnsmasq", "-C", config_path, "--log-queries", "--log-facility=/tmp/dnsmasq.log"
    ], check=False)

    print("dnsmasq started for captive portal")


def stop_dnsmasq():
    """Stop dnsmasq."""
    run_cmd(["pkill", "-9", "dnsmasq"], check=False)


# --- Flask Routes ---

@app.route('/')
def index():
    """Main captive portal page."""
    networks = scan_networks()
    return render_template_string(HTML_TEMPLATE, networks=networks, error=None, success=None)


@app.route('/connect', methods=['POST'])
def connect():
    """Handle WiFi connection form submission."""
    global received_ssid, received_password

    ssid = request.form.get('ssid', '')
    password = request.form.get('password', '')

    # Handle manual SSID entry
    if ssid == '__manual__':
        ssid = request.form.get('manual_ssid', '').strip()

    if not ssid:
        networks = scan_networks()
        return render_template_string(HTML_TEMPLATE, networks=networks,
                                      error="Please select or enter a network name")

    # Store credentials and signal main thread
    received_ssid = ssid
    received_password = password
    credentials_received.set()

    return render_template_string(CONNECTING_TEMPLATE, ssid=ssid)


# Captive portal detection endpoints
# These are checked by devices to detect captive portals

@app.route('/generate_204')
@app.route('/gen_204')
def android_check():
    """Android captive portal check - return redirect to trigger portal."""
    return redirect('http://' + AP_IP + '/', code=302)


@app.route('/hotspot-detect.html')
@app.route('/library/test/success.html')
def apple_check():
    """Apple captive portal check."""
    return redirect('http://' + AP_IP + '/', code=302)


@app.route('/ncsi.txt')
@app.route('/connecttest.txt')
def windows_check():
    """Windows captive portal check."""
    return redirect('http://' + AP_IP + '/', code=302)


@app.route('/canonical.html')
@app.route('/success.txt')
def firefox_check():
    """Firefox captive portal check."""
    return redirect('http://' + AP_IP + '/', code=302)


# Catch-all route for any other requests
@app.route('/<path:path>')
def catch_all(path):
    """Redirect all other requests to main page."""
    return redirect('http://' + AP_IP + '/', code=302)


def run_flask():
    """Run Flask server in a thread."""
    # Suppress Flask startup messages
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app.run(host='0.0.0.0', port=FLASK_PORT, threaded=True)


def known_network_checker():
    """Background thread to periodically check for known networks."""
    global wifi_iface

    while not shutdown_flag.is_set():
        # Wait for interval, but check shutdown flag periodically
        for _ in range(KNOWN_NETWORK_CHECK_INTERVAL):
            if shutdown_flag.is_set() or credentials_received.is_set():
                return
            time.sleep(1)

        if shutdown_flag.is_set() or credentials_received.is_set():
            return

        print("\n--- Periodic check for known networks ---")

        # Temporarily stop AP to scan
        stop_access_point()
        time.sleep(2)

        if check_known_networks():
            print("Connected to known network during periodic check!")
            credentials_received.set()  # Signal main loop to exit
            return

        # No known network found, restart AP
        print("No known network available, restarting AP...")
        start_access_point()


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    print("\nShutdown signal received...")
    shutdown_flag.set()
    credentials_received.set()  # Unblock any waits


def main():
    global wifi_iface, received_ssid, received_password

    # Check root
    if os.geteuid() != 0:
        print("This script must be run as root (sudo)")
        sys.exit(1)

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 50)
    print("Album Player WiFi Provisioning")
    print("=" * 50)

    # Find WiFi interface
    wifi_iface = get_wifi_interface()
    if not wifi_iface:
        print("ERROR: No WiFi interface found!")
        sys.exit(1)
    print(f"Using WiFi interface: {wifi_iface}")

    # Initial connectivity check
    print("\nChecking for existing internet connection...")

    # Give NetworkManager a chance to auto-connect
    for i in range(6):  # 30 seconds total
        if check_internet():
            print("Internet connection available. WiFi provisioning not needed.")
            sys.exit(0)
        print(f"  Waiting for connection... ({(i+1)*5}s)")
        time.sleep(5)

    # No internet, check for known networks
    print("\nNo internet. Checking for known networks...")
    if check_known_networks():
        print("Connected to known network!")
        sys.exit(0)

    # No connection possible, start captive portal
    print("\n" + "=" * 50)
    print("Starting Captive Portal Mode")
    print("=" * 50)

    if not start_access_point():
        print("ERROR: Failed to start access point!")
        sys.exit(1)

    # Start Flask server in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"Captive portal running at http://{AP_IP}/")
    print(f"Connect to WiFi network '{AP_SSID}' (password: {AP_PASSWORD})")

    # Start background thread to check for known networks
    checker_thread = threading.Thread(target=known_network_checker, daemon=True)
    checker_thread.start()

    # Main loop - wait for credentials
    try:
        while not shutdown_flag.is_set():
            # Wait for credentials (with timeout to allow periodic checks)
            if credentials_received.wait(timeout=10):
                if shutdown_flag.is_set():
                    break

                if received_ssid:
                    print(f"\nCredentials received for '{received_ssid}'")

                    # Stop AP and connect to the new network
                    stop_access_point()
                    time.sleep(2)

                    if connect_to_wifi(received_ssid, received_password):
                        print("Successfully connected!")
                        print("WiFi provisioning complete.")
                        sys.exit(0)
                    else:
                        print("Failed to connect. Restarting captive portal...")
                        received_ssid = None
                        received_password = None
                        credentials_received.clear()
                        start_access_point()
                else:
                    # Credentials event set but no SSID - likely from checker thread
                    if check_internet():
                        print("Connected to network!")
                        sys.exit(0)
                    credentials_received.clear()

    except KeyboardInterrupt:
        pass
    finally:
        print("\nCleaning up...")
        shutdown_flag.set()
        stop_access_point()
        print("Done.")


if __name__ == "__main__":
    main()
