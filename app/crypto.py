from cryptography.fernet import Fernet

from config import FERNET_KEY

if not FERNET_KEY:
    raise ValueError("FERNET_KEY не найден в переменных окружения")

fernet = Fernet(FERNET_KEY)


def encrypt_card(data: bytes) -> bytes:
    return fernet.encrypt(data)


def decrypt_card(encrypted: bytes) -> bytes:
    return fernet.decrypt(encrypted)
