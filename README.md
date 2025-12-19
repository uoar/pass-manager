# 🔐 SecureVault - 安全密码管理器

一个安全、简洁的本地密码管理器，提供接近 1Password 级别的安全性。

## ✨ 功能特性

- 🔒 **军事级加密**: AES-256-GCM 加密算法
- 🔑 **安全密钥派生**: PBKDF2-HMAC-SHA256，600,000 次迭代
- 💾 **自动备份**: 每次保存前自动备份，保留最近 10 个备份
- ⚡ **原子写入**: 防止意外断电导致数据损坏
- 📋 **剪贴板安全**: 复制后 30 秒自动清除
- ⏰ **自动锁定**: 5 分钟无操作自动锁定
- 🎲 **密码生成器**: 内置安全随机密码生成

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd pass-manager

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python main.py
```

### 3. 首次使用

1. 首次运行会提示创建主密码
2. **重要**: 请牢记主密码，丢失将无法恢复数据！
3. 建议使用 12 位以上的强密码

## 📁 数据存储位置

### 配置文件
应用配置（包括密码库路径）保存在：
```
%APPDATA%\SecureVault\config.json
```
打包成 EXE 后也使用此位置，确保配置不会丢失。

### 密码库文件
默认存储在：
```
C:\Users\<用户名>\Documents\SecureVault\vault.dat
```

**支持自定义路径**：在登录界面点击 📁 按钮可选择其他位置（如 OneDrive 文件夹）。

### 备份文件
备份文件存储在密码库同目录的 `backups` 子文件夹中。

## 🔐 安全设计

### 加密方案

```
主密码
    ↓
PBKDF2-HMAC-SHA256 (600,000 迭代 + 随机盐值)
    ↓
256 位加密密钥
    ↓
AES-256-GCM 加密
    ↓
加密数据 (salt + nonce + ciphertext + auth_tag)
```

### 安全保障

| 威胁 | 防护措施 |
|------|----------|
| 暴力破解 | PBKDF2 600,000 次迭代，大幅增加破解成本 |
| 数据篡改 | GCM 模式提供完整性校验 |
| 内存攻击 | 锁定后立即清除内存中的敏感数据 |
| 剪贴板泄露 | 30 秒后自动清除剪贴板 |
| 数据损坏 | 原子写入 + 自动备份 |

### 与 1Password 对比

| 特性 | SecureVault | 1Password |
|------|-------------|-----------|
| 加密算法 | AES-256-GCM | AES-256-GCM |
| 密钥派生 | PBKDF2 (600K) | PBKDF2 (100K+) |
| 本地存储 | ✅ | ✅ |
| 云同步 | ❌ | ✅ |
| 开源 | ✅ | ❌ |

## 📦 OneDrive 备份

密码库文件可以安全地通过 OneDrive 备份：

1. 将 `vault.dat` 文件复制到 OneDrive 文件夹
2. 或直接将 SecureVault 文件夹移动到 OneDrive

即使文件被盗，没有主密码也无法解密！

## 🛠️ 打包为 EXE

生成独立的 exe 文件，无需安装 Python 即可运行：

### 方法一：使用打包脚本（推荐）

```bash
python build.py
```

### 方法二：使用 spec 文件

```bash
# 安装 PyInstaller
pip install pyinstaller

# 使用配置文件打包
pyinstaller SecureVault.spec
```

### 方法三：命令行打包

```bash
pyinstaller --onefile --windowed --name SecureVault --collect-all customtkinter main.py
```

生成的 `SecureVault.exe` 在 `dist` 文件夹中。

### 打包后使用

1. 将 `SecureVault.exe` 复制到任意位置（可以放在 U 盘随身携带）
2. 双击运行即可
3. 配置会自动保存到 `%APPDATA%\SecureVault\config.json`
4. 首次运行可选择密码库存储位置（建议选择 OneDrive 文件夹）

## ⚠️ 重要提示

1. **牢记主密码**: 主密码是唯一的解密钥匙，无法恢复！
2. **定期备份**: 虽然有自动备份，建议定期将 vault.dat 复制到安全位置
3. **主密码强度**: 建议使用 12 位以上，包含大小写字母、数字和符号

## 🔧 故障排除

### 忘记主密码

**很遗憾，无法恢复**。这是安全设计的一部分。

建议：
- 使用密码提示帮助记忆
- 将主密码写在纸上，存放在安全的地方

### 数据损坏

程序会自动保留最近 10 个备份，位于 `backups` 文件夹。

恢复步骤：
1. 关闭程序
2. 进入 `backups` 文件夹
3. 选择最近的备份文件
4. 将其重命名为 `vault.dat` 并复制到上级目录
5. 重新启动程序

## 📄 许可证

MIT License - 可自由使用和修改
