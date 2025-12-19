"""
SecureVault - 安全密码管理器
主程序入口

安全特性：
- AES-256-GCM 加密
- PBKDF2 密钥派生（600,000 次迭代）
- 自动备份
- 原子写入（防止数据损坏）
- 剪贴板自动清除（30秒）
- 自动锁定（5分钟无操作）
- 支持自定义密码库存储位置
- 单实例运行（防止重复打开）
"""

import os
import sys
import ctypes


# ============ 单实例检测 ============
class SingleInstance:
    """确保只有一个程序实例运行（使用文件锁）"""
    
    def __init__(self):
        self.lockfile = None
        self.already_running = False
        self.lock_path = self._get_lock_path()
        
        try:
            # 尝试以独占方式打开锁文件
            if sys.platform == "win32":
                import msvcrt
                self.lockfile = open(self.lock_path, 'w')
                try:
                    msvcrt.locking(self.lockfile.fileno(), msvcrt.LK_NBLCK, 1)
                except (IOError, OSError):
                    self.already_running = True
                    self.lockfile.close()
                    self.lockfile = None
            else:
                import fcntl
                self.lockfile = open(self.lock_path, 'w')
                try:
                    fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (IOError, OSError):
                    self.already_running = True
                    self.lockfile.close()
                    self.lockfile = None
        except Exception:
            pass
    
    def _get_lock_path(self) -> str:
        """获取锁文件路径"""
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                lock_dir = os.path.join(appdata, "SecureVault")
            else:
                lock_dir = os.path.join(os.environ.get("USERPROFILE", ""), "SecureVault")
        else:
            lock_dir = os.path.join(os.path.expanduser("~"), ".securevault")
        
        if not os.path.exists(lock_dir):
            os.makedirs(lock_dir)
        
        return os.path.join(lock_dir, ".lock")
    
    def is_running(self) -> bool:
        """检查是否已有实例在运行"""
        return self.already_running
    
    def __del__(self):
        """释放文件锁"""
        if self.lockfile:
            try:
                self.lockfile.close()
            except:
                pass


def bring_existing_window_to_front():
    """尝试将已存在的窗口带到前台"""
    try:
        import ctypes
        from ctypes import wintypes
        
        # 查找窗口
        EnumWindows = ctypes.windll.user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        GetWindowText = ctypes.windll.user32.GetWindowTextW
        GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
        SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow
        ShowWindow = ctypes.windll.user32.ShowWindow
        SW_RESTORE = 9
        
        found_hwnd = [None]
        
        def enum_callback(hwnd, lparam):
            length = GetWindowTextLength(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                title = buff.value
                # 查找 SecureVault 窗口
                if "SecureVault" in title or "密码管理器" in title:
                    found_hwnd[0] = hwnd
                    return False  # 停止枚举
            return True
        
        EnumWindows(EnumWindowsProc(enum_callback), 0)
        
        if found_hwnd[0]:
            ShowWindow(found_hwnd[0], SW_RESTORE)
            SetForegroundWindow(found_hwnd[0])
            return True
    except Exception:
        pass
    return False


def get_vault_path() -> str:
    """获取密码库文件路径（从配置中读取）"""
    from i18n import config
    return config.vault_path


def main():
    """主函数"""
    # 单实例检测
    single_instance = SingleInstance()
    if single_instance.is_running():
        print("SecureVault 已经在运行中...")
        # 尝试将已有窗口带到前台
        bring_existing_window_to_front()
        sys.exit(0)
    
    # 检查依赖
    try:
        import customtkinter
        import cryptography
        import pyperclip
    except ImportError as e:
        print("=" * 50)
        print("缺少依赖！请先安装：")
        print("pip install -r requirements.txt")
        print("=" * 50)
        print(f"\n详细错误: {e}")
        input("\n按回车键退出...")
        sys.exit(1)
    
    from password_manager import PasswordManager
    from ui import MainWindow, LoginWindow
    
    # 初始化密码管理器
    vault_path = get_vault_path()
    print(f"密码库位置: {vault_path}")
    
    # 确保密码库目录存在
    vault_dir = os.path.dirname(vault_path)
    if not os.path.exists(vault_dir):
        os.makedirs(vault_dir)
    
    pm = PasswordManager(vault_path)
    
    # 创建隐藏的根窗口
    import customtkinter as ctk
    root = ctk.CTk()
    root.withdraw()  # 隐藏根窗口
    
    # 显示登录窗口
    def on_login_success():
        """登录成功后显示主窗口"""
        root.destroy()
        main_window = MainWindow(pm)
        main_window.mainloop()
    
    login = LoginWindow(root, pm, on_login_success)
    root.mainloop()


if __name__ == "__main__":
    main()
