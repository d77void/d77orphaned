#!/bin/sh
# -*- mode: shell-script; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# ex: ts=8 sw=4 sts=4 et filetype=sh

type getargbool >/dev/null 2>&1 || . /lib/dracut-lib.sh

if getargbool 0 nomodeset; then
    for dm in lightdm sddm gdm; do
        if [ -e "${NEWROOT}/etc/sv/${dm}" ]; then
            :> "${NEWROOT}/etc/sv/${dm}/down"
        fi
    done

    # d77orphaned: without KMS there is no /dev/dri, so the graphical greeter
    # (quickshell under dwl, a wlroots compositor) cannot start and greetd
    # would keep restarting it on a black screen. Use greetd's text greeter
    # for the default session instead.
    #
    # The pwm autologin ([initial_session]) runs on Xorg's vesa/fbdev drivers.
    # On some machines the video BIOS cannot switch modes back, and ending X
    # or switching to a TTY leaves a black screen for good (seen on a Toshiba
    # with Intel HD 4000 and legacy BIOS). So X never ends on its own
    # (pwm-session.sh restarts pwm) and Ctrl+Alt+Fn does nothing.
    if [ -f "${NEWROOT}/etc/greetd/config.toml" ]; then
        sed -i -e 's|^command = "/etc/greetd/greet-dwl.sh"$|command = "agreety --cmd /bin/bash"|' \
            -e 's|^command = "startx /usr/bin/env dbus-launch pwm"$|command = "startx /usr/bin/env dbus-launch /etc/d77orphaned/pwm-session.sh"|' \
            "${NEWROOT}/etc/greetd/config.toml"
        mkdir -p "${NEWROOT}/etc/X11/xorg.conf.d"
        printf 'Section "ServerFlags"\n\tOption "DontVTSwitch" "true"\nEndSection\n' \
            > "${NEWROOT}/etc/X11/xorg.conf.d/90-d77orphaned-nomodeset.conf"
    fi
fi
