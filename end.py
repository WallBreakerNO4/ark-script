#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import argparse
import os
from dotenv import load_dotenv

load_dotenv()

# 全局变量用于控制 dry-run 模式
DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"
# adb 设备地址
ADB_DEVICE = os.getenv("ADB_DEVICE", "192.168.10.103:5555")
# 明日方舟包名
ARKNIGHTS_PACKAGE = os.getenv("ARKNIGHTS_PACKAGE", "com.hypergryph.arknights")
ARKNIGHTS_PACKAGE_BILIBILI = os.getenv("ARKNIGHTS_PACKAGE_BILIBILI", "com.hypergryph.arknights.bilibili")
ENDFIELD_PACKAGE = "com.hypergryph.endfield"

ARKNIGHTS_PACKAGES = [pkg for pkg in (ARKNIGHTS_PACKAGE, ARKNIGHTS_PACKAGE_BILIBILI, ENDFIELD_PACKAGE) if pkg]


def kill_arknights():
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
        description="Kill Arknights app with dry-run support"
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

    print("Killing Arknights app...")

    # 直接杀死应用
    kill_success = kill_arknights()

    if kill_success:
        print("Arknights app killed successfully.")
        sys.exit(0)
    else:
        print("Failed to kill Arknights app.")
        sys.exit(1)


if __name__ == "__main__":
    main()
