import hashlib
import hmac
import string

ALPHABET = string.ascii_letters

def _feistel_round(val: int, key: bytes, rounds: int) -> int:
    msg = f"{val}:{rounds}".encode()
    h = hmac.new(key, msg, hashlib.sha256).digest()
    return int.from_bytes(h[:4], 'big')

def permute_id(n: int, key_str: str, bits: int) -> int:
    key = key_str.encode()
    split = bits // 2
    mask = (1 << split) - 1
    
    left = (n >> split) & mask
    right = n & mask
    
    for i in range(6):
        new_left = right
        f_val = _feistel_round(right, key, i)
        new_right = left ^ (f_val & mask)
        left, right = new_left, new_right
        
    return (left << split) | right

def unpermute_id(n: int, key_str: str, bits: int) -> int:
    key = key_str.encode()
    split = bits // 2
    mask = (1 << split) - 1
    
    left = (n >> split) & mask
    right = n & mask
    
    for i in reversed(range(6)):
        new_right = left
        f_val = _feistel_round(left, key, i)
        new_left = right ^ (f_val & mask)
        left, right = new_left, new_right
        
    return (left << split) | right


def encode_id(n: int, key: str, length: int = 8) -> str:
    bits = length * 5 
    if length >= 8: bits = 44
    elif length == 7: bits = 38
    
    permuted = permute_id(n, key, bits=bits)
    
    chars = []
    for _ in range(length):
        permuted, rem = divmod(permuted, 52)
        chars.append(ALPHABET[rem])
        
    return "".join(chars)

def decode_id(s: str, key: str) -> int:
    num = 0
    for char in reversed(s):
        num = num * 52 + ALPHABET.index(char)
        
    length = len(s)
    bits = length * 5
    if length >= 8: bits = 44
    elif length == 7: bits = 38
    
    return unpermute_id(num, key, bits=bits)
