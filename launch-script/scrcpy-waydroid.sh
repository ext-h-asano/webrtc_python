#!/bin/bash
waydroid session stop
killall weston
export WAYLAND_DISPLAY=mysocket
weston --socket=$WAYLAND_DISPLAY --backend=x11-backend.so &
waydroid show-full-ui &
sudo modprobe -r v4l2loopback
sudo modprobe v4l2loopback exclusive_caps=1
adb disconnect
adb connect 192.168.240.112:5555
scrcpy --v4l2-sink=/dev/video0 &
python3 /home/ubuntu/selenium/test.py
