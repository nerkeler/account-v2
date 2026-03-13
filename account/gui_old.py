# -*- coding: utf-8 -*-
"""
GUI 主窗口 - CustomTkinter
"""

import customtkinter as ctk
from typing import Optional

from account.core.keychain import Auth
from account.core.vault import Vault
from account.services.password_generator import PasswordGenerator

# 设置主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class LoginDialog(ctk.CTkToplevel):
    """登录对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("登录 - Account V2")
        self.geometry("400x220")
        self.resizable(False, False)
        
        # 居中
        self.transient(parent)
        
        # Windows 兼容：移除 grab_set()
        # self.grab_set()
        
        # UI
        self.password = None
        self.login_success = False
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="🔐 主密码", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.password_entry = ctk.CTkEntry(frame, show="*", width=250)
        self.password_entry.pack(pady=10)
        self.password_entry.bind("<Return>", lambda e: self.submit())
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="登录", command=self.submit, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="取消", command=self.cancel, width=100).pack(side="left", padx=10)
        
        self.error_label = ctk.CTkLabel(frame, text="", text_color="red", font=("Arial", 12))
        self.error_label.pack()
        
        self.password_entry.focus()
    
    def submit(self):
        password = self.password_entry.get()
        if not password:
            self.error_label.configure(text="⚠️ 请输入密码")
            return
        
        try:
            result = Auth.login(password)
            if result is None:
                self.error_label.configure(text="❌ 密码错误，请重试")
                self.password_entry.delete(0, "end")
                return
            
            self.password = password
            self.login_success = True
            self.destroy()
        except Exception as e:
            self.error_label.configure(text=f"❌ 登录失败: {str(e)}")
    
    def cancel(self):
        self.password = None
        self.destroy()


class AddAccountDialog(ctk.CTkToplevel):
    """添加账号对话框"""
    
    def __init__(self, parent, vault: Vault):
        super().__init__(parent)
        self.vault = vault
        self.result = None
        
        self.title("添加账号")
        self.geometry("450x400")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
    
    def _setup_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 网站名称
        ctk.CTkLabel(frame, text="网站名称:").grid(row=0, column=0, sticky="w", pady=10)
        self.website_entry = ctk.CTkEntry(frame, width=280)
        self.website_entry.grid(row=0, column=1, pady=10)
        
        # 账号
        ctk.CTkLabel(frame, text="账号:").grid(row=1, column=0, sticky="w", pady=10)
        self.account_entry = ctk.CTkEntry(frame, width=280)
        self.account_entry.grid(row=1, column=1, pady=10)
        
        # 密码
        ctk.CTkLabel(frame, text="密码:").grid(row=2, column=0, sticky="w", pady=10)
        password_frame = ctk.CTkFrame(frame, fg_color="transparent")
        password_frame.grid(row=2, column=1, pady=10)
        
        self.password_entry = ctk.CTkEntry(password_frame, show="*", width=200)
        self.password_entry.pack(side="left")
        
        ctk.CTkButton(password_frame, text="🎲", width=35, command=self.generate_password).pack(side="left", padx=5)
        ctk.CTkButton(password_frame, text="👁", width=35, command=self.toggle_password).pack(side="left")
        
        # 网址
        ctk.CTkLabel(frame, text="网址:").grid(row=3, column=0, sticky="w", pady=10)
        self.url_entry = ctk.CTkEntry(frame, width=280)
        self.url_entry.grid(row=3, column=1, pady=10)
        
        # 备注
        ctk.CTkLabel(frame, text="备注:").grid(row=4, column=0, sticky="nw", pady=10)
        self.note_text = ctk.CTkTextbox(frame, width=280, height=60)
        self.note_text.grid(row=4, column=1, pady=10)
        
        # 按钮
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ctk.CTkButton(btn_frame, text="保存", command=self.save, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="取消", command=self.destroy, width=100).pack(side="left", padx=10)
    
    def generate_password(self):
        pwd = PasswordGenerator.generate()
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, pwd)
    
    def toggle_password(self):
        current = self.password_entry.cget("show")
        self.password_entry.configure(show="" if current == "*" else "*")
    
    def save(self):
        website = self.website_entry.get()
        account = self.account_entry.get()
        password = self.password_entry.get()
        url = self.url_entry.get() or None
        note = self.note_text.get("1.0", "end").strip() or None
        
        if not website or not account or not password:
            return
        
        self.vault.add_account(website, account, password, url, note)
        self.destroy()


class MainWindow(ctk.CTk):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.title("Account V2 - 密码管理器")
        self.geometry("900x600")
        
        self.vault: Optional[Vault] = None
        
        self._setup_ui()
        self._login()
    
    def _setup_ui(self):
        # 顶部工具栏
        toolbar = ctk.CTkFrame(self, height=50)
        toolbar.pack(side="top", fill="x", padx=10, pady=5)
        
        self.search_entry = ctk.CTkEntry(toolbar, placeholder_text="搜索...", width=250)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.search())
        
        ctk.CTkButton(toolbar, text="+ 新增", command=self.add_account).pack(side="right", padx=5)
        ctk.CTkButton(toolbar, text="🔄 刷新", command=self.refresh).pack(side="right", padx=5)
        
        # 主体布局
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 账号列表
        self.list_frame = ctk.CTkScrollableFrame(main_frame, label_text="账号列表")
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 底部状态栏
        status = ctk.CTkFrame(self, height=30)
        status.pack(side="bottom", fill="x")
        
        self.status_label = ctk.CTkLabel(status, text="未登录")
        self.status_label.pack(side="left", padx=10)
    
    def _login(self):
        """登录"""
        # 检查是否已初始化
        if not Auth.is_initialized():
            self.status_label.configure(text="请先运行 CLI 初始化: account init")
            return
        
        login_dlg = LoginDialog(self)
        self.wait_window(login_dlg)
        
        # 用户取消登录
        if login_dlg.password is None or not login_dlg.login_success:
            self.destroy()
            return
        
        # 登录成功，获取 vault
        try:
            result = Auth.login(login_dlg.password)
            if result:
                user_id, encryption_key = result
                self.vault = Vault(user_id, encryption_key)
                self.status_label.configure(text=f"已登录 (ID: {user_id})")
                self.refresh()
            else:
                self.status_label.configure(text="登录失败")
        except Exception as e:
            self.status_label.configure(text=f"错误: {str(e)}")
    
    def refresh(self):
        """刷新列表"""
        if not self.vault:
            return
        
        accounts = self.vault.get_all_accounts()
        self._render_accounts(accounts)
        self.status_label.configure(text=f"共 {len(accounts)} 条记录")
    
    def search(self):
        """搜索"""
        if not self.vault:
            return
        
        keyword = self.search_entry.get().strip()
        if keyword:
            accounts = self.vault.search(keyword)
        else:
            accounts = self.vault.get_all_accounts()
        
        self._render_accounts(accounts)
    
    def _render_accounts(self, accounts):
        """渲染账号列表"""
        # 清空
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        if not accounts:
            ctk.CTkLabel(self.list_frame, text="暂无账号", text_color="gray").pack(pady=20)
            return
        
        for acc in accounts:
            card = ctk.CTkFrame(self.list_frame)
            card.pack(fill="x", pady=2, padx=2)
            
            # 收藏标记
            fav_icon = "⭐" if acc.favorite else "  "
            
            # 网站名
            ctk.CTkLabel(
                card, 
                text=f"{fav_icon} {acc.website_name}", 
                font=("Arial", 14, "bold")
            ).pack(side="left", padx=10, pady=10)
            
            # 账号
            ctk.CTkLabel(
                card,
                text=acc.account,
                text_color="gray"
            ).pack(side="left", padx=10)
            
            # 操作按钮
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=5)
            
            ctk.CTkButton(
                btn_frame, text="👁", width=35,
                command=lambda a=acc: self.show_password(a)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                btn_frame, text="🗑", width=35, fg_color="red",
                command=lambda a=acc: self.delete_account(a)
            ).pack(side="left", padx=2)
    
    def show_password(self, acc):
        """显示密码"""
        dlg = ctk.CTkToplevel(self)
        dlg.title(acc.website_name)
        dlg.geometry("400x250")
        dlg.transient(self)
        
        frame = ctk.CTkFrame(dlg)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text=acc.website_name, font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkLabel(frame, text=f"账号: {acc.account}").pack(pady=5)
        ctk.CTkLabel(frame, text=f"密码: {acc.password}", text_color="yellow").pack(pady=5)
        ctk.CTkLabel(frame, text=f"网址: {acc.url or '-'}").pack(pady=5)
        
        if acc.note:
            ctk.CTkLabel(frame, text=f"备注: {acc.note}").pack(pady=5)
        
        ctk.CTkButton(frame, text="关闭", command=dlg.destroy).pack(pady=20)
    
    def add_account(self):
        """添加账号"""
        if not self.vault:
            return
        
        dlg = AddAccountDialog(self, self.vault)
        self.wait_window(dlg)
        self.refresh()
    
    def delete_account(self, acc):
        """删除账号"""
        if not self.vault:
            return
        
        dlg = ctk.CTkToplevel(self)
        dlg.title("确认删除")
        dlg.geometry("300x120")
        dlg.transient(self)
        
        frame = ctk.CTkFrame(dlg)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text=f"确认删除 {acc.website_name}?").pack(pady=10)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def confirm():
            self.vault.delete_account(acc.id)
            dlg.destroy()
            self.refresh()
        
        ctk.CTkButton(btn_frame, text="删除", fg_color="red", command=confirm).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="取消", command=dlg.destroy).pack(side="left", padx=10)


def main():
    """入口"""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
