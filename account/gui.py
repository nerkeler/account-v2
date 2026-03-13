# -*- coding: utf-8 -*-
"""
GUI 主窗口 - 完整版
支持：居中显示、字体设置、黑白主题切换、子窗口顶层显示
"""

import customtkinter as ctk
from tkinter import ttk
from typing import Optional

from account.core.keychain import Auth
from account.core.vault import Vault
from account.services.password_generator import PasswordGenerator, PasswordConfig
from account.services.import_export import ImportExportService
from account.services.backup import BackupService
from account.services.browser_import import BrowserImportService

APP_FONT = {"family": "Arial", "size": 12}
APP_THEME = "dark"


def center_window(window, width, height):
    """窗口居中"""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def set_theme(mode):
    global APP_THEME
    APP_THEME = mode
    ctk.set_appearance_mode(mode)


class LoginDialog(ctk.CTkToplevel):
    _instance = None
    
    def __new__(cls, parent):
        if cls._instance is not None:
            cls._instance.focus()
            return cls._instance
        return super().__new__(cls)
    
    def __init__(self, parent):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        super().__init__(parent)
        self.title("登录 - Account V2")
        self.geometry("400x320")
        self.transient(parent)
        self.attributes("-topmost", True)  # 顶层显示
        center_window(self, 400, 320)
        
        self.password = None
        self.login_success = False
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        ctk.CTkLabel(frame, text="🔐", font=("Arial", 45)).pack(pady=10)
        ctk.CTkLabel(frame, text="Account V2", font=("Arial", 22, "bold")).pack()
        ctk.CTkLabel(frame, text="本地密码管理器", text_color="gray").pack()
        
        ctk.CTkLabel(frame, text="主密码:", anchor="w").pack(fill="x", pady=(25, 5))
        self.password_entry = ctk.CTkEntry(frame, show="*", width=280, font=(APP_FONT["family"], APP_FONT["size"]))
        self.password_entry.pack()
        self.password_entry.bind("<Return>", lambda e: self.submit())
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="登录", command=self.submit, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="初始化", command=self.init_db, width=100).pack(side="left", padx=10)
        
        self.error_label = ctk.CTkLabel(frame, text="", text_color="red", font=(APP_FONT["family"], 11))
        self.error_label.pack()
        
        theme_frame = ctk.CTkFrame(frame, fg_color="transparent")
        theme_frame.pack(side="bottom", pady=5)
        self.theme_var = ctk.StringVar(value=APP_THEME)
        ctk.CTkRadioButton(theme_frame, text="🌙 深色", variable=self.theme_var, value="dark", command=self._change_theme).pack(side="left", padx=10)
        ctk.CTkRadioButton(theme_frame, text="☀️ 浅色", variable=self.theme_var, value="light", command=self._change_theme).pack(side="left", padx=10)
        
        self.password_entry.focus()
        self.grab_set()
        
        LoginDialog._instance = self
    
    def _change_theme(self):
        set_theme(self.theme_var.get())
    
    def submit(self):
        password = self.password_entry.get()
        if not password:
            self.error_label.configure(text="⚠️ 请输入密码")
            return
        try:
            result = Auth.login(password)
            if result is None:
                self.error_label.configure(text="❌ 密码错误")
                self.password_entry.delete(0, "end")
                return
            self.password = password
            self.login_success = True
            self.grab_release()
            LoginDialog._instance = None
            self.destroy()
        except Exception as e:
            self.error_label.configure(text=f"❌ 登录失败: {str(e)}")
    
    def init_db(self):
        password = self.password_entry.get()
        if not password or len(password) < 4:
            self.error_label.configure(text="⚠️ 密码至少4位")
            return
        try:
            Auth.initialize(password)
            self.error_label.configure(text="✅ 初始化成功，请重新登录", text_color="green")
        except Exception as e:
            self.error_label.configure(text=f"❌ 初始化失败: {str(e)}")
    
    def destroy(self):
        self.grab_release()
        LoginDialog._instance = None
        super().destroy()


class PasswordGeneratorDialog(ctk.CTkToplevel):
    _instance = None
    
    def __new__(cls, parent):
        if cls._instance is not None:
            cls._instance.focus()
            return cls._instance
        return super().__new__(cls)
    
    def __init__(self, parent):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        super().__init__(parent)
        self.title("密码生成器")
        self.geometry("420x360")
        self.transient(parent)
        self.attributes("-topmost", True)
        center_window(self, 420, 360)
        
        self._setup_ui()
        self._generate()
        
        PasswordGeneratorDialog._instance = self
        self.grab_set()
    
    def _setup_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="🎲 密码生成器", font=(APP_FONT["family"], 16, "bold")).pack(pady=10)
        
        self.password_label = ctk.CTkLabel(frame, text="", font=("Consolas", 15, "bold"), text_color="yellow")
        self.password_label.pack(pady=15)
        
        self.strength_label = ctk.CTkLabel(frame, text="", font=(APP_FONT["family"], 11))
        self.strength_label.pack()
        
        config_frame = ctk.CTkFrame(frame)
        config_frame.pack(pady=15, fill="x")
        
        ctk.CTkLabel(config_frame, text="长度:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.length_slider = ctk.CTkSlider(config_frame, from_=8, to=64, number_of_steps=56, command=self._generate)
        self.length_slider.set(16)
        self.length_slider.grid(row=0, column=1, padx=10)
        self.length_label = ctk.CTkLabel(config_frame, text="16")
        self.length_label.grid(row=0, column=2, padx=10)
        
        self.uppercase_var = ctk.BooleanVar(value=True)
        self.lowercase_var = ctk.BooleanVar(value=True)
        self.digits_var = ctk.BooleanVar(value=True)
        self.special_var = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(config_frame, text="大写 A-Z", variable=self.uppercase_var, command=self._generate).grid(row=1, column=0, padx=10, sticky="w")
        ctk.CTkCheckBox(config_frame, text="小写 a-z", variable=self.lowercase_var, command=self._generate).grid(row=1, column=1, padx=10, sticky="w")
        ctk.CTkCheckBox(config_frame, text="数字 0-9", variable=self.digits_var, command=self._generate).grid(row=2, column=0, padx=10, sticky="w")
        ctk.CTkCheckBox(config_frame, text="特殊 !@#$", variable=self.special_var, command=self._generate).grid(row=2, column=1, padx=10, sticky="w")
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="重新生成", command=self._generate, width=90).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="复制", command=self._copy, width=90).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="关闭", command=self.close, width=90).pack(side="left", padx=5)
    
    def _generate(self, value=None):
        if value:
            self.length_label.configure(text=str(int(value)))
        config = PasswordConfig(
            length=int(self.length_slider.get()),
            use_uppercase=self.uppercase_var.get(),
            use_lowercase=self.lowercase_var.get(),
            use_digits=self.digits_var.get(),
            use_special=self.special_var.get()
        )
        password = PasswordGenerator.generate(config)
        strength = PasswordGenerator.check_strength(password)
        self.password_label.configure(text=password)
        colors = {"WEAK": "red", "FAIR": "orange", "GOOD": "yellow", "STRONG": "green", "VERY_STRONG": "cyan"}
        self.strength_label.configure(text=f"强度: {strength.name} ({strength.value}/5)", text_color=colors.get(strength.name, "white"))
    
    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.password_label.cget("text"))
    
    def close(self):
        self.grab_release()
        PasswordGeneratorDialog._instance = None
        self.destroy()


class SettingsDialog(ctk.CTkToplevel):
    _instance = None
    
    def __new__(cls, parent):
        if cls._instance is not None:
            cls._instance.focus()
            return cls._instance
        return super().__new__(cls)
    
    def __init__(self, parent):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        super().__init__(parent)
        self.title("设置")
        self.geometry("420x360")
        self.transient(parent)
        self.attributes("-topmost", True)
        center_window(self, 420, 360)
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="⚙️ 设置", font=(APP_FONT["family"], 16, "bold")).pack(pady=15)
        
        theme_frame = ctk.CTkFrame(frame)
        theme_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(theme_frame, text="界面主题:", font=(APP_FONT["family"], 12, "bold")).pack(anchor="w", padx=10, pady=10)
        
        self.theme_var = ctk.StringVar(value=APP_THEME)
        theme_options = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_options.pack(padx=10, pady=5)
        ctk.CTkRadioButton(theme_options, text="🌙 深色模式", variable=self.theme_var, value="dark", command=lambda: set_theme("dark")).pack(side="left", padx=15)
        ctk.CTkRadioButton(theme_options, text="☀️ 浅色模式", variable=self.theme_var, value="light", command=lambda: set_theme("light")).pack(side="left", padx=15)
        
        font_frame = ctk.CTkFrame(frame)
        font_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(font_frame, text="界面字体:", font=(APP_FONT["family"], 12, "bold")).pack(anchor="w", padx=10, pady=10)
        
        self.font_var = ctk.StringVar(value=APP_FONT["family"])
        fonts = ["Arial", "微软雅黑", "宋体", "黑体", "Consolas"]
        
        for f in fonts:
            ctk.CTkRadioButton(font_frame, text=f, variable=self.font_var, value=f, command=self._change_font).pack(side="left", padx=8)
        
        ctk.CTkButton(frame, text="关闭", command=self.close, width=100).pack(pady=20)
        
        SettingsDialog._instance = self
        self.grab_set()
    
    def _change_font(self):
        global APP_FONT
        APP_FONT["family"] = self.font_var.get()
    
    def close(self):
        self.grab_release()
        SettingsDialog._instance = None
        self.destroy()


class AboutDialog(ctk.CTkToplevel):
    _instance = None
    
    def __new__(cls, parent):
        if cls._instance is not None:
            cls._instance.focus()
            return cls._instance
        return super().__new__(cls)
    
    def __init__(self, parent):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        super().__init__(parent)
        self.title("关于")
        self.geometry("360x340")
        self.transient(parent)
        self.attributes("-topmost", True)
        center_window(self, 360, 340)
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(frame, text="🔐", font=("Arial", 45)).pack(pady=10)
        ctk.CTkLabel(frame, text="Account V2", font=(APP_FONT["family"], 20, "bold")).pack()
        ctk.CTkLabel(frame, text="本地密码管理器", text_color="gray").pack()
        ctk.CTkLabel(frame, text="版本: 2.0.0", text_color="gray").pack(pady=10)
        
        ttk.Separator(frame).pack(fill="x", pady=10)
        
        features = ["🔐 AES-256-GCM 加密", "💾 本地 SQLite 存储", "📥 CSV/JSON 导入导出", 
                   "🌐 浏览器密码导入", "💾 备份与恢复", "🎲 强密码生成器"]
        for f in features:
            ctk.CTkLabel(frame, text=f, font=(APP_FONT["family"], 11)).pack(pady=2)
        
        ttk.Separator(frame).pack(fill="x", pady=10)
        ctk.CTkLabel(frame, text="© 2026 Account V2\n基于 OpenClaw 框架", text_color="gray", font=(APP_FONT["family"], 10)).pack()
        ctk.CTkButton(frame, text="关闭", command=self.close, width=80).pack(pady=15)
        
        AboutDialog._instance = self
        self.grab_set()
    
    def close(self):
        self.grab_release()
        AboutDialog._instance = None
        self.destroy()


class ImportDialog(ctk.CTkToplevel):
    _instance = None
    
    def __new__(cls, parent, vault):
        if cls._instance is not None:
            cls._instance.focus()
            return cls._instance
        return super().__new__(cls)
    
    def __init__(self, parent, vault):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.vault = vault
        self.total_rows = 0
        self.current_row = 0
        
        super().__init__(parent)
        self.title("导入数据")
        self.geometry("440x320")
        self.transient(parent)
        self.attributes("-topmost", True)
        center_window(self, 440, 320)
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="📥 导入数据", font=(APP_FONT["family"], 16, "bold")).pack(pady=10)
        
        from tkinter import filedialog
        self.path_var = ctk.StringVar()
        
        ctk.CTkLabel(frame, text="选择文件:", font=(APP_FONT["family"], APP_FONT["size"])).pack(anchor="w", pady=(10, 5))
        path_frame = ctk.CTkFrame(frame, fg_color="transparent")
        path_frame.pack(fill="x")
        ctk.CTkEntry(path_frame, textvariable=self.path_var, width=270).pack(side="left", padx=5)
        ctk.CTkButton(path_frame, text="浏览", command=self._browse_file, width=60).pack(side="left")
        
        pwd_frame = ctk.CTkFrame(frame, fg_color="transparent")
        pwd_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(pwd_frame, text="JSON密码(可选):", font=(APP_FONT["family"], APP_FONT["size"])).pack(side="left")
        self.import_pwd = ctk.CTkEntry(pwd_frame, show="*", width=150, font=(APP_FONT["family"], APP_FONT["size"]))
        self.import_pwd.pack(side="left", padx=10)
        
        # 进度条
        self.progress = ctk.CTkProgressBar(frame, width=300)
        self.progress.set(0)
        self.progress.pack(pady=10)
        
        self.progress_label = ctk.CTkLabel(frame, text="", font=(APP_FONT["family"], APP_FONT["size"]))
        self.progress_label.pack()
        
        result_label = ctk.CTkLabel(frame, text="", font=(APP_FONT["family"], APP_FONT["size"]))
        result_label.pack(pady=10)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="执行导入", command=self._do_import, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="关闭", command=self.close, width=100).pack(side="left", padx=10)
        
        self.result_label = result_label
        self._filepath = None
        
        ImportDialog._instance = self
        self.grab_set()
    
    def _browse_file(self):
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            filetypes=[("CSV", "*.csv"), ("JSON", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            self.path_var.set(filename)
            self._filepath = filename
    
    def _do_import(self):
        import os
        from pathlib import Path
        
        filepath = self.path_var.get().strip()
        if not filepath or not os.path.exists(filepath):
            self.result_label.configure(text="⚠️ 请选择有效文件", text_color="orange")
            return
        
        try:
            p = Path(filepath)
            password = self.import_pwd.get().strip() or None
            
            # 先统计行数
            if p.suffix == ".csv":
                with open(p, 'r', encoding='utf-8-sig') as f:
                    lines = sum(1 for _ in f) - 1  # 减去标题行
                self.total_rows = lines
            else:
                self.total_rows = 10
            
            self.current_row = 0
            self.progress.set(0)
            self.progress_label.configure(text=f"准备导入...")
            
            self.update()
            
            if p.suffix == ".csv":
                # CSV 导入
                self.progress_label.configure(text=f"正在导入 CSV...")
                count = ImportExportService.import_csv(self.vault, p)
            else:
                self.progress_label.configure(text=f"正在导入 JSON...")
                count = ImportExportService.import_json(self.vault, p, password)
            
            self.progress.set(1)
            self.progress_label.configure(text=f"导入完成!")
            self.result_label.configure(text=f"✅ 成功导入 {count} 条记录", text_color="green")
            
            # 通知主窗口刷新
            if hasattr(self.master, '_refresh'):
                self.master.after(500, self.master._refresh)
                
        except Exception as e:
            self.result_label.configure(text=f"❌ 失败: {str(e)}", text_color="red")
    
    def close(self):
        self.grab_release()
        ImportDialog._instance = None
        self.destroy()


class ExportDialog(ctk.CTkToplevel):
    _instance = None
    
    def __new__(cls, parent, vault):
        if cls._instance is not None:
            cls._instance.focus()
            return cls._instance
        return super().__new__(cls)
    
    def __init__(self, parent, vault):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.vault = vault
        
        super().__init__(parent)
        self.title("导出数据")
        self.geometry("440x300")
        self.transient(parent)
        self.attributes("-topmost", True)
        center_window(self, 440, 300)
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="📤 导出数据", font=(APP_FONT["family"], 16, "bold")).pack(pady=10)
        
        self.fmt_var = ctk.StringVar(value="csv")
        ctk.CTkRadioButton(frame, text="CSV (明文)", variable=self.fmt_var, value="csv").pack()
        ctk.CTkRadioButton(frame, text="JSON (可选加密)", variable=self.fmt_var, value="json").pack()
        
        from tkinter import filedialog
        self.path_var = ctk.StringVar()
        
        ctk.CTkLabel(frame, text="保存路径:", font=(APP_FONT["family"], APP_FONT["size"])).pack(anchor="w", pady=(15, 5))
        path_frame = ctk.CTkFrame(frame, fg_color="transparent")
        path_frame.pack(fill="x")
        ctk.CTkEntry(path_frame, textvariable=self.path_var, width=270).pack(side="left", padx=5)
        ctk.CTkButton(path_frame, text="浏览", command=self._browse_file, width=60).pack(side="left")
        
        pwd_frame = ctk.CTkFrame(frame, fg_color="transparent")
        pwd_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(pwd_frame, text="加密密码(可选):", font=(APP_FONT["family"], APP_FONT["size"])).pack(side="left")
        self.export_pwd = ctk.CTkEntry(pwd_frame, show="*", width=150, font=(APP_FONT["family"], APP_FONT["size"]))
        self.export_pwd.pack(side="left", padx=10)
        
        result_label = ctk.CTkLabel(frame, text="", font=(APP_FONT["family"], APP_FONT["size"]))
        result_label.pack(pady=10)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="执行导出", command=self._do_export, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="关闭", command=self.close, width=100).pack(side="left", padx=10)
        
        self.result_label = result_label
        
        ExportDialog._instance = self
        self.grab_set()
    
    def _browse_file(self):
        from tkinter import filedialog
        ext = self.fmt_var.get()
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[(ext.upper(), f"*.{ext}")]
        )
        if filename:
            self.path_var.set(filename)
    
    def _do_export(self):
        from pathlib import Path
        
        filepath = self.path_var.get().strip()
        if not filepath:
            self.result_label.configure(text="⚠️ 请选择保存路径", text_color="orange")
            return
        
        try:
            p = Path(filepath)
            password = self.export_pwd.get().strip() or None
            
            if self.fmt_var.get() == "csv":
                count = ImportExportService.export_csv(self.vault, p)
            else:
                count = ImportExportService.export_json(self.vault, p, encrypt=bool(password), password=password)
            
            self.result_label.configure(text=f"✅ 成功导出 {count} 条记录", text_color="green")
        except Exception as e:
            self.result_label.configure(text=f"❌ 失败: {str(e)}", text_color="red")
    
    def close(self):
        self.grab_release()
        ExportDialog._instance = None
        self.destroy()


class BrowserImportDialog(ctk.CTkToplevel):
    _instance = None
    
    def __new__(cls, parent, vault):
        if cls._instance is not None:
            cls._instance.focus()
            return cls._instance
        return super().__new__(cls)
    
    def __init__(self, parent, vault):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.vault = vault
        
        super().__init__(parent)
        self.title("浏览器导入")
        self.geometry("420x320")
        self.transient(parent)
        self.attributes("-topmost", True)
        center_window(self, 420, 320)
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="🌐 浏览器密码导入", font=(APP_FONT["family"], 14, "bold")).pack(pady=10)
        
        self.available = BrowserImportService.get_available_browsers()
        
        if not self.available:
            ctk.CTkLabel(frame, text="未检测到浏览器数据", text_color="gray").pack(pady=30)
        else:
            for b in self.available:
                row = ctk.CTkFrame(frame)
                row.pack(fill="x", pady=3)
                ctk.CTkLabel(row, text=f"📁 {b.upper()}", font=(APP_FONT["family"], 12)).pack(side="left", padx=10)
                ctk.CTkButton(row, text="导入", width=60, command=lambda x=b: self._do_import(x)).pack(side="right", padx=10)
        
        self.result_label = ctk.CTkLabel(frame, text="", font=(APP_FONT["family"], APP_FONT["size"]))
        self.result_label.pack(pady=10)
        
        ctk.CTkButton(frame, text="关闭", command=self.close, width=100).pack(pady=10)
        
        BrowserImportDialog._instance = self
        self.grab_set()
    
    def _do_import(self, browser):
        try:
            passwords = BrowserImportService.import_from_browser(browser, self.vault, auto_add=True)
            self.result_label.configure(text=f"✅ {browser}: 导入 {len(passwords)} 条", text_color="green")
            if hasattr(self.master, '_refresh'):
                self.master._refresh()
        except Exception as e:
            self.result_label.configure(text=f"❌ 失败: {str(e)}", text_color="red")
    
    def close(self):
        self.grab_release()
        BrowserImportDialog._instance = None
        self.destroy()


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Account V2 - 密码管理器")
        self.geometry("940x620")
        center_window(self, 940, 620)
        
        self.vault = None
        self._setup_ui()
        self._login()
    
    def _setup_ui(self):
        toolbar = ctk.CTkFrame(self, height=60)
        toolbar.pack(side="top", fill="x", padx=10, pady=5)
        
        self.search_entry = ctk.CTkEntry(toolbar, placeholder_text="🔍 搜索账号...", width=220)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self._search())
        
        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.pack(side="right", padx=5)
        
        buttons = [
            ("+ 新增", self._add_account),
            ("🎲 生成", lambda: PasswordGeneratorDialog(self)),
            ("📥 导入", lambda: ImportDialog(self, self.vault) if self.vault else None),
            ("📤 导出", lambda: ExportDialog(self, self.vault) if self.vault else None),
            ("🌐 浏览器", lambda: BrowserImportDialog(self, self.vault) if self.vault else None),
            ("⚙️ 设置", lambda: SettingsDialog(self)),
            ("ℹ️", lambda: AboutDialog(self))
        ]
        
        for text, cmd in buttons:
            btn = ctk.CTkButton(btn_frame, text=text, command=cmd, width=72)
            btn.pack(side="left", padx=2)
        
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.list_frame = ctk.CTkScrollableFrame(main, label_text="账号列表")
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        status = ctk.CTkFrame(self, height=30)
        status.pack(side="bottom", fill="x")
        
        self.status_label = ctk.CTkLabel(status, text="未登录", font=(APP_FONT["family"], 10))
        self.status_label.pack(side="left", padx=10)
        ctk.CTkButton(status, text="🔄", width=30, command=self._refresh).pack(side="right", padx=10)
    
    def _login(self):
        if not Auth.is_initialized():
            dlg = LoginDialog(self)
            self.wait_window(dlg)
            if not dlg.login_success:
                self.destroy()
                return
        
        dlg = LoginDialog(self)
        self.wait_window(dlg)
        
        if dlg.password is None or not dlg.login_success:
            self.destroy()
            return
        
        try:
            result = Auth.login(dlg.password)
            if result:
                self.vault = Vault(result[0], result[1])
                self._refresh()
            else:
                self.status_label.configure(text="登录失败")
        except Exception as e:
            self.status_label.configure(text=f"错误: {str(e)}")
    
    def _refresh(self):
        if not self.vault:
            return
        accounts = self.vault.get_all_accounts()
        self._render(accounts)
        self.status_label.configure(text=f"✓ 已登录 | 共 {len(accounts)} 条")
    
    def _search(self):
        if not self.vault:
            return
        keyword = self.search_entry.get().strip()
        accounts = self.vault.search(keyword) if keyword else self.vault.get_all_accounts()
        self._render(accounts)
    
    def _render(self, accounts):
        for w in self.list_frame.winfo_children():
            w.destroy()
        
        if not accounts:
            ctk.CTkLabel(self.list_frame, text="暂无账号，点击上方「+ 新增」添加", text_color="gray", font=(APP_FONT["family"], 13)).pack(pady=30)
            return
        
        for acc in accounts:
            card = ctk.CTkFrame(self.list_frame)
            card.pack(fill="x", pady=2)
            
            fav = "⭐" if acc.favorite else "  "
            ctk.CTkLabel(card, text=f"{fav} {acc.website_name}", font=(APP_FONT["family"], 13, "bold")).pack(side="left", padx=10)
            ctk.CTkLabel(card, text=acc.account, text_color="gray").pack(side="left", padx=10)
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=5)
            
            ctk.CTkButton(btn_frame, text="👁", width=38, command=lambda a=acc: self._show_password(a)).pack(side="left", padx=1)
            ctk.CTkButton(btn_frame, text="⭐", width=38, command=lambda a=acc: self._toggle_favorite(a)).pack(side="left", padx=1)
            ctk.CTkButton(btn_frame, text="🗑", width=38, fg_color="red", command=lambda a=acc: self._delete_account(a)).pack(side="left", padx=1)
    
    def _show_password(self, acc):
        dlg = ctk.CTkToplevel(self)
        dlg.title(acc.website_name)
        dlg.geometry("380x260")
        dlg.transient(self)
        dlg.attributes("-topmost", True)
        center_window(dlg, 380, 260)
        
        frame = ctk.CTkFrame(dlg)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text=acc.website_name, font=(APP_FONT["family"], 16, "bold")).pack(pady=10)
        ctk.CTkLabel(frame, text=f"账号: {acc.account}", font=(APP_FONT["family"], APP_FONT["size"])).pack()
        ctk.CTkLabel(frame, text=f"密码: {acc.password}", text_color="yellow", font=(APP_FONT["family"], APP_FONT["size"])).pack()
        if acc.url:
            ctk.CTkLabel(frame, text=f"网址: {acc.url}", font=(APP_FONT["family"], APP_FONT["size"])).pack()
        if acc.note:
            ctk.CTkLabel(frame, text=f"备注: {acc.note}", font=(APP_FONT["family"], APP_FONT["size"])).pack()
        
        ctk.CTkButton(frame, text="关闭", command=dlg.destroy).pack(pady=15)
    
    def _toggle_favorite(self, acc):
        if self.vault:
            self.vault.update_account(acc.id, favorite=not acc.favorite)
            self._refresh()
    
    def _delete_account(self, acc):
        if self.vault:
            self.vault.delete_account(acc.id)
            self._refresh()
    
    def _add_account(self):
        if not self.vault:
            return
        dlg = ctk.CTkToplevel(self)
        dlg.title("添加账号")
        dlg.geometry("480x420")
        dlg.transient(self)
        dlg.attributes("-topmost", True)
        center_window(dlg, 480, 420)
        
        frame = ctk.CTkFrame(dlg)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        entries = {}
        for i, label in enumerate(["网站名称 *", "账号 *", "密码 *", "网址", "备注"]):
            ctk.CTkLabel(frame, text=label, anchor="w").grid(row=i, column=0, sticky="w", pady=12)
            if label == "备注":
                entries[label] = ctk.CTkTextbox(frame, width=270, height=70)
            elif label == "密码 *":
                pw_frame = ctk.CTkFrame(frame, fg_color="transparent")
                pw_frame.grid(row=i, column=1, pady=12, sticky="w")
                entries[label] = ctk.CTkEntry(pw_frame, show="*", width=200)
                entries[label].pack(side="left")
                ctk.CTkButton(pw_frame, text="🎲", width=38, 
                             command=lambda: entries["密码 *"].delete(0, "end") or 
                             entries["密码 *"].insert(0, PasswordGenerator.generate())).pack(side="left", padx=2)
            else:
                entries[label] = ctk.CTkEntry(frame, width=270)
            entries[label].grid(row=i, column=1, pady=12, padx=15)
        
        
        def save():
            website = entries["网站名称 *"].get().strip()
            account = entries["账号 *"].get().strip()
            password = entries["密码 *"].get()
            url = entries["网址"].get().strip() or None
            note = entries["备注"].get("1.0", "end").strip() or None
            
            if website and account and password and self.vault:
                self.vault.add_account(website, account, password, url, note)
                dlg.destroy()
                self._refresh()
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=15)
        ctk.CTkButton(btn_frame, text="保存", command=save, width=80).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="取消", command=dlg.destroy, width=80).pack(side="left", padx=10)


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
