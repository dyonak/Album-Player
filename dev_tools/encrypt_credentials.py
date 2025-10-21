#!/usr/bin/env python3
"""
Utility script to encrypt Spotify API credentials.
Run this locally to generate encrypted credentials for the Docker image.

Usage:
    python3 encrypt_credentials.py

This will prompt for your credentials and output encrypted values
to paste into your Dockerfile.
"""

from cryptography.fernet import Fernet
import base64
import os
import getpass

def generate_key():
    """Generate a new encryption key."""
    return Fernet.generate_key()

def encrypt_credential(key, credential):
    """Encrypt a credential string."""
    cipher = Fernet(key)
    return cipher.encrypt(credential.encode()).decode()

def main():
    print("=" * 60)
    print("Spotify Credentials Encryption Utility")
    print("=" * 60)
    print()

    # Check if key already exists
    key_file = ".encryption_key"
    if os.path.exists(key_file):
        print(f"Found existing encryption key in {key_file}")
        with open(key_file, 'rb') as f:
            key = f.read()
        print("Using existing key for consistency.")
    else:
        print("Generating new encryption key...")
        key = generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        print(f"✓ Key saved to {key_file} (keep this file secret!)")

    print()
    print("Enter your Spotify API credentials:")
    print("(Get these from: https://developer.spotify.com/dashboard)")
    print()

    # Get credentials from user
    client_id = getpass.getpass("Spotify Client ID: ").strip()
    client_secret = getpass.getpass("Spotify Client Secret: ").strip()

    if not client_id or not client_secret:
        print("\n❌ Error: Both credentials are required!")
        return

    # Encrypt credentials
    print("\nEncrypting credentials...")
    encrypted_id = encrypt_credential(key, client_id)
    encrypted_secret = encrypt_credential(key, client_secret)

    print("\n" + "=" * 60)
    print("✓ Encryption Complete!")
    print("=" * 60)
    print()
    print("Add these to your Dockerfile as ENV variables:")
    print()
    print(f"ENV ENCRYPTION_KEY={key.decode()}")
    print(f'ENV ENCRYPTED_SPOTIFY_ID="{encrypted_id}"')
    print(f'ENV ENCRYPTED_SPOTIFY_SECRET="{encrypted_secret}"')
    print()
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT SECURITY NOTES:")
    print("  1. Keep .encryption_key file SECRET (it's in .gitignore)")
    print("  2. These encrypted values are obfuscated, NOT truly secure")
    print("  3. Anyone with root on the Pi can extract these")
    print("  4. Only share with trusted friends")
    print("=" * 60)

if __name__ == "__main__":
    main()
