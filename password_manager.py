"""
密码管理器核心逻辑
提供密码的增删改查、安全存储功能
特别注意：实现了多重防数据丢失保护
"""

import os
import json
import shutil
import time
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from crypto_utils import encrypt_data, decrypt_data, CryptoError, compute_file_checksum


@dataclass
class PasswordEntry:
    """密码条目"""
    id: str
    title: str              # 网站/应用名称
    username: str           # 用户名
    password: str           # 密码
    url: str = ""           # 网址
    notes: str = ""         # 备注
    category: str = "默认"  # 分类
    created_at: str = ""    # 创建时间
    updated_at: str = ""    # 更新时间
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class PasswordManager:
    """
    密码管理器核心类
    
    安全特性：
    1. AES-256-GCM 加密
    2. PBKDF2 密钥派生（600000次迭代）
    3. 保存前自动备份
    4. 原子写入（先写临时文件，成功后再替换）
    5. 数据完整性校验
    """
    
    # 文件版本号，用于未来升级兼容
    VERSION = "1.0"
    
    def __init__(self, vault_path: str):
        """
        初始化密码管理器
        
        Args:
            vault_path: 加密数据文件路径
        """
        self.vault_path = vault_path
        self.backup_dir = os.path.join(os.path.dirname(vault_path), "backups")
        self.master_password: Optional[str] = None
        self.entries: Dict[str, PasswordEntry] = {}
        self.is_unlocked = False
        self._last_save_checksum: Optional[str] = None
        
    def _ensure_backup_dir(self):
        """确保备份目录存在"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def vault_exists(self) -> bool:
        """检查密码库是否已存在"""
        return os.path.exists(self.vault_path)
    
    def create_vault(self, master_password: str) -> bool:
        """
        创建新的密码库
        
        Args:
            master_password: 主密码
            
        Returns:
            是否成功创建
        """
        if len(master_password) < 8:
            raise ValueError("主密码长度至少为8个字符")
        
        self.master_password = master_password
        self.entries = {}
        self.is_unlocked = True
        
        # 保存空的密码库
        return self._save_vault()
    
    def unlock(self, master_password: str) -> bool:
        """
        解锁密码库
        
        Args:
            master_password: 主密码
            
        Returns:
            是否成功解锁
        """
        if not self.vault_exists():
            raise FileNotFoundError("密码库不存在")
        
        try:
            with open(self.vault_path, 'rb') as f:
                encrypted_data = f.read()
            
            data = decrypt_data(encrypted_data, master_password)
            
            # 验证数据版本
            version = data.get('version', '1.0')
            
            # 加载密码条目
            self.entries = {}
            for entry_data in data.get('entries', []):
                entry = PasswordEntry(**entry_data)
                self.entries[entry.id] = entry
            
            self.master_password = master_password
            self.is_unlocked = True
            self._last_save_checksum = compute_file_checksum(self.vault_path)
            
            return True
            
        except CryptoError:
            return False
    
    def lock(self):
        """锁定密码库，清除内存中的敏感数据"""
        self.master_password = None
        self.entries = {}
        self.is_unlocked = False
    
    def _save_vault(self) -> bool:
        """
        安全保存密码库
        
        实现原子写入：
        1. 先保存到临时文件
        2. 验证临时文件可以正确解密
        3. 备份当前文件
        4. 用临时文件替换当前文件
        """
        if not self.is_unlocked or not self.master_password:
            raise RuntimeError("密码库未解锁")
        
        # 准备数据
        data = {
            'version': self.VERSION,
            'updated_at': datetime.now().isoformat(),
            'entries': [asdict(entry) for entry in self.entries.values()]
        }
        
        # 加密数据
        encrypted_data = encrypt_data(data, self.master_password)
        
        # 临时文件路径
        temp_path = self.vault_path + '.tmp'
        
        try:
            # 1. 写入临时文件
            with open(temp_path, 'wb') as f:
                f.write(encrypted_data)
            
            # 2. 验证临时文件可以正确解密（关键安全检查！）
            with open(temp_path, 'rb') as f:
                verify_data = f.read()
            
            decrypted = decrypt_data(verify_data, self.master_password)
            if len(decrypted.get('entries', [])) != len(self.entries):
                raise CryptoError("数据验证失败：条目数量不匹配")
            
            # 3. 如果当前文件存在，创建备份
            if os.path.exists(self.vault_path):
                self._create_backup()
            
            # 4. 原子替换：将临时文件移动为正式文件
            if os.path.exists(self.vault_path):
                os.remove(self.vault_path)
            shutil.move(temp_path, self.vault_path)
            
            # 更新校验和
            self._last_save_checksum = compute_file_checksum(self.vault_path)
            
            return True
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise RuntimeError(f"保存失败: {str(e)}")
    
    def _create_backup(self):
        """创建备份文件"""
        self._ensure_backup_dir()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"vault_backup_{timestamp}.dat")
        
        shutil.copy2(self.vault_path, backup_path)
        
        # 只保留最近 10 个备份
        self._cleanup_old_backups(keep=10)
    
    def _cleanup_old_backups(self, keep: int = 10):
        """清理旧备份，只保留最近的几个"""
        if not os.path.exists(self.backup_dir):
            return
        
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.startswith("vault_backup_") and filename.endswith(".dat"):
                filepath = os.path.join(self.backup_dir, filename)
                backups.append((filepath, os.path.getmtime(filepath)))
        
        # 按修改时间排序，删除旧的
        backups.sort(key=lambda x: x[1], reverse=True)
        
        for filepath, _ in backups[keep:]:
            os.remove(filepath)
    
    def add_entry(self, title: str, username: str, password: str,
                  url: str = "", notes: str = "", category: str = "默认") -> PasswordEntry:
        """添加密码条目"""
        if not self.is_unlocked:
            raise RuntimeError("密码库未解锁")
        
        import uuid
        entry = PasswordEntry(
            id=str(uuid.uuid4()),
            title=title,
            username=username,
            password=password,
            url=url,
            notes=notes,
            category=category
        )
        
        self.entries[entry.id] = entry
        self._save_vault()
        
        return entry
    
    def update_entry(self, entry_id: str, **kwargs) -> PasswordEntry:
        """更新密码条目"""
        if not self.is_unlocked:
            raise RuntimeError("密码库未解锁")
        
        if entry_id not in self.entries:
            raise KeyError(f"条目不存在: {entry_id}")
        
        entry = self.entries[entry_id]
        
        for key, value in kwargs.items():
            if hasattr(entry, key) and key not in ('id', 'created_at'):
                setattr(entry, key, value)
        
        entry.updated_at = datetime.now().isoformat()
        self._save_vault()
        
        return entry
    
    def delete_entry(self, entry_id: str) -> bool:
        """删除密码条目"""
        if not self.is_unlocked:
            raise RuntimeError("密码库未解锁")
        
        if entry_id not in self.entries:
            return False
        
        del self.entries[entry_id]
        self._save_vault()
        
        return True
    
    def get_entry(self, entry_id: str) -> Optional[PasswordEntry]:
        """获取单个密码条目"""
        return self.entries.get(entry_id)
    
    def get_all_entries(self) -> List[PasswordEntry]:
        """获取所有密码条目"""
        return list(self.entries.values())
    
    def search_entries(self, query: str) -> List[PasswordEntry]:
        """搜索密码条目"""
        query = query.lower()
        results = []
        
        for entry in self.entries.values():
            if (query in entry.title.lower() or 
                query in entry.username.lower() or
                query in entry.url.lower() or
                query in entry.category.lower() or
                query in entry.notes.lower()):
                results.append(entry)
        
        return results
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for entry in self.entries.values():
            categories.add(entry.category)
        return sorted(list(categories))
    
    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """
        修改主密码
        
        安全措施：先验证旧密码，再创建备份，最后更新
        """
        if not self.is_unlocked:
            raise RuntimeError("密码库未解锁")
        
        if self.master_password != old_password:
            return False
        
        if len(new_password) < 8:
            raise ValueError("新密码长度至少为8个字符")
        
        # 创建额外备份（修改密码前）
        self._create_backup()
        
        # 更新主密码
        self.master_password = new_password
        self._save_vault()
        
        return True
    
    def export_to_json(self, filepath: str, include_passwords: bool = False):
        """
        导出为 JSON（用于备份查看，不包含密码）
        
        警告：如果 include_passwords=True，导出文件将包含明文密码！
        """
        if not self.is_unlocked:
            raise RuntimeError("密码库未解锁")
        
        data = []
        for entry in self.entries.values():
            entry_dict = asdict(entry)
            if not include_passwords:
                entry_dict['password'] = "********"
            data.append(entry_dict)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        categories = {}
        for entry in self.entries.values():
            cat = entry.category
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_entries': len(self.entries),
            'categories': categories,
            'backup_count': self._count_backups()
        }
    
    def _count_backups(self) -> int:
        """统计备份数量"""
        if not os.path.exists(self.backup_dir):
            return 0
        return len([f for f in os.listdir(self.backup_dir) 
                   if f.startswith("vault_backup_")])
