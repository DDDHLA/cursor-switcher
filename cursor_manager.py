#!/usr/bin/env python3
import os
import shutil
import json
import sqlite3
import sys
import subprocess
import datetime
from pathlib import Path

# 配置路径
CURSOR_DB_DIR = Path.home() / "Library/Application Support/Cursor/User/globalStorage"
STORAGE_JSON = CURSOR_DB_DIR / "storage.json"
STATE_DB = CURSOR_DB_DIR / "state.vscdb"
PROFILES_DIR = Path.home() / ".cursor_profiles"

def kill_cursor():
    """优雅地关闭 Cursor 进程"""
    print("正在尝试关闭 Cursor...")
    try:
        # 使用 AppleScript 尝试优雅退出，避免弹出崩溃窗口
        subprocess.run(["osascript", "-e", 'quit app "Cursor"'], check=False, capture_output=True)
        
        # 等待几秒让它退出
        import time
        for _ in range(5):
            result = subprocess.run(["pgrep", "-f", "Cursor"], capture_output=True)
            if result.returncode != 0:
                print("Cursor 已成功关闭。")
                return
            time.sleep(0.5)
        
        # 如果还没关掉，再强制关闭
        print("Cursor 未响应，正在强制关闭...")
        subprocess.run(["pkill", "-9", "-f", "Cursor"], check=False)
        time.sleep(1)
    except Exception as e:
        print(f"关闭 Cursor 时出错: {e}")

def get_current_account_email(db_path):
    """从数据库中获取当前登录的邮箱"""
    if not db_path.exists():
        return "Unknown"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/cachedEmail'")
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception:
        pass
    return "Unknown"

def list_profiles():
    """列出所有保存的账号"""
    if not PROFILES_DIR.exists():
        print("尚未创建任何账号配置文件。")
        return

    profiles = [d for d in PROFILES_DIR.iterdir() if d.is_dir()]
    if not profiles:
        print("尚未创建任何账号配置文件。")
        return

    current = get_current_profile_name()
    print("\n已保存的账号配置文件:")
    for p in profiles:
        status = "*" if p.name == current else " "
        email = get_current_account_email(p / "state.vscdb")
        print(f"{status} {p.name} ({email})")
    print("\n* 表示当前正在使用的配置文件\n")

def get_current_profile_name():
    """获取当前激活的配置文件名称"""
    current_file = PROFILES_DIR / "current_profile.txt"
    if current_file.exists():
        return current_file.read_text().strip()
    return None

def save_profile(name):
    """保存当前账号为新配置文件"""
    if not STORAGE_JSON.exists() or not STATE_DB.exists():
        print("错误: 找不到 Cursor 的配置文件，请确保已安装并运行过 Cursor。")
        return

    # 先尝试关闭 Cursor 并清理 WAL，确保数据写入主数据库文件
    kill_cursor()
    for ext in ["-shm", "-wal"]:
        wal_file = CURSOR_DB_DIR / f"state.vscdb{ext}"
        if wal_file.exists():
            try:
                wal_file.unlink()
            except:
                pass

    profile_path = PROFILES_DIR / name
    profile_path.mkdir(parents=True, exist_ok=True)

    # 复制文件
    shutil.copy2(STORAGE_JSON, profile_path / "storage.json")
    shutil.copy2(STATE_DB, profile_path / "state.vscdb")
    
    # 记录当前配置文件名
    (PROFILES_DIR / "current_profile.txt").write_text(name)
    
    # 记录最后使用时间
    last_active_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    (profile_path / "last_active.txt").write_text(last_active_time)
    
    email = get_current_account_email(profile_path / "state.vscdb")
    print(f"成功将当前账号保存为配置文件: {name} ({email})")

def open_cursor():
    """打开 Cursor 应用"""
    print("正在重新打开 Cursor...")
    import time
    time.sleep(1) # 给系统一点缓冲时间
    try:
        # 使用 open 指令打开
        subprocess.Popen(["open", "-a", "Cursor"], start_new_session=True)
    except Exception as e:
        print(f"无法自动打开 Cursor: {e}")

def switch_profile(name):
    """切换到指定的配置文件，并自动执行重置"""
    profile_path = PROFILES_DIR / name
    if not profile_path.exists():
        print(f"错误: 配置文件 '{name}' 不存在。")
        return

    kill_cursor()

    # 备份当前状态（如果不在任何 profile 中）
    current = get_current_profile_name()
    if not current:
        print("检测到当前环境未保存，正在备份为 'backup_before_switch'...")
        save_profile("backup_before_switch")

    # 复制配置文件到 Cursor 目录
    shutil.copy2(profile_path / "storage.json", STORAGE_JSON)
    shutil.copy2(profile_path / "state.vscdb", STATE_DB)
    
    # 清理 WAL 文件以防止冲突
    for ext in ["-shm", "-wal"]:
        wal_file = CURSOR_DB_DIR / f"state.vscdb{ext}"
        if wal_file.exists():
            try:
                wal_file.unlink()
            except:
                pass

    # 更新当前配置文件记录
    (PROFILES_DIR / "current_profile.txt").write_text(name)
    
    # 记录最后使用时间
    last_active_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    (profile_path / "last_active.txt").write_text(last_active_time)
    
    # 自动执行重置逻辑 (仅重置机器 ID，保留登录信息)
    print(f"正在为账号 '{name}' 自动生成新的机器 ID...")
    reset_current(only_machine_id=True)
    
    email = get_current_account_email(STATE_DB)
    print(f"成功切换到账号: {name} ({email})")
    
    # 自动打开 Cursor
    open_cursor()

def export_profiles(export_path):
    """批量导出所有配置文件为 zip"""
    import zipfile
    if not PROFILES_DIR.exists():
        print("没有可导出的配置文件。")
        return False
    
    try:
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(PROFILES_DIR):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(PROFILES_DIR)
                    zipf.write(file_path, arcname)
        print(f"成功导出配置文件到: {export_path}")
        return True
    except Exception as e:
        print(f"导出失败: {e}")
        return False

def import_profiles(import_path):
    """从 zip 文件批量导入配置文件"""
    import zipfile
    if not Path(import_path).exists():
        print(f"错误: 找不到导入文件 {import_path}")
        return False
    
    try:
        with zipfile.ZipFile(import_path, 'r') as zipf:
            zipf.extractall(PROFILES_DIR)
        print(f"成功从 {import_path} 导入配置文件")
        return True
    except Exception as e:
        print(f"导入失败: {e}")
        return False

def get_current_status():
    """获取当前正在使用的账号信息"""
    current = get_current_profile_name()
    email = get_current_account_email(STATE_DB)
    print(f"\n当前状态:")
    print(f"  激活配置文件: {current if current else '未命名 (外部设置)'}")
    print(f"  当前登录邮箱: {email}")
    print("")

def reset_current(only_machine_id=False):
    """重置当前账号（清除登录状态并生成新的机器 ID）
    如果 only_machine_id 为 True，则只重置机器 ID，不清除登录信息
    """
    import uuid
    import hashlib
    import secrets

    kill_cursor()
    
    # 备份
    print("正在重置机器信息...")
    
    # 1. 重置 storage.json 中的机器 ID
    if STORAGE_JSON.exists():
        try:
            with open(STORAGE_JSON, 'r') as f:
                data = json.load(f)
            
            # 生成新的 ID
            new_id = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
            new_mac_id = hashlib.sha512(secrets.token_bytes(64)).hexdigest()
            new_dev_id = str(uuid.uuid4())
            
            data["telemetry.machineId"] = new_id
            data["telemetry.macMachineId"] = new_mac_id
            data["telemetry.devDeviceId"] = new_dev_id
            
            with open(STORAGE_JSON, 'w') as f:
                json.dump(data, f, indent=2)
            print("- 已生成新的机器 ID")
        except Exception as e:
            print(f"- 更新 storage.json 失败: {e}")

    # 2. 清除 state.vscdb 中的登录信息
    if not only_machine_id and STATE_DB.exists():
        try:
            conn = sqlite3.connect(STATE_DB)
            cursor = conn.cursor()
            keys_to_delete = [
                'cursorAuth/accessToken',
                'cursorAuth/refreshToken',
                'cursorAuth/cachedEmail',
                'cursorAuth/stripeMembershipType'
            ]
            for key in keys_to_delete:
                cursor.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
            conn.commit()
            conn.close()
            print("- 已清除登录 Token")
        except Exception as e:
            print(f"- 清除数据库信息失败: {e}")

    # 清理 WAL 文件
    for ext in ["-shm", "-wal"]:
        wal_file = CURSOR_DB_DIR / f"state.vscdb{ext}"
        if wal_file.exists():
            wal_file.unlink()

    if not only_machine_id:
        # 清除当前配置文件记录
        current_file = PROFILES_DIR / "current_profile.txt"
        if current_file.exists():
            current_file.unlink()
        print("重置完成。重新打开 Cursor 时将是未登录状态且拥有新的机器 ID。")
    else:
        print("机器 ID 重置完成。")

def print_usage():
    """打印帮助说明"""
    print("\n" + "="*50)
    print("Cursor 账号切换助手 - 可用指令:")
    print("  python3 cursor_manager.py list          - 列出所有账号")
    print("  python3 cursor_manager.py save <name>   - 保存当前账号")
    print("  python3 cursor_manager.py switch <name> - 切换到指定账号")
    print("  python3 cursor_manager.py status        - 查看当前状态")
    print("  python3 cursor_manager.py reset         - 重置当前账号 (登出并生成新 ID)")
    print("  python3 cursor_manager.py export <path> - 批量导出配置文件")
    print("  python3 cursor_manager.py import <path> - 批量导入配置文件")
    print("="*50 + "\n")

def list_profiles_json():
    """以 JSON 格式列出所有保存的账号"""
    if not PROFILES_DIR.exists():
        return []

    profiles = [d for d in PROFILES_DIR.iterdir() if d.is_dir()]
    current = get_current_profile_name()
    
    result = []
    for p in profiles:
        email = get_current_account_email(p / "state.vscdb")
        
        # 读取最后使用时间
        last_active = ""
        last_active_file = p / "last_active.txt"
        if last_active_file.exists():
            last_active = last_active_file.read_text().strip()
        else:
            # 如果没有记录文件，使用文件夹修改时间作为备选
            mtime = os.path.getmtime(p)
            last_active = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            # 顺便补写一下文件，防止下次还需要计算
            try:
                last_active_file.write_text(last_active)
            except:
                pass
            
        result.append({
            "name": p.name,
            "email": email,
            "is_current": p.name == current,
            "last_active": last_active
        })
    return result

def get_current_status_json():
    """获取当前状态的 JSON 格式"""
    current = get_current_profile_name()
    email = get_current_account_email(STATE_DB)
    return {
        "current_profile": current,
        "current_email": email
    }

def delete_profile(name):
    """删除指定的配置文件"""
    profile_path = PROFILES_DIR / name
    if profile_path.exists():
        try:
            shutil.rmtree(profile_path)
            # 如果删除的是当前记录的文件，清除记录
            current_file = PROFILES_DIR / "current_profile.txt"
            if current_file.exists() and current_file.read_text().strip() == name:
                current_file.unlink()
            print(f"成功删除配置文件: {name}")
            return True
        except Exception as e:
            print(f"删除失败: {e}")
            return False
    return False

def rename_profile(old_name, new_name):
    """重命名配置文件"""
    old_path = PROFILES_DIR / old_name
    new_path = PROFILES_DIR / new_name
    
    if not old_path.exists():
        print(f"错误: 配置文件 '{old_name}' 不存在")
        return False
    
    if new_path.exists():
        print(f"错误: 配置文件 '{new_name}' 已存在")
        return False
        
    try:
        # 重命名文件夹
        old_path.rename(new_path)
        
        # 如果重命名的是当前激活的账号，更新记录文件
        current_file = PROFILES_DIR / "current_profile.txt"
        if current_file.exists() and current_file.read_text().strip() == old_name:
            current_file.write_text(new_name)
            
        print(f"成功将 '{old_name}' 重命名为 '{new_name}'")
        return True
    except Exception as e:
        print(f"重命名失败: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    cmd = sys.argv[1]
    
    if cmd == "list_json":
        print(json.dumps(list_profiles_json()))
    elif cmd == "status_json":
        print(json.dumps(get_current_status_json()))
    elif cmd == "list":
        list_profiles()
    elif cmd == "save" and len(sys.argv) > 2:
        save_profile(sys.argv[2])
    elif cmd == "switch" and len(sys.argv) > 2:
        switch_profile(sys.argv[2])
    elif cmd == "status":
        get_current_status()
    elif cmd == "reset":
        reset_current()
        open_cursor()
    elif cmd == "export" and len(sys.argv) > 2:
        export_profiles(sys.argv[2])
    elif cmd == "import" and len(sys.argv) > 2:
        import_profiles(sys.argv[2])
    elif cmd == "delete" and len(sys.argv) > 2:
        delete_profile(sys.argv[2])
    elif cmd == "rename" and len(sys.argv) > 3:
        rename_profile(sys.argv[2], sys.argv[3])
    else:
        print(f"未知命令: {cmd}")

if __name__ == "__main__":
    main()
