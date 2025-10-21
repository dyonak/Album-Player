# Album Player - Development Workflow Guide
This guide explains how to quickly test code changes on your Raspberry Pi without rebuilding and pushing Docker images.

## Overview

Instead of the slow workflow:
1. Make changes → 2. Build image → 3. Push to Docker Hub → 4. Pull on Pi → 5. Test

You now use:
1. Make changes → 2. Run `./deploy-to-pi.sh` → 3. Test (30 seconds!)

## Initial Setup (One-Time)

### 1. Set Up SSH Key Authentication

First, make sure you can SSH to your Pi without a password:

```bash
# If you haven't already set up SSH keys
ssh-copy-id pi@raspberrypi.local

# Test it works
ssh pi@raspberrypi.local exit
```

### 2. Copy Files to the Pi

On your Raspberry Pi, create the project directory:

```bash
ssh pi@raspberrypi.local
mkdir -p ~/album-player
cd ~/album-player
```

Copy the docker-compose.yml to the Pi:

```bash
# From your dev machine
scp docker-compose.yml pi@raspberrypi.local:~/album-player/
```

### 3. Initial Code Sync

From your development machine, sync all code:

```bash
./deploy-to-pi.sh
```

### 4. Start the Container (on Pi)

SSH to your Pi and start the container with volume mounts:

```bash
ssh pi@raspberrypi.local
cd ~/album-player

# Create database directory if it doesn't exist
mkdir -p ~/album_db

# Start the container
docker-compose up -d

# View logs
docker-compose logs -f
```

## Daily Development Workflow

### Making Code Changes

1. **Edit your Python files locally** (on your dev machine)
   - Use your favorite IDE/editor as normal
   - Make changes to any `.py` files

2. **Deploy to Pi**
   ```bash
   ./deploy-to-pi.sh
   ```

   This script will:
   - Sync only changed files (fast!)
   - Restart the Docker container
   - Show you the status

3. **Check the logs**
   ```bash
   ssh pi@raspberrypi.local 'docker logs -f album-player'
   ```

   Or if you're already SSH'd into the Pi:
   ```bash
   docker-compose logs -f
   ```

4. **Test your changes**
   - Scan an NFC tag
   - Check the web interface
   - Verify behavior

### Customizing the Deploy Script

You can customize the deployment with environment variables:

```bash
# Different hostname/IP
PI_HOST=192.168.1.100 ./deploy-to-pi.sh

# Different username
PI_USER=albumplayer ./deploy-to-pi.sh

# Different directory
PI_CODE_DIR=/opt/album-player ./deploy-to-pi.sh

# Combine them
PI_HOST=192.168.1.100 PI_USER=admin ./deploy-to-pi.sh
```

To make these permanent, edit the script or create a `.env` file:

```bash
# .env file (create in project root)
export PI_HOST=192.168.1.100
export PI_USER=pi
export PI_CODE_DIR=/home/pi/album-player
export CONTAINER_NAME=album-player
```

Then source it before deploying:
```bash
source .env && ./deploy-to-pi.sh
```

## Useful Commands

### On Your Dev Machine

```bash
# Quick deploy
./deploy-to-pi.sh

# Deploy and watch logs
./deploy-to-pi.sh && ssh pi@raspberrypi.local 'docker logs -f album-player'

# SSH to Pi
ssh pi@raspberrypi.local
```

### On the Raspberry Pi

```bash
# View logs
docker-compose logs -f

# Restart container
docker-compose restart

# Stop container
docker-compose down

# Start container
docker-compose up -d

# Check container status
docker-compose ps

# Access container shell (for debugging)
docker-compose exec album-player bash

# View only recent logs
docker-compose logs --tail=50 -f

# Pull latest base image (when you update dependencies)
docker-compose pull
docker-compose up -d
```

## When to Rebuild the Docker Image

You only need to rebuild and push the Docker image when you change:

- **Python dependencies** (`requirements.txt`)
- **System packages** (apt packages in Dockerfile)
- **NFC library configuration** (`libnfc.conf`)
- **The run.sh script** (though this can be volume-mounted too)

For these changes:

```bash
# On your dev machine
docker build -t dyonak/albumplayer:latest .
docker push dyonak/albumplayer:latest

# On the Pi
cd ~/album-player
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### "Permission denied" when running deploy script
```bash
chmod +x deploy-to-pi.sh
```

### "Container not found" after deploy
The container isn't running. SSH to Pi and run:
```bash
cd ~/album-player
docker-compose up -d
```

### Changes aren't taking effect
1. Check the container restarted:
   ```bash
   ssh pi@raspberrypi.local 'docker ps'
   ```

2. Verify files were synced:
   ```bash
   ssh pi@raspberrypi.local 'ls -la ~/album-player/*.py'
   ```

3. Check for Python syntax errors in logs:
   ```bash
   ssh pi@raspberrypi.local 'docker logs album-player'
   ```

### Container keeps crashing
View logs to see the error:
```bash
ssh pi@raspberrypi.local 'docker logs album-player'
```

Common issues:
- Database file permissions (`chmod 777 ~/album_db`)
- NFC device not accessible (check `--privileged` flag)
- Sonos speaker not found (check network connectivity)

### Want to revert to production mode
On the Pi, edit `docker-compose.yml` and comment out all the volume mounts except the database:
```yaml
volumes:
  - ${HOME}/album_db:/app/db
  # Comment out all the .py file mounts
```

Then restart:
```bash
docker-compose up -d
```

## Production Deployment

For customer units or production deployment:

1. **Use the pre-built image without volume mounts**
2. Edit `docker-compose.yml` on the Pi to remove all source code volume mounts
3. Only keep the database volume mount

Example production `docker-compose.yml`:
```yaml
version: '3.8'

services:
  album-player:
    image: dyonak/albumplayer:latest
    container_name: album-player
    restart: unless-stopped
    privileged: true
    network_mode: host
    volumes:
      - ${HOME}/album_db:/app/db
    environment:
      - PYTHONUNBUFFERED=1
```

## Tips for Faster Development

1. **Keep logs open in a separate terminal** while developing
   ```bash
   ssh pi@raspberrypi.local 'docker logs -f album-player'
   ```

2. **Use VS Code Remote SSH** for direct Pi editing (if preferred)

3. **Test locally first** when possible (without NFC hardware)

4. **Use git branches** for experimental features

5. **Commit working versions** before major changes
