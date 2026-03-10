"""
Script to encrypt API key for Supabase storage.
Run this locally after setting ENCRYPTION_KEY in .env
"""
import os
import sys
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_api_key(plaintext_key: str) -> str:
    """Encrypt API key using AES-256-GCM"""
    key_b64 = os.environ.get("ENCRYPTION_KEY")
    if not key_b64:
        raise ValueError("ENCRYPTION_KEY not set in environment")
    
    encryption_key = base64.b64decode(key_b64)
    aesgcm = AESGCM(encryption_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext_key.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python encrypt_key.py <your_nvidia_api_key>")
        sys.exit(1)
    
    api_key = sys.argv[1]
    encrypted = encrypt_api_key(api_key)
    print(f"Encrypted key: {encrypted}")
    print("\nUse this value in the SQL INSERT statement:")
    print(f"INSERT INTO ai_providers (name, display_name, base_url, api_key_encrypted, is_enabled, priority) VALUES ('nvidia', 'NVIDIA NIM', 'https://integrate.api.nvidia.com/v1', '{encrypted}', true, 10);")
