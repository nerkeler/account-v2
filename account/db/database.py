# -*- coding: utf-8 -*-
"""
数据库模块
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from pathlib import Path

Base = declarative_base()


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    """分类模型"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    icon = Column(String(50), default="📁")
    color = Column(String(20), default="#0078D4")
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="categories")
    accounts = relationship("Account", back_populates="category")


class Account(Base):
    """账号模型"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    website_name = Column(String(200), nullable=False)
    account = Column(String(200), nullable=False)
    encrypted_password = Column(String(500), nullable=False)
    url = Column(String(500), nullable=True)
    encrypted_note = Column(String(2000), nullable=True)
    favorite = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="accounts")
    category = relationship("Category", back_populates="accounts")


class Database:
    """数据库管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认使用用户目录
            db_dir = Path.home() / ".account-v2"
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / "vault.db"
        
        self.db_path = str(db_path)
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def close(self):
        """关闭连接"""
        self.engine.dispose()


# 全局数据库实例
_db = None


def get_db(db_path: str = None) -> Database:
    """获取全局数据库实例"""
    global _db
    if _db is None:
        _db = Database(db_path)
        _db.create_tables()
    return _db


def close_db():
    """关闭数据库"""
    global _db
    if _db:
        _db.close()
        _db = None
