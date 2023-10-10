from cryptography.fernet import Fernet

from flickypedia.utils import decrypt_string, encrypt_string


def test_encryption_is_symmetric():
    key = Fernet.generate_key()
    
    plaintext = "my deep dark secret"
    ciphertext = encrypt_string(key, plaintext)
    assert decrypt_string(key, ciphertext) == plaintext
