#!/usr/bin/env python3
"""
主权心跳同步器 (Sovereign Pulse Sync)
用途：生成心跳令牌，更新 sovereignty.json，并自动推送到 GitHub。
"""

import hashlib
import hmac
import time
import platform
import json
import os
from getpass import getpass

# ==================== 锚定信息 ====================
THEORY_BODY_HASH = "ca4cca1515bf4a5377932fec816fc814f7d0cb55eace414ad5be421ce39997a2"
STATIC_FINGERPRINT = "c6bd8f4623aded6e759344d1de4511a21c903d4e678d4bea65f547b18f1221fd38c7b23f627d10359908d71615c8d2cafabb6010298a416feabdbd1d5e7851c1"

# ==================== 安全参数 ====================
PBKDF2_ITERATIONS = 600_000
SALT = b'Metatheory-Sovereignty-Salt-v1'
HASH_ALGORITHM = 'sha512'

# ==================== 密钥派生 ====================
def derive_key(password: str) -> bytes:
    return hashlib.pbkdf2_hmac(HASH_ALGORITHM,
                               password.encode('utf-8'),
                               SALT, PBKDF2_ITERATIONS)

# ==================== 心跳生成 ====================
def generate_heartbeat(password: str) -> str:
    key = derive_key(password)
    sys_info = platform.node() + platform.processor() + platform.system()
    timestamp = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    payload = sys_info + THEORY_BODY_HASH + timestamp
    mac = hmac.new(key, payload.encode('utf-8'), HASH_ALGORITHM).hexdigest()
    return f"SYNC_PULSE_{timestamp}_{mac[:16]}", timestamp, sys_info

# ==================== 同步到 GitHub ====================
def sync_to_github(password: str, repo_path: str):
    token, timestamp, sys_info = generate_heartbeat(password)
    
    sovereignty_data = {
        "last_heartbeat": token,
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "machine_fingerprint": sys_info
    }
    filepath = os.path.join(repo_path, "sovereignty.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(sovereignty_data, f, ensure_ascii=False, indent=2)
    
    os.chdir(repo_path)
    os.system("git add sovereignty.json")
    os.system(f'git commit -m "心跳同步 {timestamp}"')
    os.system("git push origin main")
    
    print(f"心跳已同步: {token}")

if __name__ == "__main__":
    REPO_PATH = os.getcwd()  # 直接使用当前目录
    
    password = os.environ.get("SOVEREIGN_PASSWORD")
    if not password:
        password = getpass("请输入主权密码: ")
    
    key = derive_key(password)
    test_fp = hmac.new(key, THEORY_BODY_HASH.encode('utf-8'), HASH_ALGORITHM).hexdigest()
    if test_fp != STATIC_FINGERPRINT:
        print("密码错误：与静态主权指纹不匹配。同步中断。")
        exit(1)
    
    sync_to_github(password, REPO_PATH)