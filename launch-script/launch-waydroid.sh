#!/bin/bash
pkill -f "python3 /home/ubuntu/selenium/test.py"
waydroid session stop
killall weston
export WAYLAND_DISPLAY=mysocket
weston --socket=$WAYLAND_DISPLAY --backend=x11-backend.so &
waydroid session stop
waydroid show-full-ui &