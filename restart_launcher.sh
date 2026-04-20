#!/bin/bash
# 即ランチャー + 透明キーボード を手動で刷新再起動したいとき用のショートカット。
#
# 実体は Hammerspoon に復旧を依頼するだけ（trigger file を touch）。
# Hammerspoon が /tmp/sokulauncher_restart_requested を 3秒ポーリングで検知し、
#   pkill -9 -f folder_launcher.py / transparent_keyboard_mac.py → 再 spawn を実行する。
#
# 直接 pkill + open -a SokuLauncher.app するのは避ける: LaunchServices 由来の
# TCC chain になって screencapture -i が長時間後に失効するため（ハマりポイント#13）。

touch /tmp/sokulauncher_restart_requested
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 復旧を Hammerspoon に依頼しました（最大3秒で発火）"
