@echo off
adb connect 192.168.10.124:5555
scrcpy -s 192.168.10.124:5555 --turn-screen-off --no-cleanup --no-audio -b 5m