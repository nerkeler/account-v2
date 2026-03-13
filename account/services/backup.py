# -*- coding: utf-8 -*-
"""
数据备份服务
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import hashlib


class BackupService:
    """备份服务"""
    
    def __init__(self, backup_dir: str = None):
        """初始化备份服务
        
        Args:
            backup_dir: 备份目录路径，默认 ~/.account-v2/backups
        """
        if backup_dir is None:
            backup_dir = Path.home() / ".account-v2" / "backups"
        
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据目录
        self.data_dir = Path.home() / ".account-v2"
    
    def create_backup(self, name: str = None, compress: bool = True) -> Path:
        """创建备份
        
        Args:
            name: 备份名称，默认使用时间戳
            compress: 是否压缩
        
        Returns:
            备份文件路径
        """
        if name is None:
            name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_name = f"account-v2_{name}"
        if compress:
            backup_name += ".tar.gz"
        
        backup_path = self.backup_dir / backup_name
        
        # 创建临时备份目录
        temp_dir = self.backup_dir / f"temp_{name}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # 复制数据文件
            for file in ["vault.db", "auth.json"]:
                src = self.data_dir / file
                if src.exists():
                    shutil.copy2(src, temp_dir / file)
            
            # 写入备份元信息
            meta = {
                "version": "2.0.0",
                "created_at": datetime.now().isoformat(),
                "name": name,
                "files": [f.name for f in temp_dir.iterdir() if f.is_file()]
            }
            with open(temp_dir / "backup_meta.json", "w") as f:
                json.dump(meta, f, indent=2)
            
            # 压缩
            if compress:
                shutil.make_archive(str(self.backup_dir / f"account-v2_{name}"), 'gztar', temp_dir)
                shutil.rmtree(temp_dir)
                return backup_path
            else:
                return temp_dir
        
        except Exception as e:
            # 清理临时目录
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise e
    
    def list_backups(self) -> List[dict]:
        """列出所有备份
        
        Returns:
            备份信息列表
        """
        backups = []
        
        for f in sorted(self.backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file() and f.suffix in ['.tar.gz', '.gz']:
                stat = f.stat()
                backups.append({
                    "name": f.stem.replace("account-v2_", ""),
                    "path": str(f),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": "compressed"
                })
            elif f.is_dir() and f.name.startswith("account-v2_"):
                stat = f.stat()
                backups.append({
                    "name": f.name.replace("account-v2_", ""),
                    "path": str(f),
                    "size": sum(p.stat().st_size for p in f.rglob("*") if p.is_file()),
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": "directory"
                })
        
        return backups
    
    def restore_backup(self, name: str, target_dir: str = None) -> bool:
        """恢复备份
        
        Args:
            name: 备份名称
            target_dir: 目标目录，默认恢复原位置
        
        Returns:
            是否成功
        """
        if target_dir is None:
            target_dir = self.data_dir
        
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 查找备份
        backup_path = None
        for f in self.backup_dir.iterdir():
            if name in f.name and (f.is_file() or f.is_dir()):
                backup_path = f
                break
        
        if not backup_path:
            raise FileNotFoundError(f"找不到备份: {name}")
        
        try:
            if backup_path.is_file() and backup_path.suffix == ".gz":
                # 解压
                import tarfile
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(target_dir)
            else:
                # 复制
                for f in backup_path.iterdir():
                    if f.is_file() and f.name != "backup_meta.json":
                        shutil.copy2(f, target_dir / f.name)
            
            return True
        
        except Exception as e:
            print(f"恢复失败: {e}")
            return False
    
    def delete_backup(self, name: str) -> bool:
        """删除备份
        
        Args:
            name: 备份名称
        
        Returns:
            是否成功
        """
        for f in self.backup_dir.iterdir():
            if name in f.name:
                try:
                    if f.is_file():
                        f.unlink()
                    else:
                        shutil.rmtree(f)
                    return True
                except Exception as e:
                    print(f"删除失败: {e}")
                    return False
        
        return False
    
    def export_to_cloud(self, cloud_config: dict) -> bool:
        """导出到云盘 (需要 rclone 配置)
        
        Args:
            cloud_config: 云盘配置 {remote: str, path: str}
        
        Returns:
            是否成功
        """
        try:
            # 创建本地备份
            backup_path = self.create_backup()
            
            # 检查 rclone 是否可用
            result = os.system("which rclone > /dev/null 2>&1")
            if result != 0:
                print("rclone 未安装，跳过云同步")
                return False
            
            # 同步到云盘
            remote = cloud_config.get("remote", "cloud")
            path = cloud_config.get("path", "account-v2-backups")
            
            cmd = f'rclone copy "{backup_path}" "{remote}:{path}" --progress'
            result = os.system(cmd)
            
            return result == 0
        
        except Exception as e:
            print(f"云同步失败: {e}")
            return False
    
    def auto_backup(self, max_backups: int = 7) -> Optional[Path]:
        """自动备份（保留最近 N 个）
        
        Args:
            max_backups: 最大保留备份数
        
        Returns:
            备份路径
        """
        # 创建新备份
        backup_path = self.create_backup()
        
        # 清理旧备份
        backups = self.list_backups()
        if len(backups) > max_backups:
            for old in backups[max_backups:]:
                self.delete_backup(old["name"])
        
        return backup_path


# CLI 命令扩展
def add_backup_commands(app):
    """添加备份命令到 CLI"""
    from account.cli import console
    import typer
    
    @app.command()
    def backup(
        name: str = typer.Option(None, help="备份名称"),
        compress: bool = typer.Option(True, help="是否压缩"),
    ):
        """备份保险库"""
        from account.cli import get_vault
        vault = get_vault()
        
        service = BackupService()
        path = service.create_backup(name, compress)
        
        console.print(f"[green]✓[/green] 备份已创建: {path}")
    
    @app.command()
    def restore(name: str):
        """恢复备份"""
        service = BackupService()
        
        if service.restore_backup(name):
            console.print(f"[green]✓[/green] 备份已恢复")
        else:
            console.print(f"[red]恢复失败[/red]")
    
    @app.command()
    def list_backups():
        """列出所有备份"""
        service = BackupService()
        backups = service.list_backups()
        
        if not backups:
            console.print("[yellow]暂无备份[/yellow]")
            return
        
        from rich.table import Table
        table = Table(show_header=True)
        table.add_column("名称")
        table.add_column("大小", style="dim")
        table.add_column("创建时间")
        
        for b in backups:
            size_mb = b["size"] / 1024 / 1024
            table.add_row(b["name"], f"{size_mb:.1f} MB", b["created"][:16])
        
        console.print(table)


# 测试
if __name__ == "__main__":
    service = BackupService()
    
    # 创建备份
    print("创建备份...")
    path = service.create_backup("test")
    print(f"备份路径: {path}")
    
    # 列出备份
    print("\n列出备份...")
    backups = service.list_backups()
    for b in backups:
        print(f"  - {b['name']}: {b['size']/1024:.1f} KB")
    
    # 自动备份
    print("\n自动备份测试...")
    path = service.auto_backup(max_backups=3)
    print(f"自动备份: {path}")
    
    print("\n✓ 备份服务测试通过!")
