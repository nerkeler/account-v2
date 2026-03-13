# -*- coding: utf-8 -*-
"""
导入导出服务
"""

import csv
import json
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from account.core.vault import Vault, AccountVO


class ImportExportService:
    """导入导出服务"""
    
    @staticmethod
    def export_csv(vault: Vault, filepath: Path, include_passwords: bool = True) -> int:
        """导出为 CSV
        
        Args:
            vault: 保险库
            filepath: 导出文件路径
            include_passwords: 是否包含密码
        
        Returns:
            导出的记录数
        """
        accounts = vault.get_all_accounts()
        
        fieldnames = ['website_name', 'account', 'url', 'note', 'category', 'favorite']
        if include_passwords:
            fieldnames.append('password')
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for acc in accounts:
                row = {
                    'website_name': acc.website_name,
                    'account': acc.account,
                    'url': acc.url or '',
                    'note': acc.note or '',
                    'category': acc.category or '',
                    'favorite': 'Yes' if acc.favorite else 'No'
                }
                if include_passwords:
                    row['password'] = acc.password
                writer.writerow(row)
        
        return len(accounts)
    
    @staticmethod
    def import_csv(vault: Vault, filepath: Path) -> int:
        """从 CSV 导入
        
        Args:
            vault: 保险库
            filepath: CSV 文件路径
        
        Returns:
            导入的记录数
        """
        count = 0
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Chrome/Edge 导出格式: name,url,username,password,note
            # 标准格式: website_name,account,password,url,note
            fieldnames = reader.fieldnames or []
            
            # 映射字段
            name_field = 'name' if 'name' in fieldnames else 'website_name'
            user_field = 'username' if 'username' in fieldnames else 'account'
            
            for row in reader:
                try:
                    vault.add_account(
                        website=row.get(name_field, '').strip(),
                        account=row.get(user_field, '').strip(),
                        password=row.get('password', '').strip(),
                        url=row.get('url') or None,
                        note=row.get('note') or None
                    )
                    count += 1
                except Exception as e:
                    print(f"导入失败: {row.get(name_field)}, 错误: {e}")
        
        return count
    
    @staticmethod
    def export_json(vault: Vault, filepath: Path, encrypt: bool = False, password: str = None) -> int:
        """导出为 JSON
        
        Args:
            vault: 保险库
            filepath: 导出文件路径
            encrypt: 是否加密
            password: 加密密码
        
        Returns:
            导出的记录数
        """
        accounts = vault.get_all_accounts()
        
        data = {
            'version': '2.0',
            'exported_at': datetime.now().isoformat(),
            'count': len(accounts),
            'accounts': [
                {
                    'website': acc.website_name,
                    'account': acc.account,
                    'password': acc.password,
                    'url': acc.url,
                    'note': acc.note,
                    'category': acc.category,
                    'favorite': acc.favorite
                }
                for acc in accounts
            ]
        }
        
        content = json.dumps(data, ensure_ascii=False, indent=2)
        
        if encrypt and password:
            from account.core.crypto import AESCipher
            encrypted = AESCipher.encrypt(content, password)
            output = {
                'encrypted': True,
                'data': AESCipher.to_string(encrypted)
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return len(accounts)
    
    @staticmethod
    def import_json(vault: Vault, filepath: Path, password: str = None) -> int:
        """从 JSON 导入
        
        Args:
            vault: 保险库
            filepath: JSON 文件路径
            password: 解密密码（如果加密）
        
        Returns:
            导入的记录数
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否加密
        if isinstance(data, dict) and data.get('encrypted'):
            if not password:
                raise ValueError("需要密码来解密")
            
            from account.core.crypto import AESCipher
            encrypted = AESCipher.from_string(data['data'])
            content = AESCipher.decrypt(encrypted, password)
            data = json.loads(content)
        
        accounts = data.get('accounts', [])
        count = 0
        
        for acc in accounts:
            try:
                vault.add_account(
                    website=acc.get('website', ''),
                    account=acc.get('account', ''),
                    password=acc.get('password', ''),
                    url=acc.get('url'),
                    note=acc.get('note')
                )
                count += 1
            except Exception as e:
                print(f"导入失败: {acc.get('website')}, 错误: {e}")
        
        return count


# 测试
if __name__ == "__main__":
    from account.core.keychain import Auth
    from account.core.vault import Vault
    
    # 登录
    result = Auth.login("test123")
    vault = Vault(result[0], result[1])
    
    # 测试导出 CSV
    print("测试导出 CSV...")
    count = ImportExportService.export_csv(vault, Path("/tmp/export.csv"))
    print(f"导出 {count} 条记录到 /tmp/export.csv")
    
    # 测试导入 CSV
    print("\n测试导入 CSV...")
    # 先添加一个测试账号
    vault.add_account("TestSite", "test@test.com", "testpass123", "https://test.com")
    count = ImportExportService.export_csv(vault, Path("/tmp/export2.csv"))
    print(f"再次导出 {count} 条记录")
    
    print("\n✓ 导入导出测试通过!")
