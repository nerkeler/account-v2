# -*- coding: utf-8 -*-
"""
密钥链管理模块
"""

import hashlib
import secrets
from typing import Optional
from pathlib import Path

from account.db.database import get_db, User
from account.core.crypto import AESCipher


class Keychain:
    """密钥链"""
    
    def __init__(self, password_hash: str, salt: str):
        self.password_hash = password_hash
        self.salt = salt
    
    @staticmethod
    def create(master_password: str) -> "Keychain":
        """创建新的密钥链"""
        salt = secrets.token_hex(16)
        password_hash = Keychain._hash_password(master_password, salt)
        return Keychain(password_hash=password_hash, salt=salt)
    
    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """哈希密码"""
        combined = f"{password}{salt}account-v2"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def verify(self, master_password: str) -> bool:
        """验证主密码"""
        return self._hash_password(master_password, self.salt) == self.password_hash
    
    def get_encryption_key(self, master_password: str) -> bytes:
        """获取加密密钥"""
        return AESCipher.derive_key(master_password, bytes.fromhex(self.salt))
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "password_hash": self.password_hash,
            "salt": self.salt
        }
    
    @staticmethod
    def from_dict(data: dict) -> "Keychain":
        """从字典创建"""
        return Keychain(data["password_hash"], data["salt"])


class Auth:
    """认证管理器"""
    
    CONFIG_FILE = "~/.account-v2/auth.json"
    
    @staticmethod
    def is_initialized() -> bool:
        """检查是否已初始化"""
        config_path = Path(Auth.CONFIG_FILE).expanduser()
        return config_path.exists()
    
    @staticmethod
    def initialize(master_password: str) -> Keychain:
        """初始化密钥链"""
        import json
        
        # 创建密钥链
        keychain = Keychain.create(master_password)
        
        # 保存到配置文件
        config_path = Path(Auth.CONFIG_FILE).expanduser()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(keychain.to_dict(), f)
        
        # 创建数据库用户
        db = get_db()
        session = db.get_session()
        try:
            # 检查是否已有用户
            existing_user = session.query(User).first()
            if not existing_user:
                user = User(
                    username="default",
                    password_hash=keychain.password_hash,
                    salt=keychain.salt
                )
                session.add(user)
                session.commit()
        finally:
            session.close()
        
        return keychain
    
    @staticmethod
    def login(master_password: str) -> Optional[tuple[int, bytes]]:
        """登录验证"""
        import json
        
        if not Auth.is_initialized():
            return None
        
        config_path = Path(Auth.CONFIG_FILE).expanduser()
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        keychain = Keychain.from_dict(data)
        
        if not keychain.verify(master_password):
            return None
        
        # 获取用户ID
        db = get_db()
        session = db.get_session()
        try:
            user = session.query(User).first()
            if not user:
                return None
            
            encryption_key = keychain.get_encryption_key(master_password)
            return user.id, encryption_key
        finally:
            session.close()
    
    @staticmethod
    def get_encryption_key_from_password(master_password: str) -> Optional[bytes]:
        """从密码获取加密密钥（不登录）"""
        import json
        
        if not Auth.is_initialized():
            return None
        
        config_path = Path(Auth.CONFIG_FILE).expanduser()
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        keychain = Keychain.from_dict(data)
        
        if not keychain.verify(master_password):
            return None
        
        return keychain.get_encryption_key(master_password)


# 测试
if __name__ == "__main__":
    import os
    import shutil
    
    # 清理测试环境
    test_dir = Path("~/.account-v2-test").expanduser()
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    # 临时覆盖配置路径
    Auth.CONFIG_FILE = "~/.account-v2-test/auth.json"
    
    # 测试初始化
    print("测试初始化...")
    keychain = Auth.initialize("test_password_123")
    print(f"✓ 创建密钥链成功")
    
    # 测试登录
    print("测试登录...")
    result = Auth.login("test_password_123")
    assert result is not None, "登录失败"
    user_id, encryption_key = result
    print(f"✓ 登录成功, user_id={user_id}, key_len={len(encryption_key)}")
    
    # 测试错误密码
    print("测试错误密码...")
    result = Auth.login("wrong_password")
    assert result is None, "错误密码不应该登录成功"
    print("✓ 错误密码拒绝成功")
    
    print("\n✓ 所有测试通过!")
