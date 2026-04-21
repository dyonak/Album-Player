# Spotify Credentials Setup

This guide explains how to configure your Spotify API credentials for Album Player.

## Overview

Album Player needs Spotify API credentials for:
- Playing albums via the Spotify Web API
- spotifyd (Spotify Connect receiver)

## Step 1: Create Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create App"
4. Fill in:
   - App name: `Album Player`
   - App description: `NFC Album Player`
   - Redirect URI: `http://127.0.0.1:8888/callback`
5. Check the agreement box and click "Save"
6. Note your **Client ID** and **Client Secret**

## Step 2: Configure Album Player

### Option A: Using the Web UI (Recommended)

1. Access the web interface at `http://your-pi.local:3029`
2. Go to the **Spotify** tab
3. Click "Connect Spotify"
4. Authorize with your Spotify account
5. Copy the code from the redirect URL and paste it in the web UI

### Option B: Using config.json

Create or edit `~/.album-player/config.json` on your Pi:

```json
{
    "spotify_client_id": "your_client_id_here",
    "spotify_client_secret": "your_client_secret_here"
}
```

### Option C: Using Environment Variables

Set these in your shell or add to the service file:

```bash
export SPOTIFY_CLIENT_ID="your_client_id_here"
export SPOTIFY_CLIENT_SECRET="your_client_secret_here"
```

To add to the albumplayer service:
```bash
sudo systemctl edit albumplayer
```

Add:
```ini
[Service]
Environment=SPOTIFY_CLIENT_ID=your_client_id_here
Environment=SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

## Step 3: Configure spotifyd

spotifyd needs Spotify credentials to appear as a Spotify Connect device.

Edit `~/.config/spotifyd/spotifyd.conf`:

```toml
[global]
device_name = "Album Player"
backend = "alsa"
device = "default"

# Add your Spotify credentials
username = "your_spotify_email"
password = "your_spotify_password"
```

Or use a password command for better security:

```bash
# Create password file
echo "your_spotify_password" > ~/.spotify_password
chmod 600 ~/.spotify_password
```

Then in spotifyd.conf:
```toml
username = "your_spotify_email"
password_cmd = "cat /home/your_user/.spotify_password"
```

Restart spotifyd:
```bash
sudo systemctl restart spotifyd
```

## Step 4: Verify Setup

1. Check spotifyd is running:
   ```bash
   sudo systemctl status spotifyd
   journalctl -u spotifyd -f
   ```

2. Open Spotify on your phone/computer
3. Look for "Album Player" in the devices list
4. Select it to verify connection

## Encrypted Credentials (Advanced)

For additional security, you can encrypt your Spotify API credentials.

Run the encryption tool:
```bash
cd Album-Player/dev_tools
python3 encrypt_credentials.py
```

This will:
1. Prompt for your Client ID and Client Secret
2. Generate an encryption key
3. Output encrypted values

Store the encryption key securely and set as environment variable:
```bash
export ENCRYPTION_KEY="your_generated_key"
export ENCRYPTED_SPOTIFY_ID="encrypted_value"
export ENCRYPTED_SPOTIFY_SECRET="encrypted_value"
```

**Security Note**: This is obfuscation, not true security. Anyone with root access to the Pi can extract these credentials.

## Credential Priority

The code checks for credentials in this order:
1. Encrypted environment variables (if `ENCRYPTION_KEY` is set)
2. Plain environment variables (`SPOTIFY_CLIENT_ID`, etc.)
3. `config.json` file

## Troubleshooting

### "Album Player" not showing in Spotify devices

1. Check spotifyd is running: `sudo systemctl status spotifyd`
2. Check spotifyd logs: `journalctl -u spotifyd -f`
3. Verify credentials in spotifyd.conf
4. Ensure Pi is on the same network as your Spotify app

### "Premium required" error

Spotify Web API playback control requires a Spotify Premium account.

### OAuth redirect errors

Ensure your redirect URI exactly matches what's configured in the Spotify Developer Dashboard:
`http://127.0.0.1:8888/callback`

### Credentials not loading

Check file permissions:
```bash
ls -la ~/.album-player/config.json
# Should be readable by your user
```

## Questions?

- Need to rotate credentials? Update `config.json` or environment variables and restart services
- Need to revoke access? Change your Spotify API credentials in the developer dashboard
