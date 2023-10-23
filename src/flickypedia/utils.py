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


def size_at(sizes, *, desired_size):
    """
    Given a list of sizes of Flickr photo, return the info about
    the desired size.
    """
    try:
        return next(s for s in sizes if s["label"] == desired_size)
    except StopIteration:
        # NOTE: Flickr has a published list of possible sizes here:
        # https://www.flickr.com/services/api/misc.urls.html
        #
        # At some point it might be worthwhile to do some sort of
        # fallback here, e.g. if you ask for a Large but it's not
        # available, you get the Medium as the next-best option.
        raise ValueError(f"This photo is not available at size {desired_size!r}")
