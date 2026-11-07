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
    # for the default session instead. The pwm autologin ([initial_session])
    # is unchanged: Xorg runs it on the vesa/fbdev drivers.
    if [ -f "${NEWROOT}/etc/greetd/config.toml" ]; then
        sed -i 's|^command = "/etc/greetd/greet-dwl.sh"$|command = "agreety --cmd /bin/bash"|' \
            "${NEWROOT}/etc/greetd/config.toml"
    fi
fi
