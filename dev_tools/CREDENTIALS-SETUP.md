# Spotify API Credentials Setup Guide

This guide explains how to securely embed your Spotify API credentials into the Docker image using encryption.

## Overview

The Album Player now supports encrypted Spotify credentials baked into the Docker image. This allows you to:
- Distribute Docker images to friends without exposing credentials in plaintext
- Avoid requiring users to create their own Spotify developer accounts
- No need for config.json on the Pi (credentials are in the image)

**Security Note**: This is obfuscation, not true security. Anyone with root access to the Pi can extract these credentials. Only use this approach with trusted friends.

---

## Setup Steps

### 1. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create an App"
4. Fill in the app name (e.g., "Album Player") and description
5. Click "Create"
6. Copy your **Client ID** and **Client Secret**

### 2. Encrypt Your Credentials

Run the encryption utility script:

```bash
python3 dev_tools/encrypt_credentials.py
```

This will:
- Generate an encryption key (saved to `.encryption_key` - keep this secret!)
- Prompt you to enter your Spotify Client ID and Secret
- Output encrypted values to paste into the Dockerfile

Example output:
```
Add these to your Dockerfile as ENV variables:

ENV ENCRYPTION_KEY=k8s9d...
ENV ENCRYPTED_SPOTIFY_ID="gAAAAABh..."
ENV ENCRYPTED_SPOTIFY_SECRET="gAAAAABh..."
```

### 3. Update the Dockerfile

Open `Dockerfile` and replace the placeholder values (lines 32-34):

**Before:**
```dockerfile
ENV ENCRYPTION_KEY="REPLACE_WITH_YOUR_ENCRYPTION_KEY"
ENV ENCRYPTED_SPOTIFY_ID="REPLACE_WITH_ENCRYPTED_ID"
ENV ENCRYPTED_SPOTIFY_SECRET="REPLACE_WITH_ENCRYPTED_SECRET"
```

**After (using your generated values):**
```dockerfile
ENV ENCRYPTION_KEY="k8s9d..."
ENV ENCRYPTED_SPOTIFY_ID="gAAAAABh..."
ENV ENCRYPTED_SPOTIFY_SECRET="gAAAAABh..."
```

### 4. Build and Push Docker Image

```bash
./dev_tools/build-and-push.sh
```

This builds the image with your encrypted credentials and pushes it to Docker Hub.

### 5. Deploy to Friends' Raspberry Pis

Your friends can now pull and run the image:

```bash
docker pull dyonak/albumplayer:latest
docker compose up -d
```

The credentials will be automatically decrypted when the container starts!

---

## How It Works

### Runtime Decryption Flow

1. Container starts → `AlbumPlayer.py` runs
2. `Registrar.__init__()` is called
3. Checks for environment variables: `ENCRYPTION_KEY`, `ENCRYPTED_SPOTIFY_ID`, `ENCRYPTED_SPOTIFY_SECRET`
4. If found, decrypts credentials using the Fernet cipher
5. Uses decrypted credentials to authenticate with Spotify API
6. If env vars not found, falls back to `config.json` (for local development)

### File Priority

```
1. Encrypted environment variables (production)
   ↓ (if not found)
2. config.json (local development)
   ↓ (if not found)
3. Error: No credentials available
```

---

## Security Considerations

### What This Protects Against
- ✅ Casual users viewing credentials in plaintext
- ✅ Credentials accidentally committed to git
- ✅ Easy extraction via `docker inspect` or config files

### What This DOES NOT Protect Against
- ❌ Determined users with root access to the Pi
- ❌ Users who inspect running Python processes
- ❌ Users who modify the container to log credentials

### Important Security Notes

1. **Anyone with root on the Pi can extract credentials**
   - They can read environment variables from the running process
   - They can modify the Python code to print credentials
   - They can attach a debugger to the running process

2. **The encryption key is in the image**
   - Both the encrypted data AND the key are in the same place
   - This is security through obscurity, not true encryption

3. **Only share with trusted friends**
   - Assume anyone running your image can get the credentials
   - Monitor Spotify API usage for abuse
   - Spotify may have rate limits/quotas

4. **Check Spotify's Terms of Service**
   - Spotify may prohibit embedding credentials in distributed apps
   - You may be required to use OAuth for end-users
   - This approach is best for personal/small group use

---

## Development Workflow

### Local Development (without encryption)

Create a `config.json` file for local testing:

```bash
cp example-config.json config.json
# Edit config.json with your credentials
```

The code will automatically fall back to `config.json` if env vars aren't set.

### Testing Encrypted Credentials Locally

You can test the encryption flow without Docker:

```bash
# Encrypt credentials
python3 dev_tools/encrypt_credentials.py

# Export to environment
export ENCRYPTION_KEY="your-key"
export ENCRYPTED_SPOTIFY_ID="your-encrypted-id"
export ENCRYPTED_SPOTIFY_SECRET="your-encrypted-secret"

# Test
python3 Registrar.py
```

---

## Troubleshooting

### "Spotify credentials not found" Error

**Cause**: Neither env vars nor config.json are available

**Solution**:
1. For production: Ensure Dockerfile has the encrypted values
2. For development: Create a `config.json` file

### "Failed to decrypt credentials" Error

**Cause**: Encryption key or encrypted values are incorrect

**Solution**:
1. Re-run `python3 dev_tools/encrypt_credentials.py`
2. Ensure you copied ALL of the output (including quotes)
3. Check for whitespace issues in the Dockerfile

### Credentials Work Locally But Not in Container

**Cause**: config.json exists locally but isn't in the Docker image

**Solution**:
1. Use the encryption method (recommended)
2. Or: Create a volume mount for config.json (less secure)

---

## Alternative: Config File Method (Not Recommended)

If you prefer NOT to use encryption, you can mount config.json as a volume:

**docker-compose.yml:**
```yaml
volumes:
  - ./config.json:/app/config.json  # Add this line
```

Then create `config.json` on each Pi. This is less convenient but simpler.

---

## Questions?

- Encryption not working? Check the console logs when the container starts
- Want to rotate credentials? Re-run the encryption script and rebuild the image
- Need to revoke access? Change your Spotify API credentials in the developer dashboard
