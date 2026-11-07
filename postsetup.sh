#!/bin/sh
# d77orphaned post-setup, run by mklive.sh (-x) on the finished rootfs ($1),
# before the initramfs is generated.
#
# Void's runit core-services (03-filesystems.sh) run `vgchange --sysinit -a ay`
# on every boot, outside udev — masking 69-dm-lvm.rules is not enough. An
# empty auto_activation_volume_list makes every "-a ay" (and pvscan
# --autoactivation) activate nothing; event_activation = 0 also stops the
# udev/event path. LVs on target disks are activated only by hand, read-only
# with: vgchange -ay --config 'activation { read_only_volume_list = [ "<vg>" ] }' <vg>
set -eu
ROOTFS="$1"

# Where to get the source of every installed package, and the written offer
# for the GPL software (mksources.sh). Kept in the image, and written next to
# the ISO too when mkorphaned.sh sets D77_SOURCES_OUT.
sources="$ROOTFS/usr/share/doc/d77orphaned/SOURCES.txt"
mkdir -p "${sources%/*}"
"$(dirname "$0")/mksources.sh" "$ROOTFS" "$sources"
[ -z "${D77_SOURCES_OUT:-}" ] || cp "$sources" "$D77_SOURCES_OUT"

conf="$ROOTFS/etc/lvm/lvm.conf"
[ -f "$conf" ] || { echo "postsetup: $conf not found" >&2; exit 1; }

grep -q 'd77orphaned' "$conf" && exit 0

sed -i \
	-e '/^global {/a\	# d77orphaned: no event-based autoactivation.\n\tevent_activation = 0' \
	-e '/^activation {/a\	# d77orphaned: never auto-activate LVs (vgchange -a ay in runit core-services).\n\tauto_activation_volume_list = []' \
	"$conf"

if ! grep -q '^	auto_activation_volume_list = \[\]' "$conf" ||
	! grep -q '^	event_activation = 0' "$conf"; then
	echo "postsetup: failed to update $conf" >&2
	exit 1
fi
