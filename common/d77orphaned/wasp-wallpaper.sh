#!/bin/sh
# wasp autostart — d77orphaned, run just before Utumno (config.lua).
# Utumno's set-wallpaper.sh only restores the wallpaper saved in ~/.cache/quickshell/wallpaper/current, which a live
# system's fresh home never has. Restore it when there is one; otherwise
# apply the first image in ~/Wallpaper (the folder Utumno's picker, super+y,
# lists).
set_wallpaper=/usr/share/quickshell/utumno/wallpaper/set-wallpaper.sh
# awww-daemon starts at the same time (wasp.autostart): wait until it
# answers, so set-wallpaper.sh finds it instead of starting a second one.
tries=0
until awww query >/dev/null 2>&1 || [ $tries -ge 50 ]; do
	sleep 0.1
	tries=$((tries + 1))
done
if [ -f "$HOME/.cache/quickshell/wallpaper/current" ]; then
	exec "$set_wallpaper" startup
fi
image="$HOME/Wallpaper/d77void_1920x1080.png"
[ -f "$image" ] || image=$(find "$HOME/Wallpaper" -maxdepth 1 -type f | sort | head -n1)
[ -n "$image" ] && exec "$set_wallpaper" apply "$image"
