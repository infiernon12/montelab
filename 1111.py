import os

def generate_hmac_sha256_key(length=64):
    # Генерирует случайный ключ длиной length байт
    key = os.urandom(length)
    return key.hex()

# Пример генерации секретного ключа
secret_key = generate_hmac_sha256_key()
print(secret_key)
