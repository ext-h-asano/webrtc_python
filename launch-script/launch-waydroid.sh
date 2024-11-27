#!/bin/bash

# 最大試行回数
MAX_RETRIES=3
# コマンド実行とエラーチェック・再試行を行う関数
run_command_with_retry() {
  local command="$@"
  local retry_count=0
  while true; do
    $command
    local status=$?
    if [[ $status -eq 0 ]]; then
      echo "コマンド成功: $command"
      break
    else
      echo "コマンド失敗: $command (ステータス: $status)"
      retry_count=$((retry_count + 1))
      if [[ $retry_count -ge $MAX_RETRIES ]]; then
        echo "コマンド失敗、最大試行回数を超えました: $command"
        return 1
      else
        echo "再試行します ($retry_count/$MAX_RETRIES)..."
        sleep 1 # 1秒待機
      fi
    fi
  done
}


pkill -f "python3 /home/ubuntu/selenium/test.py"
waydroid session stop
killall weston
export WAYLAND_DISPLAY=mysocket
weston --socket=$WAYLAND_DISPLAY --backend=x11-backend.so &
waydroid session stop
waydroid show-full-ui &