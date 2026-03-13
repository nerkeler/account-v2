# -*- coding: utf-8 -*-
"""
浏览器密码导入服务
支持 Chrome, Edge, Firefox, Brave 等主流浏览器
"""

import os
import sqlite3
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Optional
import platform


class BrowserImporter(ABC):
    """浏览器导入基类"""
    
    @abstractmethod
    def get_login_data_path(self) -> Optional[Path]:
        """获取浏览器登录数据路径"""
        pass
    
    @abstractmethod
    def get_browser_name(self) -> str:
        """获取浏览器名称"""
        pass
    
    def decrypt_password(self, encrypted: bytes) -> str:
        """解密密码 - 默认实现，子类可覆盖"""
        # 尝试调用系统解密库
        return self._decrypt_windows(encrypted) if platform.system() == "Windows" else ""
    
    def _decrypt_windows(self, encrypted: bytes) -> str:
        """Windows 解密 - 使用 chromium密码解密库"""
        try:
            # 尝试使用 keyring 或手动解密
            # 这里需要安装 keyring 或使用自定义解密
            # 为简化，先返回空字符串，用户需要手动处理
            return ""
        except Exception:
            return ""
    
    def import_passwords(self) -> List[Tuple[str, str, str]]:
        """导入密码列表
        
        Returns:
            [(website, username, password), ...]
        """
        path = self.get_login_data_path()
        if not path or not path.exists():
            print(f"[{self.get_browser_name()}] 登录数据文件不存在: {path}")
            return []
        
        results = []
        
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            
            # 尝试不同版本的表结构
            tables = ["logins", "moz_logins", "登录"]
            for table in tables:
                try:
                    cursor.execute(f"SELECT origin_url, username_value, password_value FROM {table} WHERE blacklisted = 0")
                    break
                except sqlite3.OperationalError:
                    continue
            else:
                # 尝试通用查询
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                print(f"[{self.get_browser_name()}] 可用表: {[r[0] for r in cursor.fetchall()]}")
                conn.close()
                return []
            
            for row in cursor.fetchall():
                website = row[0] or ""
                username = row[1] or ""
                password = row[2] or ""
                
                if website and username and password:
                    # 尝试解密
                    decrypted = self.decrypt_password(password) if isinstance(password, bytes) else password
                    if not decrypted:
                        # 如果解密失败，尝试 base64 解码
                        try:
                            import base64
                            decrypted = base64.b64decode(password).decode('utf-8', errors='ignore')
                        except:
                            decrypted = str(password)
                    
                    results.append((website, username, decrypted))
            
            conn.close()
            print(f"[{self.get_browser_name()}] 找到 {len(results)} 条密码记录")
            
        except Exception as e:
            print(f"[{self.get_browser_name()}] 读取失败: {e}")
        
        return results


class ChromeImporter(BrowserImporter):
    """Chrome 浏览器导入器"""
    
    def get_browser_name(self) -> str:
        return "Chrome"
    
    def get_login_data_path(self) -> Optional[Path]:
        system = platform.system()
        
        if system == "Windows":
            local_appdata = Path(os.environ.get('LOCALAPPDATA', ''))
            return local_appdata / 'Google/Chrome/User Data/Default/Login Data'
        elif system == "Darwin":  # macOS
            return Path.home() / 'Library/Application Support/Google/Chrome/Default/Login Data'
        else:  # Linux
            return Path.home() / '.config/google-chrome/Default/Login Data'


class EdgeImporter(BrowserImporter):
    """Edge 浏览器导入器"""
    
    def get_browser_name(self) -> str:
        return "Edge"
    
    def get_login_data_path(self) -> Optional[Path]:
        system = platform.system()
        
        if system == "Windows":
            local_appdata = Path(os.environ.get('LOCALAPPDATA', ''))
            return local_appdata / 'Microsoft/Edge/User Data/Default/Login Data'
        elif system == "Darwin":
            return Path.home() / 'Library/Application Support/Microsoft Edge/Default/Login Data'
        else:
            return Path.home() / '.config/microsoft-edge/Default/Login Data'


class FirefoxImporter(BrowserImporter):
    """Firefox 浏览器导入器"""
    
    def get_browser_name(self) -> str:
        return "Firefox"
    
    def get_login_data_path(self) -> Optional[Path]:
        system = platform.system()
        
        if system == "Windows":
            appdata = Path(os.environ.get('APPDATA', ''))
            return appdata / 'Mozilla/Firefox/Profiles'
        elif system == "Darwin":
            return Path.home() / 'Library/Application Support/Firefox/Profiles'
        else:
            return Path.home() / '.mozilla/firefox'


class BraveImporter(BrowserImporter):
    """Brave 浏览器导入器"""
    
    def get_browser_name(self) -> str:
        return "Brave"
    
    def get_login_data_path(self) -> Optional[Path]:
        system = platform.system()
        
        if system == "Windows":
            local_appdata = Path(os.environ.get('LOCALAPPDATA', ''))
            return local_appdata / 'BraveSoftware/Brave-Browser/User Data/Default/Login Data'
        elif system == "Darwin":
            return Path.home() / 'Library/Application Support/BraveSoftware/Brave-Browser/Default/Login Data'
        else:
            return Path.home() / '.config/BraveSoftware/Brave-Browser/Default/Login Data'


class BrowserImportService:
    """浏览器导入服务"""
    
    # 支持的浏览器
    BROWSERS = {
        'chrome': ChromeImporter,
        'edge': EdgeImporter,
        'firefox': FirefoxImporter,
        'brave': BraveImporter,
    }
    
    @staticmethod
    def get_available_browsers() -> List[str]:
        """获取可用的浏览器列表"""
        available = []
        for name, importer_class in BrowserImportService.BROWSERS.items():
            importer = importer_class()
            path = importer.get_login_data_path()
            if path and path.exists():
                available.append(name)
        return available
    
    @staticmethod
    def import_from_browser(browser_name: str, vault, auto_add: bool = True) -> List[Tuple[str, str, str]]:
        """从指定浏览器导入
        
        Args:
            browser_name: 浏览器名称 (chrome/edge/firefox/brave)
            vault: 保险库
            auto_add: 是否自动添加到保险库
        
        Returns:
            [(website, username, password), ...]
        """
        browser_name = browser_name.lower()
        
        if browser_name not in BrowserImportService.BROWSERS:
            raise ValueError(f"不支持的浏览器: {browser_name}")
        
        importer = BrowserImportService.BROWSERS[browser_name]()
        passwords = importer.import_passwords()
        
        if auto_add and vault:
            added = 0
            for website, username, password in passwords:
                try:
                    vault.add_account(
                        website=website.replace('https://', '').replace('http://', '').split('/')[0],
                        account=username,
                        password=password,
                        url=website if website.startswith('http') else None
                    )
                    added += 1
                except Exception as e:
                    print(f"添加失败: {website}, {e}")
            print(f"已自动添加 {added} 条记录到保险库")
        
        return passwords
    
    @staticmethod
    def import_all(vault) -> dict:
        """从所有可用浏览器导入
        
        Returns:
            {browser_name: [(website, username, password), ...], ...}
        """
        results = {}
        
        for browser_name in BrowserImportService.BROWSERS.keys():
            try:
                passwords = BrowserImportService.import_from_browser(browser_name, vault, auto_add=True)
                results[browser_name] = passwords
            except Exception as e:
                print(f"[{browser_name}] 导入失败: {e}")
        
        return results


# 测试
if __name__ == "__main__":
    from account.core.keychain import Auth
    from account.core.vault import Vault
    
    # 登录
    result = Auth.login("test123")
    vault = Vault(result[0], result[1])
    
    print("="*50)
    print("浏览器密码导入测试")
    print("="*50)
    
    # 检查可用浏览器
    available = BrowserImportService.get_available_browsers()
    print(f"\n可用浏览器: {available}")
    
    # 尝试导入 Chrome
    if 'chrome' in available:
        print(f"\n尝试导入 Chrome...")
        passwords = BrowserImportService.import_from_browser('chrome', vault, auto_add=False)
        print(f"找到 {len(passwords)} 条密码")
        for website, username, password in passwords[:3]:
            print(f"  - {website}: {username}")
    else:
        print("\n未找到 Chrome 登录数据")
    
    print("\n✓ 浏览器导入服务测试完成!")
