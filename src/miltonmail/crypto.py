#!/usr/bin/env python3
"""
 Tools for safely storing passwords and other sensitive data

 Copyright (c) 2024 Jev Kuznetsov
"""
import os
from base64 import urlsafe_b64encode
from typing import Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_passphrase() -> str:
    """get passphrase from env variable"""
    passphrase = os.environ.get("MILTON_PASS")
    if not passphrase:
        raise ValueError("Passphrase not found in environment")
    return passphrase


# Derive a key from the passphrase
def derive_key_from_passphrase(passphrase: str, salt: bytes) -> bytes:
    # Use PBKDF2 to derive a key
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return urlsafe_b64encode(kdf.derive(passphrase.encode()))


# Encrypt the password
def encrypt_password(password: str) -> Tuple[bytes, bytes]:

    # Generate a random salt
    salt = os.urandom(16)

    # Derive key from passphrase
    key = derive_key_from_passphrase(get_passphrase(), salt)

    # Create cipher
    cipher = Fernet(key)

    # Encrypt the password
    encrypted_password = cipher.encrypt(password.encode())

    return encrypted_password, salt


# Decrypt the password
def decrypt_password(encrypted_password: bytes, salt: bytes) -> str:
    passphrase = get_passphrase()

    # Derive key from passphrase
    key = derive_key_from_passphrase(passphrase, salt)

    # Create cipher
    cipher = Fernet(key)

    # Decrypt password
    decrypted_password = cipher.decrypt(encrypted_password)

    return decrypted_password.decode()
