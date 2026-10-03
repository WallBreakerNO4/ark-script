#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import subprocess
import time
import sys
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

# 配置URL
# URL = "http://10.114.2.1:7070/stats"
URL = os.getenv("URL", "http://10.10.10.3:7070/stats")
# 全局变量用于控制 dry-run 模式
DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"
# adb 设备地址
ADB_DEVICE = os.getenv("ADB_DEVICE", "192.168.10.103:5555")
# 启动前等待时间（秒）
STARTUP_WAIT = int(os.getenv("STARTUP_WAIT", 60))
# Telegram 配置
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
# 明日方舟包名
ARKNIGHTS_PACKAGE = os.getenv("ARKNIGHTS_PACKAGE", "com.hypergryph.arknights")
ARKNIGHTS_PACKAGE_BILIBILI = os.getenv("ARKNIGHTS_PACKAGE_BILIBILI", "com.hypergryph.arknights.bilibili")
ENDFIELD_PACKAGE = "com.hypergryph.endfield"

ARKNIGHTS_PACKAGES = [pkg for pkg in (ARKNIGHTS_PACKAGE, ARKNIGHTS_PACKAGE_BILIBILI, ENDFIELD_PACKAGE) if pkg]
# 通知消息
STARTUP_MESSAGES = {
    "maa": os.getenv("MSG_STARTUP", "即将开始运行 MAA！请立刻停止游玩明日方舟！"),
    "maaend": "即将开始运行MaaEnd！请立刻停止游玩终末地！",
}


def check_status():
    """从/stats获取状态"""
    try:
        # 假设是本地服务，如果不是请修改URL
        url = URL
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            status = response.json().get("status", -1)
            print(f"Status obtained: {status}")
            return status
        else:
            print(f"Failed to get status. Status code: {response.status_code}")
            return -1

    except requests.exceptions.RequestException as e:
        print(f"Failed to get status. Error: {e}")
        return -1
    except Exception as e:
        print(f"Error getting status: {e}")
        return -1


def restart_computer():
    """重启电脑"""
    try:
        print("Restarting computer...")
        if DRY_RUN:
            print("[DRY RUN] Would restart computer, but dry-run mode is enabled")
            return True

        # 在 Linux 系统上使用 systemctl 重启
        if os.name == "posix":
            subprocess.run(["sudo", "reboot"], check=True)
        # 在 Windows 系统上使用 shutdown 命令
        elif os.name == "nt":
            subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
        else:
            print("Unsupported operating system for restart")
            return False
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart computer: {e}")
        return False
    except Exception as e:
        print(f"Error restarting computer: {e}")
        return False


def send_telegram_message_with_content(message_content):
    """发送指定内容的 Telegram 消息"""
    # 从环境变量读取 bot token 和 chat ID
    BOT_TOKEN = TELEGRAM_BOT_TOKEN
    CHAT_ID = TELEGRAM_CHAT_ID

    print(f"[DEBUG] Attempting to send message: '{message_content}' to chat {CHAT_ID}")
    print(f"[DEBUG] DRY_RUN mode: {DRY_RUN} (但 Telegram 消息仍会发送)")

    # 构建 API URL
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    print(f"[DEBUG] Using Telegram API URL: {url[:50]}...")

    # 准备请求数据
    data = {"chat_id": CHAT_ID, "text": message_content}
    print(
        f"[DEBUG] Request data: chat_id={CHAT_ID}, message_length={len(message_content)}"
    )

    try:
        print("[DEBUG] Sending POST request to Telegram API...")
        # 发送 POST 请求
        response = requests.post(url, data=data, timeout=10)

        print(f"[DEBUG] Response status code: {response.status_code}")
        print(f"[DEBUG] Response headers: {dict(response.headers)}")

        try:
            response_json = response.json()
            print(f"[DEBUG] Response body: {response_json}")
        except:
            print(f"[DEBUG] Response text: {response.text}")

        # 检查返回状态
        if response.status_code == 200:
            # 进一步检查 Telegram API 的 ok 字段
            try:
                response_data = response.json()
                if response_data.get("ok", False):
                    print(
                        "[SUCCESS] Message sent successfully - Telegram API confirmed delivery."
                    )
                    return True
                else:
                    print(f"[ERROR] Telegram API returned ok=false: {response_data}")
                    return False
            except Exception as e:
                print(f"[WARNING] Could not parse response JSON, but status 200: {e}")
                print("Message sent successfully (assuming success due to status 200).")
                return True
        else:
            print(
                f"[ERROR] Failed to send message. Status code: {response.status_code}"
            )
            print(f"[ERROR] Response: {response.text}")
            return False

    except requests.exceptions.Timeout as e:
        print(f"[ERROR] Request timeout: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection error: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False


def send_telegram_message(target):
    """根据启动目标发送 Telegram 消息"""
    return send_telegram_message_with_content(STARTUP_MESSAGES[target])


# def connect_adb_and_stop_game():
#     return True


def connect_adb_and_stop_game():
    """连接 ADB 并强制停止明日方舟"""
    if DRY_RUN:
        print(f"[DRY RUN] Would connect to ADB device {ADB_DEVICE}")
        for pkg in ARKNIGHTS_PACKAGES:
            print(f"[DRY RUN] Would stop Arknights app ({pkg})")
        return True

    try:
        # 连接 ADB 设备
        print(f"Connecting to ADB device {ADB_DEVICE}...")
        connect_result = subprocess.run(
            ["adb", "connect", ADB_DEVICE],
            capture_output=True,
            text=True,
            timeout=30,
        )

        print(f"ADB connect return code: {connect_result.returncode}")
        print(f"ADB connect stdout: {connect_result.stdout}")
        print(f"ADB connect stderr: {connect_result.stderr}")

        if connect_result.returncode != 0:
            print(f"ADB connection failed: {connect_result.stderr}")
            return False

        # 验证连接
        devices_result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        print(f"Connected devices:\n{devices_result.stdout}")

        # 强制停止所有明日方舟应用
        all_success = True
        for pkg in ARKNIGHTS_PACKAGES:
            print(f"Stopping Arknights app ({pkg})...")
            stop_result = subprocess.run(
                ["adb", "-s", ADB_DEVICE, "shell", "am", "force-stop", pkg],
                capture_output=True,
                text=True,
                timeout=30,
            )

            print(f"Force-stop return code: {stop_result.returncode}")
            print(f"Force-stop stdout: {stop_result.stdout}")
            print(f"Force-stop stderr: {stop_result.stderr}")

            if stop_result.returncode == 0:
                print(f"Arknights app ({pkg}) stopped successfully.")
            else:
                print(f"Failed to stop Arknights app ({pkg}): {stop_result.stderr}")
                all_success = False

        return all_success

    except subprocess.TimeoutExpired as e:
        print(f"ADB command timed out: {e}")
        return False
    except FileNotFoundError:
        print("ADB command not found. Please make sure ADB is installed and in PATH.")
        return False
    except Exception as e:
        print(f"Error executing ADB commands: {e}")
        return False


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="MAA message script with dry-run support"
    )
    parser.add_argument(
        "--target",
        choices=tuple(STARTUP_MESSAGES),
        default="maa",
        help="选择 Telegram 启动通知类型（默认：maa）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="启用 dry-run 模式，只显示将要执行的操作而不实际执行",
    )
    return parser.parse_args()


def main():
    """主函数"""
    global DRY_RUN

    # 解析命令行参数
    args = parse_arguments()
    DRY_RUN = args.dry_run

    if DRY_RUN:
        print("=== DRY RUN MODE ENABLED ===")
        print("No actual operations will be performed")
        print("=" * 32)

    print("Starting MAA message script...")

    # 首先检查状态
    status = check_status()

    if status == 0:
        # 状态0是一次性重启信号，读取后会自动重置为1
        print("Status is 0, restarting computer immediately...")
        restart_success = restart_computer()
        if restart_success:
            print("Computer restart initiated.")
            sys.exit(0)
        else:
            print("Failed to restart computer.")
            sys.exit(1)
    elif status == 1:
        # 状态为1，继续原有脚本功能
        print("Status is 1, continuing with normal script execution...")

        # 发送 Telegram 消息
        message_sent = send_telegram_message(args.target)

        if message_sent:
            if DRY_RUN:
                print(f"[DRY RUN] Would wait {STARTUP_WAIT} seconds...")
            else:
                print(f"Waiting {STARTUP_WAIT} seconds...")
                time.sleep(STARTUP_WAIT)

            # 连接 ADB 并停止游戏
            adb_success = connect_adb_and_stop_game()

            if adb_success:
                print("Script completed successfully.")
                sys.exit(0)
            else:
                print("Script completed with ADB errors.")
                sys.exit(1)
        else:
            print("Script failed to send message.")
            sys.exit(1)
    else:
        # 状态获取失败或者不是预期值
        print(f"Unexpected status: {status}. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
