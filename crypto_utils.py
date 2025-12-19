"""
加密工具模块 - 提供安全的加密/解密功能
使用 AES-256-GCM 加密 + PBKDF2 密钥派生
"""

import os
import json
import hashlib
import base64
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


# 安全参数配置
SALT_SIZE = 32          # 盐值长度（字节）
NONCE_SIZE = 12         # GCM nonce 长度（字节）
KEY_SIZE = 32           # AES-256 密钥长度（字节）
ITERATIONS = 600000     # PBKDF2 迭代次数（OWASP 2023 推荐）


class CryptoError(Exception):
    """加密/解密相关异常"""
    pass


def generate_salt() -> bytes:
    """生成随机盐值"""
    return os.urandom(SALT_SIZE)


def derive_key(master_password: str, salt: bytes) -> bytes:
    """
    从主密码派生加密密钥
    使用 PBKDF2-HMAC-SHA256，600000 次迭代
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    return kdf.derive(master_password.encode('utf-8'))


def encrypt_data(data: dict, master_password: str) -> bytes:
    """
    加密数据
    
    返回格式: salt (32 bytes) + nonce (12 bytes) + ciphertext + tag
    """
    # 生成随机盐值和 nonce
    salt = generate_salt()
    nonce = os.urandom(NONCE_SIZE)
    
    # 派生密钥
    key = derive_key(master_password, salt)
    
    # 将数据转为 JSON 字符串
    plaintext = json.dumps(data, ensure_ascii=False).encode('utf-8')
    
    # AES-256-GCM 加密
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    
    # 组合: salt + nonce + ciphertext（包含 auth tag）
    return salt + nonce + ciphertext


def decrypt_data(encrypted_data: bytes, master_password: str) -> dict:
    """
    解密数据
    
    如果密码错误或数据损坏，会抛出 CryptoError
    """
    if len(encrypted_data) < SALT_SIZE + NONCE_SIZE + 16:
        raise CryptoError("加密数据格式无效")
    
    # 提取各部分
    salt = encrypted_data[:SALT_SIZE]
    nonce = encrypted_data[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = encrypted_data[SALT_SIZE + NONCE_SIZE:]
    
    # 派生密钥
    key = derive_key(master_password, salt)
    
    # AES-256-GCM 解密
    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        raise CryptoError("解密失败：密码错误或数据损坏")
    
    # 解析 JSON
    try:
        return json.loads(plaintext.decode('utf-8'))
    except json.JSONDecodeError:
        raise CryptoError("数据格式错误")


def generate_password(length: int = 16, 
                      use_uppercase: bool = True,
                      use_lowercase: bool = True,
                      use_digits: bool = True,
                      use_symbols: bool = True) -> str:
    """
    生成安全的随机密码
    """
    import secrets
    import string
    
    chars = ""
    if use_lowercase:
        chars += string.ascii_lowercase
    if use_uppercase:
        chars += string.ascii_uppercase
    if use_digits:
        chars += string.digits
    if use_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    if not chars:
        chars = string.ascii_letters + string.digits
    
    return ''.join(secrets.choice(chars) for _ in range(length))


def verify_master_password(encrypted_data: bytes, master_password: str) -> bool:
    """
    验证主密码是否正确
    """
    try:
        decrypt_data(encrypted_data, master_password)
        return True
    except CryptoError:
        return False


def compute_file_checksum(filepath: str) -> str:
    """计算文件 SHA256 校验和"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()
