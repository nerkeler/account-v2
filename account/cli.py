# -*- coding: utf-8 -*-
"""
命令行界面
"""

import typer
import sys
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from typing import Optional
from pathlib import Path

from account.core.keychain import Auth
from account.core.vault import Vault
from account.services.password_generator import PasswordGenerator, PasswordConfig

app = typer.Typer(help="🔐 Account V2 - 本地密码管理器")
console = Console()

# 全局状态
_vault: Optional[Vault] = None


def get_vault() -> Optional[Vault]:
    """获取当前保险库"""
    return _vault


def set_vault(vault: Vault):
    """设置当前保险库"""
    global _vault
    _vault = vault


@app.command()
def init():
    """初始化密码库"""
    if Auth.is_initialized():
        console.print("[yellow]密码库已初始化，请直接登录[/yellow]")
        return
    
    password = typer.prompt("设置主密码", hide_input=True, confirmation_prompt=True)
    
    try:
        Auth.initialize(password)
        console.print("[green]✓ 密码库初始化成功![/green]")
    except Exception as e:
        console.print(f"[red]初始化失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def login(master_password: Optional[str] = None):
    """登录密码库"""
    if not Auth.is_initialized():
        console.print("[yellow]密码库未初始化，请先运行: account init[/yellow]")
        return
    
    if master_password is None:
        master_password = typer.prompt("主密码", hide_input=True)
    
    result = Auth.login(master_password)
    if result is None:
        console.print("[red]密码错误![/red]")
        raise typer.Exit(1)
    
    user_id, encryption_key = result
    vault = Vault(user_id, encryption_key)
    set_vault(vault)
    console.print("[green]✓ 登录成功![/green]")


@app.command()
def add(
    website: str = typer.Option(..., prompt=True, help="网站名称"),
    account: str = typer.Option(..., prompt=True, help="账号"),
    password: str = typer.Option(..., prompt=True, help="密码"),
    url: Optional[str] = typer.Option(None, help="网址"),
    note: Optional[str] = typer.Option(None, help="备注"),
):
    """添加新账号"""
    vault = get_vault()
    if vault is None:
        console.print("[yellow]请先登录: account login[/yellow]")
        raise typer.Exit(1)
    
    try:
        acc = vault.add_account(website, account, password, url, note)
        console.print(f"[green]✓[/green] 已添加账号: {acc.website_name}")
    except Exception as e:
        console.print(f"[red]添加失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list(
    search: Optional[str] = typer.Option(None, help="搜索关键词"),
    favorites: bool = typer.Option(False, help="只显示收藏"),
):
    """列出所有账号"""
    vault = get_vault()
    if vault is None:
        console.print("[yellow]请先登录: account login[/yellow]")
        raise typer.Exit(1)
    
    if search:
        accounts = vault.search(search)
    elif favorites:
        accounts = vault.get_favorites()
    else:
        accounts = vault.get_all_accounts()
    
    if not accounts:
        console.print("[yellow]没有找到账号[/yellow]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("序号", style="dim", width=4)
    table.add_column("网站", style="cyan")
    table.add_column("账号", style="green")
    table.add_column("网址", style="dim")
    
    for i, acc in enumerate(accounts, 1):
        table.add_row(
            str(i),
            "⭐ " + acc.website_name if acc.favorite else acc.website_name,
            acc.account,
            acc.url or '-'
        )
    
    console.print(table)
    console.print(f"\n共 {len(accounts)} 条记录")


@app.command()
def show(
    index: int = typer.Argument(..., help="账号序号"),
):
    """查看账号详情"""
    vault = get_vault()
    if vault is None:
        console.print("[yellow]请先登录: account login[/yellow]")
        raise typer.Exit(1)
    
    accounts = vault.get_all_accounts()
    if index < 1 or index > len(accounts):
        console.print(f"[red]无效的序号 (1-{len(accounts)})[/red]")
        raise typer.Exit(1)
    
    acc = accounts[index - 1]
    
    console.print(f"\n[bold cyan]{acc.website_name}[/bold cyan]")
    console.print(f"[bold]账号:[/bold] {acc.account}")
    console.print(f"[bold]密码:[/bold] [bold yellow]{acc.password}[/bold yellow]")
    console.print(f"[bold]网址:[/bold] {acc.url or '-'}")
    console.print(f"[bold]备注:[/bold] {acc.note or '-'}")
    console.print(f"[bold]收藏:[/bold] {'⭐ 是' if acc.favorite else '否'}")
    console.print(f"[bold]创建:[/bold] {acc.created_at}")


@app.command()
def delete(index: int = typer.Argument(..., help="账号序号")):
    """删除账号"""
    vault = get_vault()
    if vault is None:
        console.print("[yellow]请先登录: account login[/yellow]")
        raise typer.Exit(1)
    
    accounts = vault.get_all_accounts()
    if index < 1 or index > len(accounts):
        console.print(f"[red]无效的序号[/red]")
        raise typer.Exit(1)
    
    acc = accounts[index - 1]
    confirm = typer.confirm(f"确认删除 {acc.website_name}?")
    
    if confirm:
        if vault.delete_account(acc.id):
            console.print("[green]✓ 删除成功[/green]")
        else:
            console.print("[red]删除失败[/red]")


@app.command()
def generate(
    length: int = typer.Option(16, help="密码长度"),
    strong: bool = typer.Option(False, help="包含特殊字符"),
):
    """生成随机密码"""
    config = PasswordConfig(length=length, use_special=strong)
    password = PasswordGenerator.generate(config)
    strength = PasswordGenerator.check_strength(password)
    
    console.print(f"\n[bold]生成的密码:[/bold]")
    console.print(f"[cyan]{password}[/cyan]\n")
    console.print(f"强度: [{PasswordGenerator.get_strength_color(strength)}{strength.name}[/{PasswordGenerator.get_strength_color(strength)}]")


@app.command()
def logout():
    """退出登录"""
    global _vault
    _vault = None
    console.print("[green]✓ 已退出登录[/green]")


@app.command()
def status():
    """查看状态"""
    if Auth.is_initialized():
        console.print(f"[green]✓[/green] 密码库已初始化")
    else:
        console.print(f"[yellow]○[/yellow] 密码库未初始化")
    
    if _vault is not None:
        console.print(f"[green]✓[/green] 已登录 (user_id={_vault.user_id})")
    else:
        console.print(f"[yellow]○[/yellow] 未登录")


# ========== 导入导出命令 ==========

@app.command()
def export_csv(
    filepath: str = typer.Argument(..., help="导出文件路径"),
    include_passwords: bool = typer.Option(True, help="包含密码"),
):
    """导出为 CSV 文件"""
    vault = get_vault()
    if vault is None:
        console.print("[yellow]请先登录[/yellow]")
        raise typer.Exit(1)
    
    from account.services.import_export import ImportExportService
    
    count = ImportExportService.export_csv(vault, Path(filepath), include_passwords)
    console.print(f"[green]✓[/green] 成功导出 {count} 条记录到 {filepath}")


@app.command()
def import_csv(
    filepath: str = typer.Argument(..., help="CSV 文件路径"),
):
    """从 CSV 文件导入"""
    vault = get_vault()
    if vault is None:
        console.print("[yellow]请先登录[/yellow]")
        raise typer.Exit(1)
    
    from account.services.import_export import ImportExportService
    
    count = ImportExportService.import_csv(vault, Path(filepath))
    console.print(f"[green]✓[/green] 成功导入 {count} 条记录")


# ========== 备份命令 ==========

@app.command()
def backup(
    name: str = typer.Option(None, help="备份名称"),
    compress: bool = typer.Option(True, help="是否压缩"),
):
    """备份保险库"""
    from account.services.backup import BackupService
    
    service = BackupService()
    path = service.create_backup(name, compress)
    console.print(f"[green]✓[/green] 备份已创建: {path}")


@app.command()
def list_backups():
    """列出所有备份"""
    from account.services.backup import BackupService
    
    service = BackupService()
    backups = service.list_backups()
    
    if not backups:
        console.print("[yellow]暂无备份[/yellow]")
        return
    
    table = Table(show_header=True)
    table.add_column("名称")
    table.add_column("大小", style="dim")
    table.add_column("创建时间")
    
    for b in backups:
        size_mb = b["size"] / 1024 / 1024
        table.add_row(b["name"], f"{size_mb:.1f} MB", b["created"][:16])
    
    console.print(table)


@app.command()
def restore_backup(name: str):
    """恢复备份"""
    from account.services.backup import BackupService
    
    service = BackupService()
    if service.restore_backup(name):
        console.print(f"[green]✓[/green] 备份已恢复，请重新登录")
    else:
        console.print(f"[red]恢复失败[/red]")


# ========== 浏览器导入命令 ==========

@app.command()
def import_browser(
    browser: str = typer.Option(..., help="浏览器名称: chrome, edge, firefox, brave"),
    auto_add: bool = typer.Option(True, help="自动添加到保险库"),
):
    """从浏览器导入密码"""
    vault = get_vault()
    if vault is None:
        console.print("[yellow]请先登录[/yellow]")
        raise typer.Exit(1)
    
    from account.services.browser_import import BrowserImportService
    
    passwords = BrowserImportService.import_from_browser(browser, vault, auto_add)
    console.print(f"[green]✓[/green] 从 {browser} 找到 {len(passwords)} 条密码记录")


@app.command()
def list_browsers():
    """列出可用的浏览器"""
    from account.services.browser_import import BrowserImportService
    
    available = BrowserImportService.get_available_browsers()
    console.print(f"可用浏览器: {', '.join(available) if available else '无'}")


def main():
    """主入口"""
    app()


if __name__ == "__main__":
    main()
