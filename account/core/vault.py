# -*- coding: utf-8 -*-
"""
密码保险库 - 核心存储抽象
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

from account.db.database import get_db, Account, Category, User
from account.core.crypto import AESCipher


@dataclass
class AccountVO:
    """账号视图对象"""
    id: int
    website_name: str
    account: str
    password: str
    url: Optional[str]
    note: Optional[str]
    category: Optional[str]
    favorite: bool
    created_at: datetime
    updated_at: datetime


class Vault:
    """密码保险库"""
    
    def __init__(self, user_id: int, encryption_key: bytes):
        self.user_id = user_id
        self.encryption_key = encryption_key
        self.db = get_db()
    
    def _encrypt(self, plaintext: str) -> str:
        """加密明文"""
        encrypted = AESCipher.encrypt(plaintext, key=self.encryption_key)
        return AESCipher.to_string(encrypted)
    
    def _decrypt(self, ciphertext: str) -> str:
        """解密集群"""
        encrypted = AESCipher.from_string(ciphertext)
        return AESCipher.decrypt(encrypted, key=self.encryption_key)
    
    def add_account(self, website: str, account: str, password: str, 
                   url: str = None, note: str = None, category_id: int = None) -> Account:
        """添加账号"""
        encrypted_password = self._encrypt(password)
        encrypted_note = self._encrypt(note) if note else None
        
        session = self.db.get_session()
        try:
            account = Account(
                user_id=self.user_id,
                website_name=website,
                account=account,
                encrypted_password=encrypted_password,
                url=url,
                encrypted_note=encrypted_note,
                category_id=category_id
            )
            session.add(account)
            session.commit()
            session.refresh(account)
            return account
        finally:
            session.close()
    
    def get_account(self, account_id: int) -> Optional[AccountVO]:
        """获取单个账号"""
        session = self.db.get_session()
        try:
            account = session.query(Account).filter(
                Account.id == account_id,
                Account.user_id == self.user_id
            ).first()
            
            if account:
                return self._to_vo(account)
            return None
        finally:
            session.close()
    
    def get_all_accounts(self) -> List[AccountVO]:
        """获取所有账号"""
        session = self.db.get_session()
        try:
            accounts = session.query(Account).filter(
                Account.user_id == self.user_id
            ).order_by(Account.order_index, Account.id).all()
            return [self._to_vo(a) for a in accounts]
        finally:
            session.close()
    
    def search(self, keyword: str) -> List[AccountVO]:
        """搜索账号"""
        session = self.db.get_session()
        try:
            accounts = session.query(Account).filter(
                Account.user_id == self.user_id,
                Account.website_name.like(f"%{keyword}%")
            ).all()
            return [self._to_vo(a) for a in accounts]
        finally:
            session.close()
    
    def update_account(self, account_id: int, website: str = None, account: str = None,
                      password: str = None, url: str = None, note: str = None,
                      favorite: bool = None) -> bool:
        """更新账号"""
        session = self.db.get_session()
        try:
            account_obj = session.query(Account).filter(
                Account.id == account_id,
                Account.user_id == self.user_id
            ).first()
            
            if not account_obj:
                return False
            
            if website: account_obj.website_name = website
            if account: account_obj.account = account
            if password: account_obj.encrypted_password = self._encrypt(password)
            if url is not None: account_obj.url = url
            if note is not None: account_obj.encrypted_note = self._encrypt(note) if note else None
            if favorite is not None: account_obj.favorite = favorite
            
            session.commit()
            return True
        finally:
            session.close()
    
    def delete_account(self, account_id: int) -> bool:
        """删除账号"""
        session = self.db.get_session()
        try:
            account = session.query(Account).filter(
                Account.id == account_id,
                Account.user_id == self.user_id
            ).first()
            
            if not account:
                return False
            
            session.delete(account)
            session.commit()
            return True
        finally:
            session.close()
    
    def get_favorites(self) -> List[AccountVO]:
        """获取收藏夹"""
        session = self.db.get_session()
        try:
            accounts = session.query(Account).filter(
                Account.user_id == self.user_id,
                Account.favorite == True
            ).all()
            return [self._to_vo(a) for a in accounts]
        finally:
            session.close()
    
    def _to_vo(self, account: Account) -> AccountVO:
        """转换为视图对象"""
        return AccountVO(
            id=account.id,
            website_name=account.website_name,
            account=account.account,
            password=self._decrypt(account.encrypted_password),
            url=account.url,
            note=self._decrypt(account.encrypted_note) if account.encrypted_note else None,
            category=account.category.name if account.category else None,
            favorite=account.favorite,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
