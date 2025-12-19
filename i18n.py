"""
多语言支持模块 & 配置管理
支持中文和英文
"""

import os
import json
from typing import Dict, Optional

# 支持的语言
SUPPORTED_LANGUAGES = ["zh", "en"]
DEFAULT_LANGUAGE = "zh"

# 配置文件路径 - 使用 AppData 目录，打包后也能正常工作
def get_config_dir() -> str:
    """获取配置目录路径（使用 AppData，打包成exe后也能正常工作）"""
    import sys
    if sys.platform == "win32":
        # 使用 %APPDATA%/SecureVault，这是标准的应用配置位置
        # 打包成 exe 后也能正确访问
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            base_dir = os.path.join(appdata, "SecureVault")
        else:
            base_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "SecureVault")
    else:
        base_dir = os.path.join(os.path.expanduser("~"), ".securevault")
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    return base_dir


def get_config_path() -> str:
    """获取配置文件路径"""
    return os.path.join(get_config_dir(), "config.json")


# 翻译字典
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ==================== 应用标题 ====================
    "app_title": {
        "zh": "🔐 SecureVault - 密码管理器",
        "en": "🔐 SecureVault - Password Manager"
    },
    "app_name": {
        "zh": "🔐 SecureVault",
        "en": "🔐 SecureVault"
    },
    "login_title": {
        "zh": "🔐 密码管理器",
        "en": "🔐 Password Manager"
    },
    
    # ==================== 登录窗口 ====================
    "unlock_subtitle": {
        "zh": "输入主密码解锁",
        "en": "Enter master password to unlock"
    },
    "create_vault_subtitle": {
        "zh": "创建新的密码库",
        "en": "Create a new vault"
    },
    "master_password": {
        "zh": "主密码",
        "en": "Master Password"
    },
    "confirm_password": {
        "zh": "确认主密码",
        "en": "Confirm Password"
    },
    "unlock_btn": {
        "zh": "解锁",
        "en": "Unlock"
    },
    "create_vault_btn": {
        "zh": "创建密码库",
        "en": "Create Vault"
    },
    "password_warning": {
        "zh": "⚠️ 请牢记主密码，丢失将无法恢复数据！",
        "en": "⚠️ Remember your master password! Data cannot be recovered if lost!"
    },
    
    # ==================== 错误提示 ====================
    "error": {
        "zh": "错误",
        "en": "Error"
    },
    "error_enter_password": {
        "zh": "请输入主密码",
        "en": "Please enter the master password"
    },
    "error_wrong_password": {
        "zh": "密码错误！",
        "en": "Wrong password!"
    },
    "error_password_min_length": {
        "zh": "密码长度至少为8个字符",
        "en": "Password must be at least 8 characters"
    },
    "error_password_mismatch": {
        "zh": "两次输入的密码不一致",
        "en": "Passwords do not match"
    },
    "error_create_failed": {
        "zh": "创建失败",
        "en": "Creation failed"
    },
    "error_enter_title": {
        "zh": "请输入名称",
        "en": "Please enter a title"
    },
    "error_enter_username": {
        "zh": "请输入用户名",
        "en": "Please enter a username"
    },
    "error_enter_password_field": {
        "zh": "请输入密码",
        "en": "Please enter a password"
    },
    
    # ==================== 主窗口 ====================
    "search_placeholder": {
        "zh": "🔍 搜索...",
        "en": "🔍 Search..."
    },
    "add_btn": {
        "zh": "➕ 添加",
        "en": "➕ Add"
    },
    "generate_password_btn": {
        "zh": "🎲 生成密码",
        "en": "🎲 Generate"
    },
    "lock_btn": {
        "zh": "🔒 锁定",
        "en": "🔒 Lock"
    },
    "edit_btn": {
        "zh": "编辑",
        "en": "Edit"
    },
    "delete_btn": {
        "zh": "删除",
        "en": "Delete"
    },
    "total_records": {
        "zh": "共 {count} 条记录",
        "en": "{count} records"
    },
    "no_records": {
        "zh": "暂无密码记录\n点击「添加」创建第一条",
        "en": "No passwords yet\nClick \"Add\" to create one"
    },
    "select_entry_hint": {
        "zh": "选择一个密码条目查看详情",
        "en": "Select an entry to view details"
    },
    "copied_hint": {
        "zh": "✓ 已复制（30秒后清除）",
        "en": "✓ Copied (clears in 30s)"
    },
    
    # ==================== 密码条目字段 ====================
    "field_username": {
        "zh": "用户名",
        "en": "Username"
    },
    "field_password": {
        "zh": "密码",
        "en": "Password"
    },
    "field_url": {
        "zh": "网址",
        "en": "URL"
    },
    "field_category": {
        "zh": "分类",
        "en": "Category"
    },
    "field_notes": {
        "zh": "备注",
        "en": "Notes"
    },
    "field_created_at": {
        "zh": "创建时间",
        "en": "Created"
    },
    "field_updated_at": {
        "zh": "更新时间",
        "en": "Updated"
    },
    
    # ==================== 添加/编辑对话框 ====================
    "add_password_title": {
        "zh": "添加密码",
        "en": "Add Password"
    },
    "edit_password_title": {
        "zh": "编辑密码",
        "en": "Edit Password"
    },
    "field_title_label": {
        "zh": "名称 *",
        "en": "Title *"
    },
    "field_title_placeholder": {
        "zh": "例如：GitHub",
        "en": "e.g. GitHub"
    },
    "field_username_label": {
        "zh": "用户名",
        "en": "Username"
    },
    "field_username_placeholder": {
        "zh": "用户名或邮箱",
        "en": "Username or email"
    },
    "field_password_label": {
        "zh": "密码 *",
        "en": "Password *"
    },
    "field_url_label": {
        "zh": "网址",
        "en": "URL"
    },
    "field_url_placeholder": {
        "zh": "https://example.com",
        "en": "https://example.com"
    },
    "field_category_label": {
        "zh": "分类",
        "en": "Category"
    },
    "field_category_placeholder": {
        "zh": "默认",
        "en": "Default"
    },
    "field_notes_label": {
        "zh": "备注",
        "en": "Notes"
    },
    "field_notes_placeholder": {
        "zh": "可选备注信息",
        "en": "Optional notes"
    },
    "cancel_btn": {
        "zh": "取消",
        "en": "Cancel"
    },
    "save_btn": {
        "zh": "保存",
        "en": "Save"
    },
    "default_category": {
        "zh": "默认",
        "en": "Default"
    },
    
    # ==================== 删除确认 ====================
    "confirm_delete_title": {
        "zh": "确认删除",
        "en": "Confirm Delete"
    },
    "confirm_delete_message": {
        "zh": "确定要删除「{title}」吗？\n\n此操作不可撤销！",
        "en": "Are you sure you want to delete \"{title}\"?\n\nThis action cannot be undone!"
    },
    
    # ==================== 密码生成器 ====================
    "generator_title": {
        "zh": "密码生成器",
        "en": "Password Generator"
    },
    "length_label": {
        "zh": "长度:",
        "en": "Length:"
    },
    "uppercase_option": {
        "zh": "大写字母 (A-Z)",
        "en": "Uppercase (A-Z)"
    },
    "lowercase_option": {
        "zh": "小写字母 (a-z)",
        "en": "Lowercase (a-z)"
    },
    "digits_option": {
        "zh": "数字 (0-9)",
        "en": "Digits (0-9)"
    },
    "symbols_option": {
        "zh": "特殊符号 (!@#$...)",
        "en": "Symbols (!@#$...)"
    },
    "regenerate_btn": {
        "zh": "🎲 重新生成",
        "en": "🎲 Regenerate"
    },
    "copied_title": {
        "zh": "已复制",
        "en": "Copied"
    },
    "copied_message": {
        "zh": "密码已复制到剪贴板（30秒后自动清除）",
        "en": "Password copied to clipboard (auto-clears in 30s)"
    },
    
    # ==================== 语言设置 ====================
    "language_label": {
        "zh": "🌐",
        "en": "🌐"
    },
    "language_zh": {
        "zh": "中文",
        "en": "Chinese"
    },
    "language_en": {
        "zh": "English",
        "en": "English"
    },
    
    # ==================== 密码库路径设置 ====================
    "vault_location": {
        "zh": "密码库位置",
        "en": "Vault Location"
    },
    "change_vault_path": {
        "zh": "📁 更改位置",
        "en": "📁 Change Location"
    },
    "select_vault_folder": {
        "zh": "选择密码库存储文件夹",
        "en": "Select vault storage folder"
    },
    "vault_path_changed": {
        "zh": "密码库位置已更改，请重启应用",
        "en": "Vault location changed, please restart the app"
    },
    "current_vault_path": {
        "zh": "当前位置：{path}",
        "en": "Current: {path}"
    },
    "no_vault_found": {
        "zh": "在此位置未找到密码库，是否创建新的？",
        "en": "No vault found at this location, create a new one?"
    },
    "vault_found": {
        "zh": "发现已有密码库，是否使用？",
        "en": "Existing vault found, use it?"
    },
    "create_new_vault": {
        "zh": "创建新密码库",
        "en": "Create New Vault"
    },
    "open_existing_vault": {
        "zh": "打开已有密码库",
        "en": "Open Existing Vault"
    },
    "vault_status_exists": {
        "zh": "检测到已有密码库",
        "en": "Existing vault detected"
    },
    "vault_status_new": {
        "zh": "将在此创建新密码库",
        "en": "New vault will be created here"
    },
    "change_btn": {
        "zh": "更改",
        "en": "Change"
    },
    "vault_found_switching": {
        "zh": "已切换到此密码库",
        "en": "Switched to this vault"
    },
    "vault_new_location": {
        "zh": "已设为新的密码库位置",
        "en": "Set as new vault location"
    },
    
    # ==================== Tooltip 提示 ====================
    "tooltip_show_password": {
        "zh": "显示/隐藏密码",
        "en": "Show/Hide password"
    },
    "tooltip_generate_password": {
        "zh": "生成随机密码",
        "en": "Generate random password"
    },
    "tooltip_copy": {
        "zh": "复制到剪贴板",
        "en": "Copy to clipboard"
    },
    "tooltip_change_vault": {
        "zh": "更改密码库位置",
        "en": "Change vault location"
    },
    "tooltip_add": {
        "zh": "添加新密码",
        "en": "Add new password"
    },
    "tooltip_lock": {
        "zh": "锁定密码库",
        "en": "Lock vault"
    },
    "tooltip_edit": {
        "zh": "编辑",
        "en": "Edit"
    },
    "tooltip_delete": {
        "zh": "删除",
        "en": "Delete"
    },
}


# ==================== 配置管理类 ====================
class Config:
    """配置管理类 - 管理密码库路径等设置"""
    
    _instance: Optional['Config'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._vault_path = None
            cls._instance._load_config()
        return cls._instance
    
    def _get_default_vault_dir(self) -> str:
        """获取默认密码库目录"""
        import sys
        if sys.platform == "win32":
            return os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "SecureVault")
        else:
            return os.path.join(os.path.expanduser("~"), ".securevault")
    
    def _load_config(self):
        """加载配置"""
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self._vault_path = config.get('vault_path')
            except:
                pass
        
        # 如果没有配置，使用默认路径
        if not self._vault_path:
            self._vault_path = os.path.join(self._get_default_vault_dir(), "vault.dat")
    
    def _save_config(self):
        """保存配置"""
        config_path = get_config_path()
        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                pass
        
        config['vault_path'] = self._vault_path
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    @property
    def vault_path(self) -> str:
        """获取密码库文件路径"""
        return self._vault_path
    
    @vault_path.setter
    def vault_path(self, value: str):
        """设置密码库文件路径"""
        self._vault_path = value
        self._save_config()
    
    def get_vault_dir(self) -> str:
        """获取密码库所在目录"""
        return os.path.dirname(self._vault_path)
    
    def set_vault_dir(self, dir_path: str):
        """设置密码库目录（自动添加 vault.dat 文件名）"""
        # 确保目录存在
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        self.vault_path = os.path.join(dir_path, "vault.dat")


# 全局配置实例
config = Config()


class I18n:
    """国际化类"""
    
    _instance: Optional['I18n'] = None
    _language: str = DEFAULT_LANGUAGE
    _observers: list = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_language()
        return cls._instance
    
    def _load_language(self):
        """从配置文件加载语言设置"""
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    lang = config.get('language', DEFAULT_LANGUAGE)
                    if lang in SUPPORTED_LANGUAGES:
                        self._language = lang
            except:
                pass
    
    def _save_language(self):
        """保存语言设置到配置文件"""
        config_path = get_config_path()
        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                pass
        
        config['language'] = self._language
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    @property
    def language(self) -> str:
        return self._language
    
    @language.setter
    def language(self, value: str):
        if value in SUPPORTED_LANGUAGES and value != self._language:
            self._language = value
            self._save_language()
            self._notify_observers()
    
    def get(self, key: str, **kwargs) -> str:
        """获取翻译文本"""
        if key not in TRANSLATIONS:
            return key
        
        text = TRANSLATIONS[key].get(self._language, TRANSLATIONS[key].get(DEFAULT_LANGUAGE, key))
        
        # 支持参数替换
        if kwargs:
            for k, v in kwargs.items():
                text = text.replace(f"{{{k}}}", str(v))
        
        return text
    
    def add_observer(self, callback):
        """添加语言变更观察者"""
        if callback not in self._observers:
            self._observers.append(callback)
    
    def remove_observer(self, callback):
        """移除观察者"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self):
        """通知所有观察者语言已变更"""
        for callback in self._observers:
            try:
                callback()
            except:
                pass
    
    def toggle_language(self):
        """切换语言"""
        if self._language == "zh":
            self.language = "en"
        else:
            self.language = "zh"


# 全局实例
i18n = I18n()


def t(key: str, **kwargs) -> str:
    """翻译函数的快捷方式"""
    return i18n.get(key, **kwargs)
