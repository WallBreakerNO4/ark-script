#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import subprocess
import time
import sys
import os
import argparse

# 配置URL
URL = "http://10.114.2.1:7070/stats"
# 全局变量用于控制 dry-run 模式
DRY_RUN = False


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
        print("Status is 0, restarting computer...")
        
        # 在重启前发送Telegram消息
        print("Sending restart notification message...")
        message_sent = send_restart_message()
        if message_sent:
            print("Restart notification sent successfully.")
        else:
            print("Failed to send restart notification, but proceeding with restart...")
        
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
    # 设置 bot token 和 chat ID
    BOT_TOKEN = "7055892526:AAGOoW15bzU7V08fMVrMW7MMYx3cyVzh22Q"
    CHAT_ID = "974603980"

    print(f"[DEBUG] Attempting to send message: '{message_content}' to chat {CHAT_ID}")
    print(f"[DEBUG] DRY_RUN mode: {DRY_RUN} (但 Telegram 消息仍会发送)")

    # 构建 API URL
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    print(f"[DEBUG] Using Telegram API URL: {url[:50]}...")

    # 准备请求数据
    data = {"chat_id": CHAT_ID, "text": message_content}
    print(f"[DEBUG] Request data: chat_id={CHAT_ID}, message_length={len(message_content)}")

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
                if response_data.get('ok', False):
                    print("[SUCCESS] Message sent successfully - Telegram API confirmed delivery.")
                    return True
                else:
                    print(f"[ERROR] Telegram API returned ok=false: {response_data}")
                    return False
            except Exception as e:
                print(f"[WARNING] Could not parse response JSON, but status 200: {e}")
                print("Message sent successfully (assuming success due to status 200).")
                return True
        else:
            print(f"[ERROR] Failed to send message. Status code: {response.status_code}")
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


def send_telegram_message():
    """发送 Telegram 消息（保持原有函数兼容性）"""
    return send_telegram_message_with_content("即将开始运行MAA！请立刻停止游玩明日方舟！")


def send_restart_message():
    """发送重启消息"""
    return send_telegram_message_with_content("MAA将跳过此次运行")


def connect_adb_and_stop_game():
    return True
# def connect_adb_and_stop_game():
#     """连接 ADB 并强制停止明日方舟"""
#     if DRY_RUN:
#         print("[DRY RUN] Would connect to ADB device 192.168.20.124:5555")
#         print("[DRY RUN] Would stop Arknights app (com.hypergryph.arknights.bilibili)")
#         return True
    
#     try:
#         # 连接 ADB 设备
#         print("Connecting to ADB device...")
#         connect_result = subprocess.run(
#             ["adb", "connect", "192.168.20.124:5555"],
#             capture_output=True,
#             text=True,
#             timeout=30,
#         )

#         if connect_result.returncode == 0:
#             print("ADB connected successfully.")
#         else:
#             print(f"ADB connection failed: {connect_result.stderr}")
#             return False

#         # 强制停止明日方舟应用
#         print("Stopping Arknights app...")
#         stop_result = subprocess.run(
#             ["adb", "shell", "am", "force-stop", "com.hypergryph.arknights.bilibili"],
#             capture_output=True,
#             text=True,
#             timeout=30,
#         )

#         if stop_result.returncode == 0:
#             print("Arknights app stopped successfully.")
#             return True
#         else:
#             print(f"Failed to stop Arknights app: {stop_result.stderr}")
#             return False

#     except subprocess.TimeoutExpired:
#         print("ADB command timed out.")
#         return False
#     except FileNotFoundError:
#         print("ADB command not found. Please make sure ADB is installed and in PATH.")
#         return False
#     except Exception as e:
#         print(f"Error executing ADB commands: {e}")
#         return False


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="MAA message script with dry-run support")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="启用 dry-run 模式，只显示将要执行的操作而不实际执行"
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
        # 状态为0，重启电脑
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
        message_sent = send_telegram_message()

        if message_sent:
            if DRY_RUN:
                print("[DRY RUN] Would wait 60 seconds...")
            else:
                print("Waiting 60 seconds...")
                time.sleep(60)

            # 60秒后再次检查状态
            print("Checking status again after 60 seconds...")
            new_status = check_status()
            
            if new_status == 0:
                # 新状态为0，重启电脑
                print("Status changed to 0 during wait, restarting computer...")
                restart_success = restart_computer()
                if restart_success:
                    print("Computer restart initiated.")
                    sys.exit(0)
                else:
                    print("Failed to restart computer.")
                    sys.exit(1)
            elif new_status == 1:
                # 新状态仍为1，继续执行ADB操作
                print("Status remains 1, continuing with ADB operations...")
                # 连接 ADB 并停止游戏
                adb_success = connect_adb_and_stop_game()

                if adb_success:
                    print("Script completed successfully.")
                    sys.exit(0)
                else:
                    print("Script completed with ADB errors.")
                    sys.exit(1)
            else:
                # 新状态获取失败或者不是预期值
                print(f"Unexpected status after wait: {new_status}. Continuing with ADB operations as fallback...")
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
