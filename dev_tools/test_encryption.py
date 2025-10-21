#!/usr/bin/env python3
"""
Test script to verify encryption/decryption works correctly.
This simulates what happens in the container.
"""

from cryptography.fernet import Fernet
import os

def test_encryption_flow():
    """Test the full encryption/decryption flow."""
    print("=" * 60)
    print("Testing Encryption/Decryption Flow")
    print("=" * 60)
    print()

    # Test credentials
    test_client_id = "test_id_12345"
    test_client_secret = "test_secret_67890"

    # Step 1: Generate key
    print("1. Generating encryption key...")
    key = Fernet.generate_key()
    print(f"   Key: {key.decode()[:20]}...")
    print()

    # Step 2: Encrypt credentials
    print("2. Encrypting credentials...")
    cipher = Fernet(key)
    encrypted_id = cipher.encrypt(test_client_id.encode()).decode()
    encrypted_secret = cipher.encrypt(test_client_secret.encode()).decode()
    print(f"   Encrypted ID: {encrypted_id[:40]}...")
    print(f"   Encrypted Secret: {encrypted_secret[:40]}...")
    print()

    # Step 3: Decrypt credentials (simulating container startup)
    print("3. Decrypting credentials (as container would)...")
    cipher2 = Fernet(key)  # Create new cipher instance
    decrypted_id = cipher2.decrypt(encrypted_id.encode()).decode()
    decrypted_secret = cipher2.decrypt(encrypted_secret.encode()).decode()
    print(f"   Decrypted ID: {decrypted_id}")
    print(f"   Decrypted Secret: {decrypted_secret}")
    print()

    # Step 4: Verify
    print("4. Verifying...")
    if decrypted_id == test_client_id and decrypted_secret == test_client_secret:
        print("   ✅ SUCCESS: Encryption/decryption working correctly!")
        print()
        print("=" * 60)
        print("Your encryption setup is ready to use!")
        print("=" * 60)
        return True
    else:
        print("   ❌ FAILED: Decrypted values don't match originals")
        return False

if __name__ == "__main__":
    success = test_encryption_flow()
    exit(0 if success else 1)
