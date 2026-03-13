#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI 测试脚本
"""

from account.core.keychain import Auth
from account.core.vault import Vault

def test_full_flow():
    # 登录
    result = Auth.login("test123")
    if not result:
        print("登录失败")
        return
    
    user_id, encryption_key = result
    vault = Vault(user_id, encryption_key)
    
    # 添加测试账号
    vault.add_account(
        website="Bilibili",
        account="testuser",
        password="bilibili2024!",
        url="https://bilibili.com",
        note="娱乐账号"
    )
    
    # 列出
    accounts = vault.get_all_accounts()
    print(f"当前共有 {len(accounts)} 个账号:")
    for i, acc in enumerate(accounts, 1):
        print(f"  {i}. {acc.website_name} - {acc.account}")
    
    # 搜索
    results = vault.search("Git")
    print(f"\n搜索 'Git': {len(results)} 条")
    
    print("\n✓ CLI 测试通过!")

if __name__ == "__main__":
    test_full_flow()
