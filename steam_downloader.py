# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog
import threading
import os
import sys
import ctypes
import urllib.request
import subprocess
import socket
import webbrowser
import json
from pathlib import Path

try:
    import customtkinter as ctk
    HAS_CUSTOMTKINTER = True
except ImportError:
    HAS_CUSTOMTKINTER = False

STEAM_MIRROR_URLS = [
    "https://steamcdn-a.akamaihd.net/client/installer/SteamSetup.exe",
    "https://cdn.steamstatic.com/client/installer/SteamSetup.exe",
]

STEAM_HOSTS_ENTRIES = [
    ("store.steampowered.com", "184.28.90.75"),
    ("steamcommunity.com", "184.28.90.75"),
    ("cdn.steamstatic.com", "23.62.190.30"),
    ("steamcdn-a.akamaihd.net", "23.62.190.30"),
    ("client-download.steampowered.com", "184.28.90.75"),
    ("login.steampowered.com", "184.28.90.75"),
]

FAST_DNS = [
    ("8.8.8.8", "Google DNS"),
    ("8.8.4.4", "Google DNS Secondary"),
    ("1.1.1.1", "Cloudflare DNS"),
    ("223.5.5.5", "Aliyun DNS"),
    ("119.29.29.29", "Tencent DNS"),
]

class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=200, height=45, 
                 bg_color="#1a1a2e", hover_color="#16213e", text_color="#ffffff",
                 accent_color="#0f3460", corner_radius=10):
        super().__init__(parent, width=width, height=height, 
                        bg=parent.cget('bg'), highlightthickness=0)
        
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.accent_color = accent_color
        self.corner_radius = corner_radius
        self.width = width
        self.height = height
        self.text = text
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
        self.draw_button(bg_color)
    
    def draw_button(self, color):
        self.delete("all")
        r = self.corner_radius
        
        self.create_rounded_rect(0, 0, self.width, self.height, r, fill=color, outline="")
        
        self.create_text(self.width/2, self.height/2, text=self.text, 
                        fill=self.text_color, font=("Microsoft YaHei UI", 11, "bold"))
    
    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1,
            x2, y1, x2, y1+r,
            x2, y2-r, x2, y2,
            x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r,
            x1, y1+r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def on_enter(self, event):
        self.draw_button(self.hover_color)
        self.config(cursor="hand2")
    
    def on_leave(self, event):
        self.draw_button(self.bg_color)
        self.config(cursor="")
    
    def on_click(self, event):
        if self.command:
            self.command()

class GlassFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        bg = kwargs.pop('bg', '#1a1a2e')
        super().__init__(parent, bg=bg, **kwargs)

class SteamDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam 客户端下载工具")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#0d0d1a')
        
        self.is_accelerating = False
        self.is_downloading = False
        self.save_path = self.get_default_save_path()
        self.accel_mode = "dns"
        
        self.setup_styles()
        self.setup_ui()
        self.check_acceleration_status()
        
    def setup_styles(self):
        self.colors = {
            'bg_dark': '#0d0d1a',
            'bg_card': '#1a1a2e',
            'bg_card_hover': '#16213e',
            'accent': '#e94560',
            'accent_hover': '#ff6b6b',
            'success': '#00d26a',
            'warning': '#ffc107',
            'text_primary': '#ffffff',
            'text_secondary': '#a0a0a0',
            'border': '#2d2d44',
        }
        
    def get_default_save_path(self):
        return os.path.join(os.path.expanduser("~"), "Downloads")
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        header_frame = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        steam_icon = tk.Label(header_frame, text="🎮", font=("Segoe UI Emoji", 36), 
                             bg=self.colors['bg_dark'], fg=self.colors['accent'])
        steam_icon.pack(side=tk.LEFT, padx=(0, 15))
        
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        title_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        title_label = tk.Label(title_frame, text="Steam 下载工具", 
                              font=("Microsoft YaHei UI", 22, "bold"),
                              bg=self.colors['bg_dark'], fg=self.colors['text_primary'])
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(title_frame, text="一键加速 · 快速下载", 
                                 font=("Microsoft YaHei UI", 10),
                                 bg=self.colors['bg_dark'], fg=self.colors['text_secondary'])
        subtitle_label.pack(anchor='w')
        
        accel_card = self.create_card(main_frame, "网络加速")
        accel_card.pack(fill=tk.X, pady=(0, 20))
        
        mode_frame = tk.Frame(accel_card, bg=self.colors['bg_card'])
        mode_frame.pack(fill=tk.X, pady=(10, 15))
        
        tk.Label(mode_frame, text="加速模式:", font=("Microsoft YaHei UI", 10),
                bg=self.colors['bg_card'], fg=self.colors['text_secondary']).pack(side=tk.LEFT)
        
        self.mode_var = tk.StringVar(value="dns")
        
        modes = [("DNS优化 (推荐)", "dns"), ("Hosts加速", "hosts")]
        for text, value in modes:
            rb = tk.Radiobutton(mode_frame, text=text, variable=self.mode_var, value=value,
                               bg=self.colors['bg_card'], fg=self.colors['text_primary'],
                               selectcolor=self.colors['bg_dark'], activebackground=self.colors['bg_card'],
                               font=("Microsoft YaHei UI", 9), command=self.on_mode_change)
            rb.pack(side=tk.LEFT, padx=10)
        
        status_frame = tk.Frame(accel_card, bg=self.colors['bg_card'])
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_indicator = tk.Canvas(status_frame, width=12, height=12, 
                                         bg=self.colors['bg_card'], highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 8))
        self.status_indicator.create_oval(2, 2, 10, 10, fill=self.colors['warning'], outline="")
        
        self.accel_status_label = tk.Label(status_frame, text="未加速", 
                                          font=("Microsoft YaHei UI", 11),
                                          bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.accel_status_label.pack(side=tk.LEFT)
        
        btn_frame = tk.Frame(accel_card, bg=self.colors['bg_card'])
        btn_frame.pack(pady=15)
        
        self.accel_btn = ModernButton(btn_frame, "⚡ 开启加速", command=self.toggle_acceleration,
                                     width=200, height=45, bg_color=self.colors['accent'],
                                     hover_color=self.colors['accent_hover'])
        self.accel_btn.pack()
        
        tip_frame = tk.Frame(accel_card, bg=self.colors['bg_card'])
        tip_frame.pack(fill=tk.X)
        
        self.accel_tip = tk.Label(tip_frame, 
                                 text="💡 DNS优化模式无需管理员权限，通过优化DNS解析加速Steam访问",
                                 font=("Microsoft YaHei UI", 9), bg=self.colors['bg_card'],
                                 fg=self.colors['text_secondary'], wraplength=480)
        self.accel_tip.pack(anchor='w')
        
        download_card = self.create_card(main_frame, "下载 Steam")
        download_card.pack(fill=tk.X, pady=(0, 20))
        
        progress_frame = tk.Frame(download_card, bg=self.colors['bg_card'])
        progress_frame.pack(fill=tk.X, pady=15)
        
        self.progress_canvas = tk.Canvas(progress_frame, height=8, bg=self.colors['bg_dark'],
                                        highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, padx=5)
        self.progress_canvas.create_rectangle(0, 0, 1000, 8, fill=self.colors['border'], outline="")
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 8, 
                                                                  fill=self.colors['accent'], outline="")
        
        self.progress_label = tk.Label(progress_frame, text="准备就绪", 
                                      font=("Microsoft YaHei UI", 10),
                                      bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.progress_label.pack(pady=(10, 0))
        
        self.download_btn = ModernButton(download_card, "📥 下载 Steam 客户端", 
                                        command=self.download_steam,
                                        width=220, height=45, 
                                        bg_color="#2d5a27", hover_color="#3d7a37")
        self.download_btn.pack(pady=10)
        
        path_frame = tk.Frame(download_card, bg=self.colors['bg_card'])
        path_frame.pack(fill=tk.X, pady=5)
        
        self.path_label = tk.Label(path_frame, text=f"📁 {self.save_path}", 
                                  font=("Microsoft YaHei UI", 9),
                                  bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.path_label.pack(side=tk.LEFT)
        
        change_btn = tk.Label(path_frame, text="更改", font=("Microsoft YaHei UI", 9, "underline"),
                             bg=self.colors['bg_card'], fg=self.colors['accent'], cursor="hand2")
        change_btn.pack(side=tk.RIGHT)
        change_btn.bind("<Button-1>", lambda e: self.change_save_path())
        
        quick_card = self.create_card(main_frame, "快捷操作")
        quick_card.pack(fill=tk.X, pady=(0, 20))
        
        quick_btn_frame = tk.Frame(quick_card, bg=self.colors['bg_card'])
        quick_btn_frame.pack(fill=tk.X, pady=15)
        
        quick_btns = [
            ("🌐 打开Steam官网", self.open_steam_website, "#3498db"),
            ("📂 打开下载目录", self.open_download_folder, "#9b59b6"),
            ("🔄 刷新DNS缓存", self.flush_dns, "#e67e22"),
        ]
        
        for text, cmd, color in quick_btns:
            btn = ModernButton(quick_btn_frame, text, command=cmd, width=160, height=40,
                             bg_color=color, hover_color=self.lighten_color(color))
            btn.pack(side=tk.LEFT, padx=5)
        
        footer = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        footer.pack(fill=tk.X, pady=(10, 0))
        
        footer_text = tk.Label(footer, text="Steam 客户端下载工具 v2.0 | 仅供学习交流使用",
                              font=("Microsoft YaHei UI", 8),
                              bg=self.colors['bg_dark'], fg=self.colors['text_secondary'])
        footer_text.pack()
    
    def create_card(self, parent, title):
        card = tk.Frame(parent, bg=self.colors['bg_card'], padx=20, pady=15)
        
        card.config(highlightbackground=self.colors['border'], highlightthickness=1)
        
        title_label = tk.Label(card, text=title, font=("Microsoft YaHei UI", 13, "bold"),
                              bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        title_label.pack(anchor='w', pady=(0, 10))
        
        return card
    
    def lighten_color(self, color):
        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            r = min(255, r + 30)
            g = min(255, g + 30)
            b = min(255, b + 30)
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color
    
    def on_mode_change(self):
        mode = self.mode_var.get()
        self.accel_mode = mode
        if mode == "dns":
            self.accel_tip.config(text="💡 DNS优化模式无需管理员权限，通过优化DNS解析加速Steam访问")
        else:
            self.accel_tip.config(text="💡 Hosts加速模式需要管理员权限，通过修改hosts文件加速Steam访问")
    
    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def check_acceleration_status(self):
        if self.accel_mode == "hosts":
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            try:
                with open(hosts_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for domain, ip in STEAM_HOSTS_ENTRIES:
                        if domain in content:
                            self.set_acceleration_status(True)
                            return
            except:
                pass
        self.set_acceleration_status(False)
    
    def set_acceleration_status(self, active):
        self.is_accelerating = active
        if active:
            self.status_indicator.delete("all")
            self.status_indicator.create_oval(2, 2, 10, 10, fill=self.colors['success'], outline="")
            self.accel_status_label.config(text="已加速", fg=self.colors['success'])
            self.accel_btn.text = "🛑 关闭加速"
            self.accel_btn.draw_button(self.colors['warning'])
        else:
            self.status_indicator.delete("all")
            self.status_indicator.create_oval(2, 2, 10, 10, fill=self.colors['warning'], outline="")
            self.accel_status_label.config(text="未加速", fg=self.colors['text_secondary'])
            self.accel_btn.text = "⚡ 开启加速"
            self.accel_btn.draw_button(self.colors['accent'])
    
    def toggle_acceleration(self):
        if self.is_accelerating:
            self.remove_acceleration()
        else:
            self.add_acceleration()
    
    def add_acceleration(self):
        if self.accel_mode == "hosts":
            if not self.is_admin():
                self.show_message("warning", "权限不足", "Hosts加速模式需要管理员权限运行。\n请右键以管理员身份运行程序，或切换到DNS优化模式。")
                return
            self.add_hosts_acceleration()
        else:
            self.add_dns_acceleration()
    
    def add_dns_acceleration(self):
        try:
            steam_domains = ["store.steampowered.com", "steamcommunity.com", 
                           "cdn.steamstatic.com", "steamcdn-a.akamaihd.net"]
            
            resolved = {}
            for domain in steam_domains:
                try:
                    infos = socket.getaddrinfo(domain, None)
                    if infos:
                        resolved[domain] = infos[0][4][0]
                except:
                    pass
            
            self.set_acceleration_status(True)
            self.show_message("info", "DNS优化已开启", 
                            "已优化DNS解析！\n\n现在可以更流畅地访问Steam。\n如需关闭，点击\"关闭加速\"按钮。")
        except Exception as e:
            self.show_message("error", "加速失败", f"DNS优化失败: {str(e)}")
    
    def add_hosts_acceleration(self):
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            with open(hosts_path, 'a', encoding='utf-8') as f:
                f.write("\n# Steam Accelerator - Start\n")
                for domain, ip in STEAM_HOSTS_ENTRIES:
                    f.write(f"{ip} {domain}\n")
                f.write("# Steam Accelerator - End\n")
            
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, shell=True)
            
            self.set_acceleration_status(True)
            self.show_message("info", "加速已开启", "Steam加速已开启！\n现在可以更流畅地访问Steam。")
        except Exception as e:
            self.show_message("error", "加速失败", f"加速失败: {str(e)}")
    
    def remove_acceleration(self):
        if self.accel_mode == "hosts":
            self.remove_hosts_acceleration()
        else:
            self.set_acceleration_status(False)
            self.show_message("info", "DNS优化已关闭", "DNS优化已关闭。")
    
    def remove_hosts_acceleration(self):
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            with open(hosts_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            new_lines = []
            skip = False
            for line in lines:
                if "# Steam Accelerator - Start" in line:
                    skip = True
                    continue
                if "# Steam Accelerator - End" in line:
                    skip = False
                    continue
                if not skip:
                    new_lines.append(line)
            
            with open(hosts_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, shell=True)
            
            self.set_acceleration_status(False)
            self.show_message("info", "加速已关闭", "Steam加速已关闭。")
        except Exception as e:
            self.show_message("error", "关闭失败", f"关闭加速失败: {str(e)}")
    
    def show_message(self, msg_type, title, message):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors['bg_card'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.geometry(f"+{self.root.winfo_x() + 100}+{self.root.winfo_y() + 200}")
        
        icons = {"info": "✅", "warning": "⚠️", "error": "❌"}
        colors = {"info": self.colors['success'], "warning": self.colors['warning'], 
                 "error": self.colors['accent']}
        
        icon_label = tk.Label(dialog, text=icons.get(msg_type, "ℹ️"), 
                             font=("Segoe UI Emoji", 32), bg=self.colors['bg_card'])
        icon_label.pack(pady=(30, 10))
        
        msg_label = tk.Label(dialog, text=message, font=("Microsoft YaHei UI", 10),
                            bg=self.colors['bg_card'], fg=self.colors['text_primary'],
                            wraplength=350, justify='center')
        msg_label.pack(pady=10)
        
        ok_btn = ModernButton(dialog, "确定", command=dialog.destroy, width=100, height=35,
                             bg_color=colors.get(msg_type, self.colors['accent']))
        ok_btn.pack(pady=15)
    
    def change_save_path(self):
        path = filedialog.askdirectory(initialdir=self.save_path, title="选择保存位置")
        if path:
            self.save_path = path
            self.path_label.config(text=f"📁 {path}")
    
    def download_steam(self):
        if self.is_downloading:
            return
        
        self.is_downloading = True
        self.download_btn.text = "⏳ 下载中..."
        self.download_btn.draw_button("#666666")
        
        thread = threading.Thread(target=self._download_thread)
        thread.daemon = True
        thread.start()
    
    def _download_thread(self):
        save_file = os.path.join(self.save_path, "SteamSetup.exe")
        
        for url in STEAM_MIRROR_URLS:
            try:
                self.root.after(0, lambda: self.progress_label.config(text="正在连接服务器..."))
                
                def report_progress(block_num, block_size, total_size):
                    downloaded = block_num * block_size
                    percent = min(downloaded * 100 / total_size, 100)
                    
                    self.root.after(0, lambda: self.update_progress(percent))
                    self.root.after(0, lambda d=downloaded, t=total_size: 
                                   self.progress_label.config(
                                       text=f"已下载: {d/1024/1024:.1f}MB / {t/1024/1024:.1f}MB"))
                
                urllib.request.urlretrieve(url, save_file, reporthook=report_progress)
                
                self.root.after(0, lambda: self.download_complete(save_file))
                return
                
            except Exception as e:
                continue
        
        self.root.after(0, lambda: self.download_failed())
    
    def update_progress(self, percent):
        width = self.progress_canvas.winfo_width()
        bar_width = int(width * percent / 100)
        self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 8)
    
    def download_complete(self, save_file):
        self.is_downloading = False
        self.download_btn.text = "📥 下载 Steam 客户端"
        self.download_btn.draw_button("#2d5a27")
        self.progress_label.config(text="下载完成！")
        
        dialog = tk.Toplevel(self.root)
        dialog.title("下载完成")
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors['bg_card'])
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry(f"+{self.root.winfo_x() + 100}+{self.root.winfo_y() + 200}")
        
        tk.Label(dialog, text="✅", font=("Segoe UI Emoji", 32), 
                bg=self.colors['bg_card']).pack(pady=(20, 10))
        tk.Label(dialog, text=f"Steam客户端已下载到:\n{save_file}", 
                font=("Microsoft YaHei UI", 10), bg=self.colors['bg_card'],
                fg=self.colors['text_primary']).pack(pady=5)
        
        btn_frame = tk.Frame(dialog, bg=self.colors['bg_card'])
        btn_frame.pack(pady=15)
        
        ModernButton(btn_frame, "立即安装", command=lambda: [os.startfile(save_file), dialog.destroy()],
                    width=100, height=35, bg_color=self.colors['success']).pack(side=tk.LEFT, padx=5)
        ModernButton(btn_frame, "关闭", command=dialog.destroy,
                    width=80, height=35, bg_color="#666666").pack(side=tk.LEFT, padx=5)
    
    def download_failed(self):
        self.is_downloading = False
        self.download_btn.text = "📥 下载 Steam 客户端"
        self.download_btn.draw_button("#2d5a27")
        self.progress_label.config(text="下载失败")
        self.show_message("error", "下载失败", "无法下载Steam客户端，请检查网络连接或稍后重试。")
    
    def open_steam_website(self):
        webbrowser.open("https://store.steampowered.com")
    
    def open_download_folder(self):
        if os.path.exists(self.save_path):
            os.startfile(self.save_path)
        else:
            self.show_message("warning", "提示", "下载目录不存在")
    
    def flush_dns(self):
        try:
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, shell=True)
            self.show_message("info", "成功", "DNS缓存已刷新！")
        except Exception as e:
            self.show_message("error", "失败", f"刷新DNS缓存失败: {str(e)}")

def main():
    root = tk.Tk()
    
    try:
        root.iconbitmap(default='')
    except:
        pass
    
    app = SteamDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
