#!/bin/bash
export WAYLAND_DISPLAY=mysocket
weston --socket=$WAYLAND_DISPLAY --backend=x11-backend.so &
waydroid session stop
waydroid show-full-ui &