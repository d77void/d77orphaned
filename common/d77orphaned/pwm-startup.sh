#!/bin/sh
# pwm startup — d77orphaned. pwm runs this with the active theme's name as $1,
# at login and again every time it restarts: a theme change in Kantele sends
# pwm SIGHUP, and pwm re-execs itself. So the wallpaper is set every time,
# while the background programs are started only if they are not running yet
# (otherwise each theme change would start another copy of each).
#
# Based on the packaged /etc/xdg/pwm/startup.sh, without what d77orphaned
# must not or cannot run: udiskie (automounts target disks), redshift
# (fixed coordinates) and sxhkd (no sxhkdrc here).

# Wallpaper matching the theme (d77Lpwm_<theme>.*, or d77Lpwm.* for the
# default "d77" theme), as the packaged script does; any wallpaper otherwise.
theme="$1"
if [ -z "$theme" ] || [ "$theme" = "d77" ]; then
	pattern="d77Lpwm.*"
else
	pattern="d77Lpwm_$theme.*"
fi
wallpaper=$(find /etc/xdg/pwm/wallpaper -maxdepth 1 -type f -name "$pattern" | head -n1)
if [ -n "$wallpaper" ]; then
	feh --no-fehbg --bg-fill "$wallpaper"
else
	feh --no-fehbg --bg-fill --randomize /etc/xdg/pwm/wallpaper/
fi

# once <process name> <command...>: start the command unless a process of
# this user with that exact name is already running.
once() {
	name="$1"
	shift
	pgrep -u "$(id -u)" -x "$name" >/dev/null || "$@" &
}

once pipewire pipewire
once synclient synclient TapButton1=1
once xcompmgr xcompmgr -c -f -n
once xautolock xautolock -time 5 -locker slock
once polkit-mate-aut /usr/libexec/polkit-mate-authentication-agent-1
once conky conky -c "$HOME/.conkyrc1"
once dunst dunst
