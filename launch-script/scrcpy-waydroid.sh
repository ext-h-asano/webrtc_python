#!/bin/bash

# 最大試行回数
MAX_RETRIES=3
# コマンド実行とエラーチェック・再試行を行う関数
run_command_with_retry() {
  local command="$@"
  local retry_count=0
  while true; do
    output=$($command 2>&1)
    local status=$?
    if [[ $status -eq 0 && ! $output =~ "No route to host" ]]; then
      echo "コマンド成功: $command"
      break
    else
      echo "コマンド失敗: $command (ステータス: $status)"
      echo "出力: $output"
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

# scrcpyの出力をチェックし、必要に応じて再試行する関数
run_scrcpy_with_retry() {
  local retry_count=0
  while true; do
    output=$(scrcpy --v4l2-sink=/dev/video0 2>&1 &)
    local status=$?
    if [[ $status -eq 0 && ! $output =~ "ERROR: Device could not be connected (state=offline)" ]]; then
      echo "scrcpyコマンド成功"
      break
    else
      echo "scrcpyコマンド失敗 (ステータス: $status)"
      echo "出力: $output"
      retry_count=$((retry_count + 1))
      if [[ $retry_count -ge $MAX_RETRIES ]]; then
        echo "scrcpyコマンド失敗、最大試行回数を超えました"
        return 1
      else
        echo "adb connectを再試行します ($retry_count/$MAX_RETRIES)..."
        run_command_with_retry adb connect 192.168.240.112:5555
        sleep 1 # 1秒待機
      fi
    fi
  done
}

waydroid session stop
killall weston
export WAYLAND_DISPLAY=mysocket
weston --socket=$WAYLAND_DISPLAY --backend=x11-backend.so &
waydroid show-full-ui &
run_command_with_retry sudo modprobe -r v4l2loopback
run_command_with_retry sudo modprobe v4l2loopback exclusive_caps=1
run_command_with_retry adb disconnect
run_command_with_retry adb connect 192.168.240.112:5555
run_scrcpy_with_retry &
python3 ./launch-script/test.py
