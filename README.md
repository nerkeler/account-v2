# account-v2 本地密码管理器

一个安全的本地密码管理器，支持 CLI 和 GUI 界面，数据加密存储在本地。

## 功能特性

- 🔐 **安全加密** - AES-256-GCM 加密，密钥存储在系统 Keychain
- 🖥️ **双界面** - CLI 命令行 + Tkinter GUI 图形界面
- 🌐 **浏览器导入** - 支持从浏览器导入账号
- 📦 **导入/导出** - 支持 JSON 格式导入导出
- 💾 **本地存储** - SQLite 数据库，本地加密存储
- 🔑 **密码生成** - 内置强密码生成器
- ⏰ **自动备份** - 支持定时自动备份

## 环境要求

- Python 3.10+
- SQLite3

## 安装

```bash
# 克隆仓库
git clone https://github.com/nerkeler/account-v2.git
cd account-v2

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### GUI 界面

```bash
python -m account.gui
# 或
python account/gui.py
```

### CLI 命令行

```bash
# 查看帮助
python -m account.cli --help

# 添加账号
python -m account.cli add --service github --username myuser

# 列出所有账号
python -m account.cli list

# 查询账号
python -m account.cli get github

# 删除账号
python -m account.cli delete github

# 导出数据
python -m account.cli export --file backup.json

# 导入数据
python -m account.cli import --file backup.json
```

## 项目结构

```
account-v2/
├── account/
│   ├── core/           # 核心加密模块
│   │   ├── crypto.py   # 加密解密
│   │   ├── keychain.py # 系统密钥链
│   │   └── vault.py    # 保险库
│   ├── db/             # 数据库
│   │   └── database.py
│   ├── models/         # 数据模型
│   ├── services/       # 服务模块
│   │   ├── backup.py          # 备份
│   │   ├── browser_import.py  # 浏览器导入
│   │   ├── import_export.py   # 导入导出
│   │   └── password_generator.py
│   ├── ui/             # UI 组件
│   ├── utils/          # 工具函数
│   ├── cli.py          # CLI 入口
│   └── gui.py          # GUI 入口
├── scripts/            # 脚本
├── tests/              # 测试
└── requirements.txt    # 依赖
```

## 安全说明

- 主密码不会存储，只用于解锁密钥
- 加密密钥存储在系统 Keychain（Linux: Secret Service API）
- 所有数据本地存储，不上传云端
- 建议定期导出备份

## 技术栈

- Python 3.10+
- SQLite3
- cryptography (AES-256-GCM)
- keyring (系统密钥链)
- Tkinter (GUI)

## License

MIT License
