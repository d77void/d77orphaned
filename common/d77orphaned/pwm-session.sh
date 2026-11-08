#!/bin/sh
# pwm session for the "graphics disabled" (nomodeset) boot — d77orphaned.
# Xorg runs on the vesa driver there. On some machines (a Toshiba with Intel
# HD 4000 and legacy BIOS) the video BIOS cannot switch modes back, so ending
# X leaves a black screen that only the power button gets out of. So X stays:
# leaving pwm starts pwm again. Power off with pwm's menu (super+x).
#
# If pwm keeps dying at once, give up, rather than restart it forever.
quick=0
while [ "$quick" -lt 5 ]; do
	start=$(date +%s)
	pwm
	if [ $(($(date +%s) - start)) -lt 10 ]; then
		quick=$((quick + 1))
	else
		quick=0
	fi
done
