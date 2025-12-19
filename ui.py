"""
密码管理器图形界面
使用 CustomTkinter 构建现代化 UI
支持多语言（中文/英文）
VS Code 风格深色主题
"""

import os
import sys
import threading
import time
import ctypes
from typing import Optional, Callable
import customtkinter as ctk
from tkinter import messagebox, filedialog
import pyperclip

from password_manager import PasswordManager, PasswordEntry
from crypto_utils import generate_password
from i18n import t, i18n, config


# ============ 输入法控制 (Windows) ============
def force_english_ime(widget):
    """强制切换到英文输入法"""
    try:
        # 获取窗口句柄
        hwnd = widget.winfo_id()
        
        # Windows API 常量
        WM_INPUTLANGCHANGEREQUEST = 0x0050
        INPUTLANGCHANGE_SYSCHARSET = 0x0001
        
        # 英文键盘布局 (US English)
        ENGLISH_LAYOUT = 0x0409  # 英语(美国)
        
        # 发送消息切换输入法
        ctypes.windll.user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, ENGLISH_LAYOUT)
        
        # 备用方法：使用 imm32.dll 设置输入法状态
        imm32 = ctypes.windll.imm32
        himc = imm32.ImmGetContext(hwnd)
        if himc:
            # 关闭输入法（切换到英文模式）
            imm32.ImmSetOpenStatus(himc, False)
            imm32.ImmReleaseContext(hwnd, himc)
    except Exception:
        pass  # 静默失败，不影响程序运行


def setup_ime_control(entry_widget):
    """为输入框设置输入法控制"""
    def on_focus_in(event):
        force_english_ime(event.widget)
    
    # 绑定焦点事件
    entry_widget.bind("<FocusIn>", on_focus_in)
    
    # 对于CTkEntry，需要绑定到内部的Entry组件
    if hasattr(entry_widget, '_entry'):
        entry_widget._entry.bind("<FocusIn>", on_focus_in)


# ============ VS Code 主题配置 ============
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# VS Code 颜色方案
VS_BG_DARK = "#1e1e1e"          # 主背景
VS_BG_SIDEBAR = "#252526"        # 侧边栏背景
VS_BG_HEADER = "#323233"         # 标题栏背景
VS_BG_INPUT = "#3c3c3c"          # 输入框背景
VS_BG_HOVER = "#2a2d2e"          # hover 背景
VS_BG_SELECTED = "#094771"       # 选中项背景
VS_BG_BUTTON = "#0e639c"         # 按钮背景

VS_BORDER = "#3c3c3c"            # 边框
VS_BORDER_LIGHT = "#474747"      # 浅边框

VS_TEXT = "#cccccc"              # 主文字
VS_TEXT_DIM = "#808080"          # 次要文字
VS_TEXT_BRIGHT = "#ffffff"       # 高亮文字

VS_ACCENT = "#0078d4"            # 强调色（蓝色）
VS_ACCENT_HOVER = "#1c8bd4"      # 强调色 hover
VS_ERROR = "#f14c4c"             # 错误色（红色）
VS_ERROR_HOVER = "#d13333"       # 错误 hover
VS_SUCCESS = "#89d185"           # 成功色（绿色）
VS_WARNING = "#cca700"           # 警告色（黄色）

# 圆角配置 (VS Code 风格偏小圆角)
VS_CORNER = 4
VS_CORNER_SM = 3


# ============ Tooltip 类 ============
class Tooltip:
    """鼠标悬停提示框（优化性能）"""
    
    def __init__(self, widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self.scheduled_id = None
        self._visible = False
        
        widget.bind("<Enter>", self.on_enter, add="+")
        widget.bind("<Leave>", self.on_leave, add="+")
        widget.bind("<Button>", self.on_leave, add="+")
    
    def on_enter(self, event=None):
        """鼠标进入时计划显示提示"""
        self.cancel_scheduled()
        self.scheduled_id = self.widget.after(self.delay, self.show_tip)
    
    def on_leave(self, event=None):
        """鼠标离开时隐藏提示"""
        self.cancel_scheduled()
        self.hide_tip()
    
    def cancel_scheduled(self):
        """取消计划的显示"""
        if self.scheduled_id:
            try:
                self.widget.after_cancel(self.scheduled_id)
            except:
                pass
            self.scheduled_id = None
    
    def show_tip(self):
        """显示提示框"""
        if self._visible or self.tip_window:
            return
        
        try:
            x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            
            self.tip_window = tw = ctk.CTkToplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_attributes("-topmost", True)
            tw.wm_attributes("-alpha", 0.95)  # 轻微透明
            tw.configure(fg_color=VS_BG_HEADER)
            
            label = ctk.CTkLabel(
                tw,
                text=self.text,
                font=ctk.CTkFont(size=11),
                text_color=VS_TEXT,
                fg_color=VS_BG_HEADER,
                corner_radius=VS_CORNER_SM,
                padx=8,
                pady=4
            )
            label.pack()
            
            tw.update_idletasks()
            tw_width = tw.winfo_width()
            x = x - tw_width // 2
            tw.wm_geometry(f"+{x}+{y}")
            self._visible = True
        except:
            pass
    
    def hide_tip(self):
        """隐藏提示框"""
        self._visible = False
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except:
                pass
            self.tip_window = None
    
    def update_text(self, new_text: str):
        """更新提示文本"""
        self.text = new_text


class ClipboardCleaner:
    """剪贴板自动清理器"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._timer: Optional[threading.Timer] = None
        self._copied_value: Optional[str] = None
    
    def copy_and_schedule_clear(self, value: str):
        """复制到剪贴板并计划清理"""
        if self._timer:
            self._timer.cancel()
        
        self._copied_value = value
        pyperclip.copy(value)
        
        self._timer = threading.Timer(self.timeout, self._clear_clipboard)
        self._timer.daemon = True
        self._timer.start()
    
    def _clear_clipboard(self):
        """清理剪贴板"""
        try:
            current = pyperclip.paste()
            if current == self._copied_value:
                pyperclip.copy("")
        except:
            pass
        self._copied_value = None


class LoginWindow(ctk.CTkToplevel):
    """登录/创建密码库窗口"""
    
    def __init__(self, parent, password_manager: PasswordManager, on_success: Callable):
        super().__init__(parent)
        
        self.pm = password_manager
        self.on_success = on_success
        
        self.title(t("login_title"))
        self.geometry("420x480")
        self.resizable(True, True)
        self.minsize(380, 450)
        self.configure(fg_color=VS_BG_DARK)
        
        self.center_window()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.grab_set()
        
        self.setup_ui()
    
    def center_window(self):
        """居中显示窗口"""
        self.update_idletasks()
        width = 420
        height = 480
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        """设置界面"""
        # 语言切换按钮
        lang_btn = ctk.CTkButton(
            self,
            text=t("language_label") + (" EN" if i18n.language == "zh" else " 中"),
            width=55,
            height=28,
            corner_radius=VS_CORNER,
            fg_color="transparent",
            text_color=VS_ACCENT,
            hover_color=VS_BG_HOVER,
            font=ctk.CTkFont(size=12),
            command=self.toggle_language
        )
        lang_btn.place(x=355, y=10)
        
        # 主容器
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=30)
        
        # 标题
        title_label = ctk.CTkLabel(
            container, 
            text=t("app_name"),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=VS_TEXT_BRIGHT
        )
        title_label.pack(pady=(10, 5))
        
        # ========== 密码库路径选择区域 ==========
        vault_section = ctk.CTkFrame(container, fg_color=VS_BG_SIDEBAR, corner_radius=VS_CORNER)
        vault_section.pack(fill="x", pady=(15, 10))
        
        vault_header = ctk.CTkFrame(vault_section, fg_color="transparent")
        vault_header.pack(fill="x", padx=12, pady=(10, 5))
        
        vault_icon = ctk.CTkLabel(
            vault_header,
            text="📁",
            font=ctk.CTkFont(size=14),
            text_color=VS_TEXT
        )
        vault_icon.pack(side="left")
        
        vault_title = ctk.CTkLabel(
            vault_header,
            text=t("vault_location"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=VS_TEXT
        )
        vault_title.pack(side="left", padx=(5, 0))
        
        # 更改按钮
        change_btn = ctk.CTkButton(
            vault_header,
            text=t("change_btn"),
            width=60,
            height=24,
            corner_radius=VS_CORNER,
            fg_color="transparent",
            hover_color=VS_BG_HOVER,
            text_color=VS_ACCENT,
            font=ctk.CTkFont(size=11),
            command=self.change_vault_path
        )
        change_btn.pack(side="right")
        
        # 当前路径显示
        current_path = config.vault_path
        vault_dir = os.path.dirname(current_path)
        display_path = vault_dir
        if len(display_path) > 45:
            display_path = "..." + display_path[-42:]
        
        self.path_label = ctk.CTkLabel(
            vault_section,
            text=display_path,
            font=ctk.CTkFont(size=10),
            text_color=VS_TEXT_DIM,
            anchor="w"
        )
        self.path_label.pack(fill="x", padx=12, pady=(0, 5))
        
        # 密码库状态
        if self.pm.vault_exists():
            status_text = "✓ " + t("vault_status_exists")
            status_color = VS_SUCCESS
        else:
            status_text = "○ " + t("vault_status_new")
            status_color = VS_WARNING
        
        self.status_label = ctk.CTkLabel(
            vault_section,
            text=status_text,
            font=ctk.CTkFont(size=10),
            text_color=status_color,
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=12, pady=(0, 10))
        
        # ========== 副标题 ==========
        if self.pm.vault_exists():
            subtitle = t("unlock_subtitle")
        else:
            subtitle = t("create_vault_subtitle")
        
        self.subtitle_label = ctk.CTkLabel(
            container, 
            text=subtitle,
            font=ctk.CTkFont(size=13),
            text_color=VS_TEXT_DIM
        )
        self.subtitle_label.pack(pady=(10, 15))
        
        # 密码输入区域
        pwd_frame = ctk.CTkFrame(container, fg_color="transparent")
        pwd_frame.pack(pady=8)
        
        # 密码标签
        pwd_label = ctk.CTkLabel(
            pwd_frame,
            text=t("master_password"),
            font=ctk.CTkFont(size=12),
            text_color=VS_TEXT_DIM,
            anchor="w"
        )
        pwd_label.pack(fill="x", pady=(0, 4))
        
        # 密码输入框容器
        pwd_input_frame = ctk.CTkFrame(pwd_frame, fg_color="transparent")
        pwd_input_frame.pack(fill="x")
        
        # 密码输入框
        self.password_entry = ctk.CTkEntry(
            pwd_input_frame,
            width=255,
            height=40,
            corner_radius=VS_CORNER,
            show="●",
            font=ctk.CTkFont(size=14),
            fg_color=VS_BG_INPUT,
            border_color=VS_BORDER,
            border_width=1,
            text_color=VS_TEXT
        )
        self.password_entry.pack(side="left")
        self.password_entry.bind("<Return>", lambda e: self.submit())
        setup_ime_control(self.password_entry)
        
        # 显示/隐藏密码按钮
        self.show_pwd = False
        self.toggle_btn = ctk.CTkButton(
            pwd_input_frame,
            text="👁",
            width=40,
            height=40,
            corner_radius=VS_CORNER,
            fg_color=VS_BG_INPUT,
            hover_color=VS_BG_HOVER,
            text_color=VS_TEXT_DIM,
            border_color=VS_BORDER,
            border_width=1,
            command=self.toggle_password_visibility
        )
        self.toggle_btn.pack(side="left", padx=(5, 0))
        Tooltip(self.toggle_btn, t("tooltip_show_password"))
        
        # 如果是新建，需要确认密码
        if not self.pm.vault_exists():
            confirm_frame = ctk.CTkFrame(container, fg_color="transparent")
            confirm_frame.pack(pady=8)
            
            confirm_label = ctk.CTkLabel(
                confirm_frame,
                text=t("confirm_password"),
                font=ctk.CTkFont(size=12),
                text_color=VS_TEXT_DIM,
                anchor="w"
            )
            confirm_label.pack(fill="x", pady=(0, 4))
            
            confirm_input_frame = ctk.CTkFrame(confirm_frame, fg_color="transparent")
            confirm_input_frame.pack(fill="x")
            
            self.confirm_entry = ctk.CTkEntry(
                confirm_input_frame,
                width=255,
                height=40,
                corner_radius=VS_CORNER,
                show="●",
                font=ctk.CTkFont(size=14),
                fg_color=VS_BG_INPUT,
                border_color=VS_BORDER,
                border_width=1,
                text_color=VS_TEXT
            )
            self.confirm_entry.pack(side="left")
            self.confirm_entry.bind("<Return>", lambda e: self.submit())
            setup_ime_control(self.confirm_entry)
            
            # 确认密码的显示/隐藏按钮
            self.show_confirm_pwd = False
            self.toggle_confirm_btn = ctk.CTkButton(
                confirm_input_frame,
                text="👁",
                width=40,
                height=40,
                corner_radius=VS_CORNER,
                fg_color=VS_BG_INPUT,
                hover_color=VS_BG_HOVER,
                text_color=VS_TEXT_DIM,
                border_color=VS_BORDER,
                border_width=1,
                command=self.toggle_confirm_visibility
            )
            self.toggle_confirm_btn.pack(side="left", padx=(5, 0))
            Tooltip(self.toggle_confirm_btn, t("tooltip_show_password"))
        
        # 提交按钮
        btn_text = t("unlock_btn") if self.pm.vault_exists() else t("create_vault_btn")
        submit_btn = ctk.CTkButton(
            container,
            text=btn_text,
            width=300,
            height=40,
            corner_radius=VS_CORNER,
            fg_color=VS_ACCENT,
            hover_color=VS_ACCENT_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=VS_TEXT_BRIGHT,
            command=self.submit
        )
        submit_btn.pack(pady=20)
        
        # 提示信息
        if not self.pm.vault_exists():
            hint_label = ctk.CTkLabel(
                container,
                text=t("password_warning"),
                font=ctk.CTkFont(size=11),
                text_color=VS_WARNING
            )
            hint_label.pack()
        
        # 聚焦并切换输入法
        self.password_entry.focus()
        self.after(100, lambda: force_english_ime(self.password_entry))
    
    def change_vault_path(self):
        """更改密码库存储路径"""
        # 打开文件夹选择对话框
        new_dir = filedialog.askdirectory(
            title=t("select_vault_folder"),
            initialdir=config.get_vault_dir()
        )
        
        if not new_dir:
            return
        
        # 检查新路径是否有已存在的密码库
        new_vault_path = os.path.join(new_dir, "vault.dat")
        has_existing = os.path.exists(new_vault_path)
        
        # 保存新路径（不管有没有现有库）
        config.set_vault_dir(new_dir)
        
        if has_existing:
            # 发现已有密码库
            messagebox.showinfo(t("vault_location"), t("vault_found_switching"))
        else:
            # 没有密码库
            messagebox.showinfo(t("vault_location"), t("vault_new_location"))
        
        # 重启应用以加载新路径
        self.destroy()
        self.master.destroy()
        import subprocess
        subprocess.Popen([sys.executable, os.path.abspath(sys.argv[0])])
    
    def toggle_password_visibility(self):
        """切换主密码可见性"""
        self.show_pwd = not self.show_pwd
        self.password_entry.configure(show="" if self.show_pwd else "●")
        self.toggle_btn.configure(text="🙈" if self.show_pwd else "👁")
    
    def toggle_confirm_visibility(self):
        """切换确认密码可见性"""
        self.show_confirm_pwd = not self.show_confirm_pwd
        self.confirm_entry.configure(show="" if self.show_confirm_pwd else "●")
        self.toggle_confirm_btn.configure(text="🙈" if self.show_confirm_pwd else "👁")
    
    def toggle_language(self):
        """切换语言"""
        i18n.toggle_language()
        self.destroy()
        self.master.destroy()
        import subprocess
        subprocess.Popen([sys.executable, os.path.abspath(sys.argv[0])])
    
    def submit(self):
        """提交"""
        password = self.password_entry.get()
        
        if not password:
            messagebox.showerror(t("error"), t("error_enter_password"))
            return
        
        if self.pm.vault_exists():
            if self.pm.unlock(password):
                self.on_success()
                self.destroy()
            else:
                messagebox.showerror(t("error"), t("error_wrong_password"))
                self.password_entry.delete(0, 'end')
                self.password_entry.focus()
        else:
            confirm = self.confirm_entry.get()
            
            if len(password) < 8:
                messagebox.showerror(t("error"), t("error_password_min_length"))
                return
            
            if password != confirm:
                messagebox.showerror(t("error"), t("error_password_mismatch"))
                return
            
            try:
                self.pm.create_vault(password)
                self.on_success()
                self.destroy()
            except Exception as e:
                messagebox.showerror(t("error"), f"{t('error_create_failed')}: {str(e)}")
    
    def on_close(self):
        """关闭窗口"""
        sys.exit(0)


class PasswordDialog(ctk.CTkToplevel):
    """添加/编辑密码对话框"""
    
    def __init__(self, parent, entry: Optional[PasswordEntry] = None, 
                 on_save: Optional[Callable] = None):
        super().__init__(parent)
        
        self.entry = entry
        self.on_save = on_save
        self.result = None
        
        self.title(t("edit_password_title") if entry else t("add_password_title"))
        self.geometry("480x620")
        self.resizable(True, True)
        self.minsize(440, 580)
        self.configure(fg_color=VS_BG_DARK)
        
        self.center_window()
        self.grab_set()
        
        self.setup_ui()
    
    def center_window(self):
        """居中显示"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (240)
        y = (self.winfo_screenheight() // 2) - (310)
        self.geometry(f"480x620+{x}+{y}")
    
    def setup_ui(self):
        """设置界面"""
        # 主容器
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)
        
        # 字段配置
        fields = [
            ("title", t("field_title_label"), t("field_title_placeholder"), False),
            ("username", t("field_username_label"), t("field_username_placeholder"), True),
            ("password", t("field_password_label"), "", True),
            ("url", t("field_url_label"), t("field_url_placeholder"), True),
            ("category", t("field_category_label"), t("field_category_placeholder"), False),
            ("notes", t("field_notes_label"), t("field_notes_placeholder"), False),
        ]
        
        self.field_entries = {}
        
        for field_name, label, placeholder, needs_ime in fields:
            frame = ctk.CTkFrame(container, fg_color="transparent")
            frame.pack(fill="x", pady=6)
            
            lbl = ctk.CTkLabel(
                frame, 
                text=label,
                font=ctk.CTkFont(size=12),
                text_color=VS_TEXT,
                anchor="w"
            )
            lbl.pack(fill="x")
            
            if field_name == "password":
                pwd_frame = ctk.CTkFrame(frame, fg_color="transparent")
                pwd_frame.pack(fill="x")
                
                entry = ctk.CTkEntry(
                    pwd_frame,
                    height=36,
                    corner_radius=VS_CORNER,
                    placeholder_text=placeholder,
                    placeholder_text_color=VS_TEXT_DIM,
                    show="●",
                    font=ctk.CTkFont(size=13),
                    fg_color=VS_BG_INPUT,
                    border_color=VS_BORDER,
                    border_width=1,
                    text_color=VS_TEXT
                )
                entry.pack(side="left", fill="x", expand=True)
                setup_ime_control(entry)
                
                # 显示/隐藏按钮
                self.show_pwd = False
                self.toggle_btn = ctk.CTkButton(
                    pwd_frame,
                    text="👁",
                    width=36,
                    height=36,
                    corner_radius=VS_CORNER,
                    fg_color=VS_BG_INPUT,
                    hover_color=VS_BG_HOVER,
                    text_color=VS_TEXT_DIM,
                    border_color=VS_BORDER,
                    border_width=1,
                    command=self.toggle_password_visibility
                )
                self.toggle_btn.pack(side="left", padx=(6, 0))
                Tooltip(self.toggle_btn, t("tooltip_show_password"))
                
                # 生成按钮
                gen_btn = ctk.CTkButton(
                    pwd_frame,
                    text="🔄",
                    width=36,
                    height=36,
                    corner_radius=VS_CORNER,
                    fg_color=VS_BG_INPUT,
                    hover_color=VS_BG_HOVER,
                    text_color=VS_ACCENT,
                    border_color=VS_BORDER,
                    border_width=1,
                    command=self.generate_password
                )
                gen_btn.pack(side="left", padx=(6, 0))
                Tooltip(gen_btn, t("tooltip_generate_password"))
                
            elif field_name == "notes":
                entry = ctk.CTkTextbox(
                    frame, 
                    height=70,
                    corner_radius=VS_CORNER,
                    font=ctk.CTkFont(size=13),
                    fg_color=VS_BG_INPUT,
                    border_color=VS_BORDER,
                    border_width=1,
                    text_color=VS_TEXT
                )
                entry.pack(fill="x")
            else:
                entry = ctk.CTkEntry(
                    frame,
                    height=36,
                    corner_radius=VS_CORNER,
                    placeholder_text=placeholder,
                    placeholder_text_color=VS_TEXT_DIM,
                    font=ctk.CTkFont(size=13),
                    fg_color=VS_BG_INPUT,
                    border_color=VS_BORDER,
                    border_width=1,
                    text_color=VS_TEXT
                )
                entry.pack(fill="x")
                if needs_ime:
                    setup_ime_control(entry)
            
            self.field_entries[field_name] = entry
        
        # 填充数据
        if self.entry:
            self.field_entries["title"].insert(0, self.entry.title)
            self.field_entries["username"].insert(0, self.entry.username)
            self.field_entries["password"].insert(0, self.entry.password)
            self.field_entries["url"].insert(0, self.entry.url)
            self.field_entries["category"].insert(0, self.entry.category)
            self.field_entries["notes"].insert("1.0", self.entry.notes)
        
        # 按钮区
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=t("cancel_btn"),
            width=100,
            height=36,
            corner_radius=VS_CORNER,
            fg_color=VS_BG_INPUT,
            hover_color=VS_BG_HOVER,
            text_color=VS_TEXT,
            border_color=VS_BORDER,
            border_width=1,
            command=self.destroy
        )
        cancel_btn.pack(side="left")
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text=t("save_btn"),
            width=100,
            height=36,
            corner_radius=VS_CORNER,
            fg_color=VS_ACCENT,
            hover_color=VS_ACCENT_HOVER,
            text_color=VS_TEXT_BRIGHT,
            command=self.save
        )
        save_btn.pack(side="right")
    
    def toggle_password_visibility(self):
        """切换密码可见性"""
        self.show_pwd = not self.show_pwd
        self.field_entries["password"].configure(show="" if self.show_pwd else "●")
        self.toggle_btn.configure(text="🙈" if self.show_pwd else "👁")
    
    def generate_password(self):
        """生成随机密码"""
        pwd = generate_password(length=20)
        entry = self.field_entries["password"]
        entry.delete(0, 'end')
        entry.insert(0, pwd)
    
    def save(self):
        """保存"""
        title = self.field_entries["title"].get().strip()
        username = self.field_entries["username"].get().strip()
        password = self.field_entries["password"].get()
        url = self.field_entries["url"].get().strip()
        category = self.field_entries["category"].get().strip() or t("default_category")
        notes = self.field_entries["notes"].get("1.0", "end-1c").strip()
        
        if not title:
            messagebox.showerror(t("error"), t("error_enter_title"))
            return
        if not password:
            messagebox.showerror(t("error"), t("error_enter_password_field"))
            return
        
        self.result = {
            "title": title,
            "username": username,
            "password": password,
            "url": url,
            "category": category,
            "notes": notes
        }
        
        if self.on_save:
            self.on_save(self.result)
        
        self.destroy()


class PasswordGeneratorDialog(ctk.CTkToplevel):
    """密码生成器对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title(t("generator_title"))
        self.geometry("400x360")
        self.resizable(True, True)
        self.minsize(360, 340)
        self.configure(fg_color=VS_BG_DARK)
        self.grab_set()
        
        self.clipboard = ClipboardCleaner()
        self.setup_ui()
        self.generate()
    
    def setup_ui(self):
        """设置界面"""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 生成的密码显示
        self.password_var = ctk.StringVar()
        pwd_frame = ctk.CTkFrame(container, fg_color="transparent")
        pwd_frame.pack(fill="x", pady=(0, 15))
        
        self.pwd_entry = ctk.CTkEntry(
            pwd_frame,
            textvariable=self.password_var,
            height=42,
            corner_radius=VS_CORNER,
            font=ctk.CTkFont(size=14, family="Consolas"),
            fg_color=VS_BG_INPUT,
            border_color=VS_BORDER,
            border_width=1,
            text_color=VS_TEXT,
            state="readonly"
        )
        self.pwd_entry.pack(side="left", fill="x", expand=True)
        
        copy_btn = ctk.CTkButton(
            pwd_frame,
            text="📋",
            width=42,
            height=42,
            corner_radius=VS_CORNER,
            fg_color=VS_ACCENT,
            hover_color=VS_ACCENT_HOVER,
            text_color=VS_TEXT_BRIGHT,
            command=self.copy_password
        )
        copy_btn.pack(side="left", padx=(8, 0))
        
        # 长度滑块
        length_frame = ctk.CTkFrame(container, fg_color="transparent")
        length_frame.pack(fill="x", pady=8)
        
        ctk.CTkLabel(
            length_frame, 
            text=t("length_label"),
            text_color=VS_TEXT,
            font=ctk.CTkFont(size=13)
        ).pack(side="left")
        
        self.length_var = ctk.IntVar(value=20)
        self.length_label = ctk.CTkLabel(
            length_frame, 
            text="20",
            text_color=VS_ACCENT,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.length_label.pack(side="right")
        
        self.length_slider = ctk.CTkSlider(
            length_frame,
            from_=8,
            to=64,
            variable=self.length_var,
            button_color=VS_ACCENT,
            button_hover_color=VS_ACCENT_HOVER,
            progress_color=VS_ACCENT,
            command=self.on_length_change
        )
        self.length_slider.pack(side="right", fill="x", expand=True, padx=10)
        
        # 选项
        self.uppercase_var = ctk.BooleanVar(value=True)
        self.lowercase_var = ctk.BooleanVar(value=True)
        self.digits_var = ctk.BooleanVar(value=True)
        self.symbols_var = ctk.BooleanVar(value=True)
        
        options = [
            (t("uppercase_option"), self.uppercase_var),
            (t("lowercase_option"), self.lowercase_var),
            (t("digits_option"), self.digits_var),
            (t("symbols_option"), self.symbols_var),
        ]
        
        for text, var in options:
            cb = ctk.CTkCheckBox(
                container,
                text=text,
                variable=var,
                text_color=VS_TEXT,
                fg_color=VS_ACCENT,
                hover_color=VS_ACCENT_HOVER,
                border_color=VS_BORDER,
                command=self.generate
            )
            cb.pack(anchor="w", pady=3)
        
        # 生成按钮
        gen_btn = ctk.CTkButton(
            container,
            text=t("regenerate_btn"),
            height=38,
            corner_radius=VS_CORNER,
            fg_color=VS_ACCENT,
            hover_color=VS_ACCENT_HOVER,
            text_color=VS_TEXT_BRIGHT,
            font=ctk.CTkFont(size=13),
            command=self.generate
        )
        gen_btn.pack(fill="x", pady=(15, 0))
    
    def on_length_change(self, value):
        """长度改变"""
        self.length_label.configure(text=str(int(value)))
        self.generate()
    
    def generate(self):
        """生成密码"""
        pwd = generate_password(
            length=self.length_var.get(),
            use_uppercase=self.uppercase_var.get(),
            use_lowercase=self.lowercase_var.get(),
            use_digits=self.digits_var.get(),
            use_symbols=self.symbols_var.get()
        )
        self.password_var.set(pwd)
    
    def copy_password(self):
        """复制密码"""
        self.clipboard.copy_and_schedule_clear(self.password_var.get())
        messagebox.showinfo(t("copied_title"), t("copied_message"))


class MainWindow(ctk.CTk):
    """主窗口"""
    
    def __init__(self, password_manager: PasswordManager):
        super().__init__()
        
        self.pm = password_manager
        self.clipboard = ClipboardCleaner()
        self.selected_entry_id: Optional[str] = None
        self._list_items: dict = {}  # 缓存列表项 {entry_id: frame}
        self._current_entries: list = []  # 当前显示的条目
        self._updating = False  # 防止重复更新
        
        self.title(t("app_title"))
        self.geometry("1000x650")
        self.minsize(800, 500)
        self.configure(fg_color=VS_BG_DARK)
        
        self.setup_ui()
        self.refresh_list()
        
        # 自动锁定（5分钟无操作）
        self.last_activity = time.time()
        self.bind_all("<Key>", self.on_activity)
        self.bind_all("<Button>", self.on_activity)
        self.check_auto_lock()
    
    def on_activity(self, event=None):
        """记录用户活动"""
        self.last_activity = time.time()
    
    def check_auto_lock(self):
        """检查是否需要自动锁定"""
        if time.time() - self.last_activity > 300:  # 5分钟
            self.lock_vault()
        else:
            self.after(10000, self.check_auto_lock)
    
    def setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        toolbar = ctk.CTkFrame(
            self, 
            height=48, 
            corner_radius=0, 
            fg_color=VS_BG_HEADER,
            border_width=0
        )
        toolbar.pack(fill="x", padx=0, pady=0)
        toolbar.pack_propagate(False)
        
        # 搜索框
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda *args: self.on_search())
        
        search_entry = ctk.CTkEntry(
            toolbar,
            width=260,
            height=30,
            corner_radius=VS_CORNER,
            placeholder_text=t("search_placeholder"),
            placeholder_text_color=VS_TEXT_DIM,
            textvariable=self.search_var,
            font=ctk.CTkFont(size=13),
            fg_color=VS_BG_INPUT,
            border_color=VS_BORDER,
            border_width=1,
            text_color=VS_TEXT
        )
        search_entry.pack(side="left", padx=(12, 12), pady=9)
        
        # 工具栏按钮 - VS Code 简约风格（统一尺寸和对齐）
        add_btn = ctk.CTkButton(
            toolbar,
            text="＋",
            width=30,
            height=30,
            corner_radius=VS_CORNER,
            fg_color="transparent",
            hover_color=VS_BG_HOVER,
            text_color=VS_TEXT,
            font=ctk.CTkFont(size=16),
            command=self.add_password
        )
        add_btn.pack(side="left", padx=2, pady=9)
        Tooltip(add_btn, t("tooltip_add"))
        
        gen_btn = ctk.CTkButton(
            toolbar,
            text="🔄",
            width=30,
            height=30,
            corner_radius=VS_CORNER,
            fg_color="transparent",
            hover_color=VS_BG_HOVER,
            text_color=VS_TEXT,
            font=ctk.CTkFont(size=14),
            command=self.open_generator
        )
        gen_btn.pack(side="left", padx=2, pady=9)
        Tooltip(gen_btn, t("tooltip_generate_password"))
        
        # 分隔符
        sep = ctk.CTkFrame(toolbar, width=1, height=20, fg_color=VS_BORDER)
        sep.pack(side="left", padx=8, pady=14)
        
        lock_btn = ctk.CTkButton(
            toolbar,
            text="🔒",
            width=30,
            height=30,
            corner_radius=VS_CORNER,
            fg_color="transparent",
            hover_color=VS_BG_HOVER,
            text_color=VS_TEXT,
            font=ctk.CTkFont(size=14),
            command=self.lock_vault
        )
        lock_btn.pack(side="right", padx=8, pady=9)
        Tooltip(lock_btn, t("tooltip_lock"))
        
        # 语言切换按钮
        lang_btn = ctk.CTkButton(
            toolbar,
            text=t("language_label") + (" EN" if i18n.language == "zh" else " 中"),
            width=55,
            height=30,
            corner_radius=VS_CORNER,
            fg_color="transparent",
            text_color=VS_ACCENT,
            hover_color=VS_BG_HOVER,
            font=ctk.CTkFont(size=12),
            command=self.toggle_language
        )
        lang_btn.pack(side="right", padx=4, pady=9)
        
        # 统计信息
        self.stats_label = ctk.CTkLabel(
            toolbar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=VS_TEXT_DIM
        )
        self.stats_label.pack(side="right", padx=12, pady=9)
        
        # 主内容区
        content = ctk.CTkFrame(self, fg_color=VS_BG_DARK)
        content.pack(fill="both", expand=True, padx=0, pady=0)
        
        # 左侧列表
        list_frame = ctk.CTkFrame(
            content, 
            width=320, 
            corner_radius=0,
            fg_color=VS_BG_SIDEBAR,
            border_width=0
        )
        list_frame.pack(side="left", fill="y", padx=0, pady=0)
        list_frame.pack_propagate(False)
        
        # 密码列表
        self.list_container = ctk.CTkScrollableFrame(
            list_frame, 
            corner_radius=0,
            fg_color=VS_BG_SIDEBAR
        )
        self.list_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # 右侧详情
        self.detail_frame = ctk.CTkFrame(
            content, 
            corner_radius=0,
            fg_color=VS_BG_DARK
        )
        self.detail_frame.pack(side="right", fill="both", expand=True)
        
        # 预创建详情页控件（避免每次重建）
        self._init_detail_widgets()
        
        self.show_empty_detail()
    
    def toggle_language(self):
        """切换语言"""
        i18n.toggle_language()
        self.pm.lock()
        self.destroy()
        import subprocess
        subprocess.Popen([sys.executable, os.path.abspath(sys.argv[0])])
    
    def _init_detail_widgets(self):
        """预创建详情页控件，避免每次切换都重建"""
        # 空状态标签
        self._empty_label = ctk.CTkLabel(
            self.detail_frame,
            text=t("select_entry_hint"),
            font=ctk.CTkFont(size=15),
            text_color=VS_TEXT_DIM
        )
        
        # 详情容器
        self._detail_container = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        
        # 标题区域
        self._header = ctk.CTkFrame(self._detail_container, fg_color="transparent")
        self._header.pack(fill="x", pady=(0, 20), padx=30, anchor="n")
        
        self._title_label = ctk.CTkLabel(
            self._header,
            text="",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=VS_TEXT_BRIGHT,
            anchor="w"
        )
        self._title_label.pack(side="left")
        
        # 按钮容器
        self._btn_container = ctk.CTkFrame(self._header, fg_color="transparent")
        self._btn_container.pack(side="right")
        
        self._edit_btn = ctk.CTkButton(
            self._btn_container,
            text="✏",
            width=28,
            height=28,
            corner_radius=VS_CORNER,
            fg_color="transparent",
            hover_color=VS_BG_HOVER,
            text_color=VS_TEXT_DIM,
            font=ctk.CTkFont(size=13),
            command=lambda: self.edit_entry(self.selected_entry_id)
        )
        self._edit_btn.pack(side="left", padx=2)
        Tooltip(self._edit_btn, t("tooltip_edit"))
        
        self._delete_btn = ctk.CTkButton(
            self._btn_container,
            text="🗑",
            width=28,
            height=28,
            corner_radius=VS_CORNER,
            fg_color="transparent",
            hover_color=VS_BG_HOVER,
            text_color=VS_TEXT_DIM,
            font=ctk.CTkFont(size=13),
            command=lambda: self.delete_entry(self.selected_entry_id)
        )
        self._delete_btn.pack(side="left", padx=2)
        Tooltip(self._delete_btn, t("tooltip_delete"))
        
        # 分隔线
        self._separator = ctk.CTkFrame(self._detail_container, height=1, fg_color=VS_BORDER)
        self._separator.pack(fill="x", pady=(0, 15), padx=30)
        
        # 字段容器（滚动区域）
        self._fields_container = ctk.CTkScrollableFrame(
            self._detail_container,
            fg_color="transparent",
            scrollbar_button_color=VS_BG_HOVER,
            scrollbar_button_hover_color=VS_TEXT_DIM
        )
        self._fields_container.pack(fill="both", expand=True, padx=30, pady=(0, 25))
        
        # 记录当前显示状态
        self._detail_visible = False
    
    def show_empty_detail(self):
        """显示空的详情页"""
        if self._detail_visible:
            self._detail_container.pack_forget()
            self._detail_visible = False
        self._empty_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def refresh_list(self, keep_selection=False):
        """刷新密码列表"""
        if self._updating:
            return
        self._updating = True
        
        try:
            query = self.search_var.get()
            if query:
                entries = self.pm.search_entries(query)
            else:
                entries = self.pm.get_all_entries()
            
            entries.sort(key=lambda x: x.title.lower())
            
            stats = self.pm.get_stats()
            self.stats_label.configure(text=t("total_records", count=stats['total_entries']))
            
            # 检查是否需要完全重建列表
            new_ids = [e.id for e in entries]
            old_ids = [e.id for e in self._current_entries]
            
            if new_ids != old_ids:
                # 条目变化，需要重建
                self._rebuild_list(entries)
            else:
                # 只更新选中状态
                self._update_selection()
            
            self._current_entries = entries
            
            if not entries:
                for widget in self.list_container.winfo_children():
                    widget.destroy()
                self._list_items.clear()
                empty_label = ctk.CTkLabel(
                    self.list_container,
                    text=t("no_records"),
                    font=ctk.CTkFont(size=13),
                    text_color=VS_TEXT_DIM
                )
                empty_label.pack(pady=50)
        finally:
            self._updating = False
    
    def _rebuild_list(self, entries):
        """重建整个列表"""
        # 批量删除旧的
        for widget in self.list_container.winfo_children():
            widget.destroy()
        self._list_items.clear()
        
        # 批量创建新的
        for entry in entries:
            self._create_list_item(entry)
        
        # 强制更新界面
        self.list_container.update_idletasks()
    
    def _update_selection(self):
        """只更新选中状态，不重建列表"""
        for entry_id, item_data in self._list_items.items():
            is_selected = entry_id == self.selected_entry_id
            frame = item_data['frame']
            title_label = item_data['title']
            
            if is_selected:
                frame.configure(fg_color=VS_BG_SELECTED)
                title_label.configure(text_color=VS_TEXT_BRIGHT)
            else:
                frame.configure(fg_color="transparent")
                title_label.configure(text_color=VS_TEXT)
    
    def _create_list_item(self, entry: PasswordEntry):
        """创建列表项"""
        is_selected = self.selected_entry_id == entry.id
        
        item = ctk.CTkFrame(
            self.list_container,
            height=56,
            corner_radius=0,
            fg_color=VS_BG_SELECTED if is_selected else "transparent",
            cursor="hand2"
        )
        item.pack(fill="x", pady=0)
        item.pack_propagate(False)
        
        entry_id = entry.id  # 捕获变量
        
        def on_click(e):
            self.select_entry(entry_id)
        
        def on_enter(e):
            if self.selected_entry_id != entry_id:
                item.configure(fg_color=VS_BG_HOVER)
        
        def on_leave(e):
            if self.selected_entry_id != entry_id:
                item.configure(fg_color="transparent")
        
        item.bind("<Button-1>", on_click)
        item.bind("<Enter>", on_enter)
        item.bind("<Leave>", on_leave)
        
        # 左边距和内容
        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=8)
        inner.bind("<Button-1>", on_click)
        
        title_label = ctk.CTkLabel(
            inner,
            text=entry.title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=VS_TEXT_BRIGHT if is_selected else VS_TEXT,
            anchor="w"
        )
        title_label.pack(fill="x")
        title_label.bind("<Button-1>", on_click)
        
        username_label = ctk.CTkLabel(
            inner,
            text=entry.username if entry.username else "-",
            font=ctk.CTkFont(size=11),
            text_color=VS_TEXT_DIM,
            anchor="w"
        )
        username_label.pack(fill="x")
        username_label.bind("<Button-1>", on_click)
        
        # 缓存列表项引用
        self._list_items[entry.id] = {
            'frame': item,
            'title': title_label,
            'username': username_label
        }
    
    def select_entry(self, entry_id: str):
        """选择条目，显示详情"""
        if self.selected_entry_id == entry_id:
            return  # 已经选中，无需操作
        
        old_id = self.selected_entry_id
        self.selected_entry_id = entry_id
        
        # 只更新受影响的列表项，不重建整个列表
        if old_id and old_id in self._list_items:
            old_item = self._list_items[old_id]
            old_item['frame'].configure(fg_color="transparent")
            old_item['title'].configure(text_color=VS_TEXT)
        
        if entry_id in self._list_items:
            new_item = self._list_items[entry_id]
            new_item['frame'].configure(fg_color=VS_BG_SELECTED)
            new_item['title'].configure(text_color=VS_TEXT_BRIGHT)
        
        # 更新详情页
        self._show_entry_detail(entry_id)
    
    def _show_entry_detail(self, entry_id: str):
        """显示条目详情（优化性能，只更新内容不重建控件）"""
        entry = self.pm.get_entry(entry_id)
        if not entry:
            return
        
        # 隐藏空状态标签，显示详情容器
        self._empty_label.place_forget()
        if not self._detail_visible:
            self._detail_container.pack(fill="both", expand=True, pady=25)
            self._detail_visible = True
        
        # 更新标题
        self._title_label.configure(text=entry.title)
        
        # 清除字段容器中的旧内容
        for widget in self._fields_container.winfo_children():
            widget.destroy()
        
        # 详情字段
        fields = [
            (t("field_username"), entry.username, True),
            (t("field_password"), entry.password, True, True),
            (t("field_url"), entry.url, True),
            (t("field_category"), entry.category, False),
            (t("field_notes"), entry.notes, False),
            (t("field_created_at"), entry.created_at[:19].replace("T", " "), False),
            (t("field_updated_at"), entry.updated_at[:19].replace("T", " "), False),
        ]
        
        for field_info in fields:
            label = field_info[0]
            value = field_info[1]
            copyable = field_info[2] if len(field_info) > 2 else False
            is_password = field_info[3] if len(field_info) > 3 else False
            
            if not value:
                continue
            
            field_frame = ctk.CTkFrame(self._fields_container, fg_color="transparent")
            field_frame.pack(fill="x", pady=7)
            
            lbl = ctk.CTkLabel(
                field_frame,
                text=label,
                font=ctk.CTkFont(size=11),
                text_color=VS_TEXT_DIM,
                anchor="w"
            )
            lbl.pack(fill="x")
            
            value_frame = ctk.CTkFrame(field_frame, fg_color="transparent")
            value_frame.pack(fill="x")
            
            if is_password:
                password_value = value
                display_value = "●" * min(len(password_value), 20)
                value_var = ctk.StringVar(value=display_value)
                
                value_lbl = ctk.CTkLabel(
                    value_frame,
                    textvariable=value_var,
                    font=ctk.CTkFont(size=13, family="Consolas"),
                    text_color=VS_TEXT,
                    anchor="w"
                )
                value_lbl.pack(side="left")
                
                show_state = {"shown": False}
                
                def make_toggle_func(pwd_val, var, btn_ref, state):
                    def toggle_show():
                        state["shown"] = not state["shown"]
                        if state["shown"]:
                            var.set(pwd_val)
                            btn_ref[0].configure(text="🙈")
                        else:
                            var.set("●" * min(len(pwd_val), 20))
                            btn_ref[0].configure(text="👁")
                    return toggle_show
                
                btn_ref = [None]
                
                pwd_btns = ctk.CTkFrame(value_frame, fg_color="transparent")
                pwd_btns.pack(side="right")
                
                copy_btn = ctk.CTkButton(
                    pwd_btns,
                    text="📋",
                    width=26,
                    height=24,
                    corner_radius=VS_CORNER_SM,
                    fg_color="transparent",
                    hover_color=VS_BG_HOVER,
                    text_color=VS_TEXT_DIM,
                    font=ctk.CTkFont(size=12),
                    command=lambda v=value: self.copy_to_clipboard(v)
                )
                copy_btn.pack(side="left", padx=1)
                Tooltip(copy_btn, t("tooltip_copy"))
                
                show_btn = ctk.CTkButton(
                    pwd_btns,
                    text="👁",
                    width=26,
                    height=24,
                    corner_radius=VS_CORNER_SM,
                    fg_color="transparent",
                    hover_color=VS_BG_HOVER,
                    text_color=VS_TEXT_DIM,
                    font=ctk.CTkFont(size=12),
                    command=make_toggle_func(password_value, value_var, btn_ref, show_state)
                )
                btn_ref[0] = show_btn
                show_btn.pack(side="left", padx=1)
                Tooltip(show_btn, t("tooltip_show_password"))
                
            else:
                value_lbl = ctk.CTkLabel(
                    value_frame,
                    text=value,
                    font=ctk.CTkFont(size=13),
                    text_color=VS_TEXT,
                    anchor="w",
                    wraplength=400
                )
                value_lbl.pack(side="left")
                
                if copyable and value:
                    copy_btn = ctk.CTkButton(
                        value_frame,
                        text="📋",
                        width=26,
                        height=24,
                        corner_radius=VS_CORNER_SM,
                        fg_color="transparent",
                        hover_color=VS_BG_HOVER,
                        text_color=VS_TEXT_DIM,
                        font=ctk.CTkFont(size=12),
                        command=lambda v=value: self.copy_to_clipboard(v)
                    )
                    copy_btn.pack(side="right")
                    Tooltip(copy_btn, t("tooltip_copy"))
    
    def copy_to_clipboard(self, value: str):
        """复制到剪贴板"""
        self.clipboard.copy_and_schedule_clear(value)
        self.stats_label.configure(text=t("copied_hint"), text_color=VS_SUCCESS)
        self.after(2000, lambda: self.stats_label.configure(
            text=t("total_records", count=self.pm.get_stats()['total_entries']),
            text_color=VS_TEXT_DIM
        ))
    
    def on_search(self):
        """搜索（防抖动）"""
        # 取消之前的搜索计划
        if hasattr(self, '_search_timer') and self._search_timer:
            self.after_cancel(self._search_timer)
        
        # 延迟150ms执行搜索，减少频繁刷新
        self._search_timer = self.after(150, self._do_search)
    
    def _do_search(self):
        """执行搜索"""
        self._search_timer = None
        # 强制重建列表因为搜索结果变了
        self._current_entries = []
        self.refresh_list()
    
    def add_password(self):
        """添加密码"""
        def on_save(data):
            self.pm.add_entry(**data)
            self.refresh_list()
        
        PasswordDialog(self, on_save=on_save)
    
    def edit_entry(self, entry_id: str):
        """编辑条目"""
        entry = self.pm.get_entry(entry_id)
        if not entry:
            return
        
        def on_save(data):
            self.pm.update_entry(entry_id, **data)
            self.refresh_list()
            self.select_entry(entry_id)
        
        PasswordDialog(self, entry=entry, on_save=on_save)
    
    def delete_entry(self, entry_id: str):
        """删除条目"""
        entry = self.pm.get_entry(entry_id)
        if not entry:
            return
        
        if messagebox.askyesno(
            t("confirm_delete_title"), 
            t("confirm_delete_message", title=entry.title)
        ):
            self.pm.delete_entry(entry_id)
            self.refresh_list()
            self.show_empty_detail()
    
    def open_generator(self):
        """打开密码生成器"""
        PasswordGeneratorDialog(self)
    
    def lock_vault(self):
        """锁定密码库"""
        self.pm.lock()
        self.destroy()
        import subprocess
        subprocess.Popen([sys.executable, os.path.abspath(sys.argv[0])])
