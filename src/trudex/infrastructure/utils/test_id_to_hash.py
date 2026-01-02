import hashlib
import hmac
import string


def generate_alpha_id(n: int, secret_key: str, length: int = 16) -> str:
    data = str(n).encode('utf-8')
    key = secret_key.encode('utf-8')
    
    digest = hmac.new(key, data, hashlib.sha256).digest()
    num = int.from_bytes(digest, byteorder='big')
    
    alphabet = string.ascii_letters
    result = []
    
    while num > 0:
        num, rem = divmod(num, 52)
        result.append(alphabet[rem])
        
    encoded = "".join(result)
    
    if len(encoded) < length:
        encoded = encoded.ljust(length, alphabet[0])
        
    return encoded[:length]
