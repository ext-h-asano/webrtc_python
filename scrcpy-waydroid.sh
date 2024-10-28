#!/bin/bash

sudo modprobe -r v4l2loopback
sudo modprobe v4l2loopback exclusive_caps=1
waydroid show-full-ui
adb disconnect
adb connect 192.168.240.112:5555
scrcpy --v4l2-sink=/dev/video0