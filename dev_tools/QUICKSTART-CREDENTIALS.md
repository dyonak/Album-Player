# Quick Start: Encrypting Spotify Credentials

**Goal**: Embed your Spotify API credentials into the Docker image securely.

## Prerequisites

- You have Spotify API credentials (Client ID and Secret)
- Python 3 installed locally

## Steps

### 1. Run the Encryption Script

```bash
python3 dev_tools/encrypt_credentials.py
```

Enter your credentials when prompted.

### 2. Copy the Output

You'll see output like this:

```
Add these to your Dockerfile as ENV variables:

ENV ENCRYPTION_KEY=QcsCPag7P9fd2PxKgWOT...
ENV ENCRYPTED_SPOTIFY_ID="gAAAAABh..."
ENV ENCRYPTED_SPOTIFY_SECRET="gAAAAABh..."
```

### 3. Update Dockerfile

Open `Dockerfile` and find lines 32-34. Replace:

```dockerfile
ENV ENCRYPTION_KEY="REPLACE_WITH_YOUR_ENCRYPTION_KEY"
ENV ENCRYPTED_SPOTIFY_ID="REPLACE_WITH_ENCRYPTED_ID"
ENV ENCRYPTED_SPOTIFY_SECRET="REPLACE_WITH_ENCRYPTED_SECRET"
```

With the values from step 2.

### 4. Build and Push

```bash
./dev_tools/build-and-push.sh
```

### 5. Deploy

On your Pi (or your friends' Pis):

```bash
docker pull dyonak/albumplayer:latest
docker compose up -d
```

Done! The credentials are now encrypted in the image.

---

## Verification

Check the container logs to confirm credentials loaded:

```bash
docker logs album-player | grep credentials
```

You should see:
```
✓ Successfully loaded credentials from encrypted environment variables
```

---

## Need Help?

See [CREDENTIALS-SETUP.md](CREDENTIALS-SETUP.md) for detailed documentation.
