from cryptography.fernet import Fernet


def encrypt_string(key: bytes, plaintext: str) -> bytes:
    """
    Encrypt an ASCII string using Fernet.
    See https://cryptography.io/en/latest/fernet/#cryptography.fernet.Fernet
    """
    return Fernet(key).encrypt(plaintext.encode("ascii"))


def decrypt_string(key: bytes, ciphertext: bytes) -> str:
    """
    Decode an ASCII string using Fernet.
    See https://cryptography.io/en/latest/fernet/#cryptography.fernet.Fernet
    """
    return Fernet(key).decrypt(ciphertext).decode("ascii")


def a_href(url):
    """
    Render a URL as an <a> tag with the URL as both target and text.

        >>> a_href("https://example.net")
        '<a href="https://example.net">https://example.net</a>'

    This is a utility function for Flask templates.

    """
    return f'<a href="{url}">{url}</a>'
