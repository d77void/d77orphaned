#!/bin/sh
# -*- mode: shell-script; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# ex: ts=8 sw=4 sts=4 et filetype=sh
#
# d77orphaned: "console only" boot entry. With d77.nogui on the kernel
# command line, keep greetd down so no graphical session starts and the
# TTYs are the only environment. Same mechanism as nomodeset.sh.

type getargbool >/dev/null 2>&1 || . /lib/dracut-lib.sh

if getargbool 0 d77.nogui; then
    if [ -e "${NEWROOT}/etc/sv/greetd" ]; then
        :> "${NEWROOT}/etc/sv/greetd/down"
    fi
fi
