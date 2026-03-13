# -*- coding: utf-8 -*-
"""
加密模块 - AES-256-GCM
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import secrets
import base64
from dataclasses import dataclass
from typing import Union


@dataclass
class EncryptedData:
    """加密数据容器"""
    ciphertext: bytes
    nonce: bytes
    salt: bytes


class AESCipher:
    """AES-256-GCM 加密器"""
    
    KEY_LENGTH = 32   # 256 bits
    NONCE_LENGTH = 12  # 96 bits
    SALT_LENGTH = 16   # 128 bits
    ITERATIONS = 600000  # OWASP 推荐
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """使用 PBKDF2 派生密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=AESCipher.KEY_LENGTH,
            salt=salt,
            iterations=AESCipher.ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))
    
    @staticmethod
    def encrypt(plaintext: str, password: str = None, salt: bytes = None, key: bytes = None) -> EncryptedData:
        """加密数据
        
        Args:
            plaintext: 要加密的明文
            password: 密码 (与 key 二选一)
            salt: 盐 (与 key 二选一)
            key: 直接使用字节密钥
        """
        if key is None:
            salt = salt or secrets.token_bytes(AESCipher.SALT_LENGTH)
            key = AESCipher.derive_key(password, salt)
        else:
            salt = salt or secrets.token_bytes(AESCipher.SALT_LENGTH)
        
        nonce = secrets.token_bytes(AESCipher.NONCE_LENGTH)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        return EncryptedData(ciphertext=ciphertext, nonce=nonce, salt=salt)
    
    @staticmethod
    def decrypt(encrypted: EncryptedData, password: str = None, key: bytes = None) -> str:
        """解密数据
        
        Args:
            encrypted: 加密数据
            password: 密码 (与 key 二选一)
            key: 直接使用字节密钥
        """
        if key is None:
            key = AESCipher.derive_key(password, encrypted.salt)
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(encrypted.nonce, encrypted.ciphertext, None).decode('utf-8')
    
    @staticmethod
    def to_string(encrypted: EncryptedData) -> str:
        """序列化为字符串 (salt:nonce:ciphertext)"""
        combined = encrypted.salt + encrypted.nonce + encrypted.ciphertext
        return base64.b64encode(combined).decode('utf-8')
    
    @staticmethod
    def from_string(data: str) -> EncryptedData:
        """从字符串反序列化"""
        combined = base64.b64decode(data)
        salt = combined[:AESCipher.SALT_LENGTH]
        nonce = combined[AESCipher.SALT_LENGTH:AESCipher.SALT_LENGTH + AESCipher.NONCE_LENGTH]
        ciphertext = combined[AESCipher.SALT_LENGTH + AESCipher.NONCE_LENGTH:]
        return EncryptedData(ciphertext=ciphertext, nonce=nonce, salt=salt)


# 测试代码
if __name__ == "__main__":
    # 测试加密解密
    password = "test_password_123"
    plaintext = "Hello, World! 这是一个测试密码: abc123"
    
    # 加密
    encrypted = AESCipher.encrypt(plaintext, password)
    encrypted_str = AESCipher.to_string(encrypted)
    print(f"加密后: {encrypted_str[:50]}...")
    
    # 解密
    encrypted2 = AESCipher.from_string(encrypted_str)
    decrypted = AESCipher.decrypt(encrypted2, password)
    print(f"解密后: {decrypted}")
    
    # 验证
    assert plaintext == decrypted, "加解密失败!"
    print("✓ 加解密测试通过!")
    
    # 测试密钥派生
    salt1 = secrets.token_bytes(16)
    key1 = AESCipher.derive_key(password, salt1)
    key2 = AESCipher.derive_key(password, salt1)
    assert key1 == key2, "相同密码+盐应得到相同密钥"
    print("✓ 密钥派生测试通过!")
