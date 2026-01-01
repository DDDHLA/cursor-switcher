#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import cursor_manager
import threading
import sys
import os
from pathlib import Path

class CursorSwitcherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cursor 账号切换助手")
        self.root.geometry("500x600")
        
        # 设置样式
        style = ttk.Style()
        style.configure("TButton", padding=5)
        
        self.create_widgets()
        self.refresh_status()
        self.refresh_list()

    def create_widgets(self):
        # 顶部状态栏
        status_frame = ttk.LabelFrame(self.root, text="当前状态", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.current_profile_label = ttk.Label(status_frame, text="激活配置文件: 加载中...")
        self.current_profile_label.pack(anchor="w")
        
        self.current_email_label = ttk.Label(status_frame, text="当前登录邮箱: 加载中...")
        self.current_email_label.pack(anchor="w")

        # 列表框
        list_frame = ttk.LabelFrame(self.root, text="账号列表", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.profile_listbox = tk.Listbox(list_frame, font=("Arial", 12))
        self.profile_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.profile_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.profile_listbox.config(yscrollcommand=scrollbar.set)

        # 按钮区
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x")

        # 第一行按钮
        row1 = ttk.Frame(btn_frame)
        row1.pack(fill="x", pady=2)
        ttk.Button(row1, text="切换到选中账号", command=self.on_switch).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(row1, text="保存当前账号", command=self.on_save).pack(side="left", fill="x", expand=True, padx=2)

        # 第二行按钮
        row2 = ttk.Frame(btn_frame)
        row2.pack(fill="x", pady=2)
        ttk.Button(row2, text="批量导出", command=self.on_export).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(row2, text="批量导入", command=self.on_import).pack(side="left", fill="x", expand=True, padx=2)

        # 第三行按钮
        row3 = ttk.Frame(btn_frame)
        row3.pack(fill="x", pady=2)
        ttk.Button(row3, text="重置当前账号", command=self.on_reset).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(row3, text="刷新列表", command=self.refresh_list).pack(side="left", fill="x", expand=True, padx=2)

        # 日志输出
        log_frame = ttk.LabelFrame(self.root, text="运行日志", padding=5)
        log_frame.pack(fill="x", padx=10, pady=5)
        self.log_text = tk.Text(log_frame, height=6, state="disabled", font=("Courier", 10))
        self.log_text.pack(fill="x")

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def refresh_status(self):
        current = cursor_manager.get_current_profile_name()
        email = cursor_manager.get_current_account_email(cursor_manager.STATE_DB)
        self.current_profile_label.config(text=f"激活配置文件: {current if current else '未命名 (外部设置)'}")
        self.current_email_label.config(text=f"当前登录邮箱: {email}")

    def refresh_list(self):
        self.profile_listbox.delete(0, "end")
        if not cursor_manager.PROFILES_DIR.exists():
            return
        
        current = cursor_manager.get_current_profile_name()
        profiles = [d for d in cursor_manager.PROFILES_DIR.iterdir() if d.is_dir()]
        for p in profiles:
            email = cursor_manager.get_current_account_email(p / "state.vscdb")
            display_name = f"{'* ' if p.name == current else '  '}{p.name} ({email})"
            self.profile_listbox.insert("end", display_name)

    def on_switch(self):
        selection = self.profile_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个账号")
            return
        
        item = self.profile_listbox.get(selection[0])
        name = item.strip().split(" (")[0].replace("* ", "")
        
        def task():
            self.log(f"正在切换到 {name}...")
            cursor_manager.switch_profile(name)
            self.root.after(0, self.finish_action, f"成功切换到 {name}")

        threading.Thread(target=task).start()

    def on_save(self):
        name = tk.simpledialog.askstring("保存账号", "请输入配置名称:")
        if not name:
            return
        
        def task():
            self.log(f"正在保存当前账号为 {name}...")
            cursor_manager.save_profile(name)
            self.root.after(0, self.finish_action, f"成功保存为 {name}")

        threading.Thread(target=task).start()

    def on_reset(self):
        if not messagebox.askyesno("确认", "确定要重置当前账号吗？这会清除登录状态并生成新的机器 ID。"):
            return
        
        def task():
            self.log("正在重置当前账号...")
            cursor_manager.reset_current()
            cursor_manager.open_cursor()
            self.root.after(0, self.finish_action, "重置完成")

        threading.Thread(target=task).start()

    def on_export(self):
        path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("Zip files", "*.zip")])
        if not path:
            return
        
        if cursor_manager.export_profiles(path):
            messagebox.showinfo("成功", "导出成功")
            self.log(f"已导出到: {path}")
        else:
            messagebox.showerror("错误", "导出失败")

    def on_import(self):
        path = filedialog.askopenfilename(filetypes=[("Zip files", "*.zip")])
        if not path:
            return
        
        if cursor_manager.import_profiles(path):
            messagebox.showinfo("成功", "导入成功")
            self.refresh_list()
            self.log(f"已从 {path} 导入")
        else:
            messagebox.showerror("错误", "导入失败")

    def finish_action(self, msg):
        self.log(msg)
        self.refresh_status()
        self.refresh_list()
        messagebox.showinfo("完成", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = CursorSwitcherGUI(root)
    root.mainloop()
