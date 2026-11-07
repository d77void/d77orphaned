#!/bin/bash

set -eu

. ./lib.sh

PROGNAME=$(basename "$0")
ARCH=x86_64
REPO=
DATE=$(date -u +%Y%m%d)

# Binary repositories used on top of the official Void ones that mklive.sh
# always appends. d77void: pwm, wasp, utumno, qsd77, dwl, d77-st, scenefx0.5.
# nonfree: nmap. Order matters: earlier repositories take precedence.
DEFAULT_REPOS="https://sourceforge.net/projects/d77void/files/d77void-repo https://repo-default.voidlinux.org/current/nonfree"

usage() {
	cat <<-EOH
	Usage: $PROGNAME [options ...] [-- mklive options ...]

	Builds the D77orphaned live ISO (recovery, diagnostics, careful forensics).
	Wrapper around mklive.sh, adapted from d77void's mkd77.sh (Daniel Azevedo).

	OPTIONS
	 -d <date>     Override the datestamp on the generated image (YYYYMMDD format)
	 -r <repo>     Use this XBPS repository (in addition to the defaults).
	               May be specified multiple times
	 -n            Do not add the default extra repositories (d77void, nonfree)
	 -h            Show this help and exit
	 -V            Show version and exit

	Default extra repositories:
	 $DEFAULT_REPOS

	Other options can be passed directly to mklive.sh by specifying them after the --
	(e.g. -- -k pt-latin1 -l pt_PT.UTF-8). See mklive.sh -h for more details.
	EOH
}

NO_DEFAULT_REPOS=
while getopts "d:hnr:V" opt; do
case $opt in
	d) DATE="$OPTARG";;
	n) NO_DEFAULT_REPOS=yes;;
	r) REPO="$REPO -r $OPTARG";;
	V) version; exit 0;;
	h) usage; exit 0;;
	*) usage >&2; exit 1;;
esac
done
shift $((OPTIND - 1))

if [ -z "$NO_DEFAULT_REPOS" ]; then
	for r in $DEFAULT_REPOS; do
		REPO="$REPO -r $r"
	done
fi

if [ ! -x mklive.sh ]; then
	echo mklive.sh not found >&2
	exit 1
fi

INCLUDEDIR=$(mktemp -d)
trap "cleanup" INT TERM

cleanup() {
	rm -rf "$INCLUDEDIR"
}

# ── Packages (docs/APPROVAL_GATE.md §2) ────────────────────────────────
# base-system, syslinux, grub-*-efi and memtest86+ are added by mklive.sh.

PKGS_DISKS="util-linux parted gptfdisk smartmontools nvme-cli hdparm sdparm sg3_utils lsscsi"
PKGS_RECOVERY="ddrescue testdisk partclone fsarchiver"
PKGS_FS="e2fsprogs xfsprogs btrfs-progs dosfstools exfatprogs ntfs-3g f2fs-tools mtools"
PKGS_VOLUMES="cryptsetup lvm2 mdadm"
PKGS_BOOT="efibootmgr efivar os-prober"
PKGS_NET="iproute2 iputils dhcpcd wpa_supplicant openssh curl rsync"
PKGS_NETDIAG="tcpdump nmap traceroute mtr ldns openbsd-netcat socat arp-scan"
PKGS_FORENSICS="dcfldd libewf sleuthkit foremost"
PKGS_HW="dmidecode pciutils usbutils hwinfo chntpw f3 lynis acpid"
PKGS_OPS="tmux vim less man-db lsof strace pv zstd p7zip squashfs-tools dialog chrony xtools-minimal"

# xmodmap: pwm runs `xmodmap -pke` at startup and exits without it, but
# the pwm package does not declare it (xorg-minimal does not pull it in).
PKGS_X11="xorg-minimal xmodmap xorg-input-drivers xorg-video-drivers xinit setxkbmap xauth dejavu-fonts-ttf terminus-font font-misc-misc pwm d77-st dmenu dbus dbus-x11 elogind polkit"
PKGS_WAYLAND="mesa-dri wasp utumno qsd77 quickshell matugen wmenu alacritty dunst awww"
PKGS_LOGIN="greetd dwl"
# d77 tools: Kantele (settings GUI for pwm and wasp).
PKGS_D77TOOLS="kantele"

# acpi-gpe-guard is not a package: its service dir is placed by
# _include_base and linked into runsvdir there, not via -S.
SERVICES="acpid dbus polkitd greetd dhcpcd chronyd"

# ── Include directory (overlay) ────────────────────────────────────────

# System identity. Keep base-files' /usr/lib/os-release intact; /etc takes
# precedence. The noextract rule stops a base-files update from pointing the
# /etc/os-release symlink back at Void's file.
_include_identity() {
	install -Dm644 ./common/os-release "$INCLUDEDIR"/usr/lib/d77orphaned-os-release
	mkdir -p "$INCLUDEDIR"/etc
	ln -sfn ../usr/lib/d77orphaned-os-release "$INCLUDEDIR"/etc/os-release
	install -Dm644 ./common/xbps.d/90-d77orphaned-os-release.conf \
		"$INCLUDEDIR"/usr/share/xbps.d/90-d77orphaned-os-release.conf
	install -Dm644 ./assets/logo.png \
		"$INCLUDEDIR"/usr/share/icons/hicolor/512x512/apps/d77void.png
}

_include_base() {
	mkdir -p "$INCLUDEDIR"/etc/skel
	cp -r ./common/skel/. "$INCLUDEDIR"/etc/skel/
	cp -r ./pwm/skel/. "$INCLUDEDIR"/etc/skel/
	cp -r ./wasp/skel/. "$INCLUDEDIR"/etc/skel/
	install -Dm755 ./common/d77orphaned/pwm-startup.sh \
		"$INCLUDEDIR"/etc/d77orphaned/pwm-startup.sh
	# greetd sources /etc/profile (and so profile.d) before each session.
	install -Dm644 ./common/profile.d/d77orphaned-wlr.sh \
		"$INCLUDEDIR"/etc/profile.d/d77orphaned-wlr.sh

	# acpi-gpe-guard: guards against a runaway ACPI GPE (firmware
	# interrupt-storm bug seen on some laptops — masks whichever GPE is
	# actually storming, no hardcoded machine-specific GPE number, so
	# it's safe on hardware we don't control). Runtime-only: it writes
	# to sysfs, never to disks.
	install -Dm755 ./common/acpi-gpe-guard/acpi-gpe-guard.sh \
		"$INCLUDEDIR"/usr/lib/acpi-gpe-guard/acpi-gpe-guard.sh
	install -Dm755 ./common/acpi-gpe-guard/run \
		"$INCLUDEDIR"/etc/sv/acpi-gpe-guard/run
	install -Dm755 ./common/acpi-gpe-guard/log/run \
		"$INCLUDEDIR"/etc/sv/acpi-gpe-guard/log/run
	mkdir -p "$INCLUDEDIR"/etc/runit/runsvdir/default
	ln -sf /etc/sv/acpi-gpe-guard "$INCLUDEDIR"/etc/runit/runsvdir/default/acpi-gpe-guard
}

# Integrity of target disks: nothing on them is assembled, activated or
# mounted unless the user does it on purpose.
_include_integrity() {
	# Mask the udev rules that auto-assemble MD RAID and auto-activate LVM
	# after boot (rd.md=0/rd.lvm=0 only cover the initramfs).
	install -Dm644 ./common/udev/64-md-raid-assembly.rules \
		"$INCLUDEDIR"/etc/udev/rules.d/64-md-raid-assembly.rules
	install -Dm644 ./common/udev/69-dm-lvm.rules \
		"$INCLUDEDIR"/etc/udev/rules.d/69-dm-lvm.rules
	install -Dm644 ./common/mdadm.conf "$INCLUDEDIR"/etc/mdadm.conf
	# D1: block Utumno's automatic wttr.in request.
	install -Dm644 ./common/hosts "$INCLUDEDIR"/etc/hosts
}

# greetd + the quickshell-d77 greeter under a disposable dwl (as in d77void's
# include_greetd), with an autologin [initial_session] into pwm.
include_greetd() {
	mkdir -p "$INCLUDEDIR"/etc/greetd/quickshell-d77/greeter
	cp -r ./common/quickshell-d77/greeter/. "$INCLUDEDIR"/etc/greetd/quickshell-d77/greeter/
	install -m755 ./common/quickshell-d77/greeter/assets/greet-dwl.sh "$INCLUDEDIR"/etc/greetd/
	install -m644 ./common/greetd/config.toml "$INCLUDEDIR"/etc/greetd/config.toml
}

build_variant() {
	IMG=d77orphaned-live-${ARCH}-${DATE}.iso

	PKGS="$PKGS_DISKS $PKGS_RECOVERY $PKGS_FS $PKGS_VOLUMES $PKGS_BOOT $PKGS_NET $PKGS_NETDIAG $PKGS_FORENSICS $PKGS_HW $PKGS_OPS $PKGS_X11 $PKGS_WAYLAND $PKGS_LOGIN $PKGS_D77TOOLS"

	_include_identity
	_include_base
	_include_integrity
	include_greetd

	# shellcheck disable=SC2086
	./mklive.sh -a "$ARCH" -o "$IMG" -p "$PKGS" -S "$SERVICES" -I "$INCLUDEDIR" \
		-T "D77orphaned" -x "$(pwd -P)/postsetup.sh" ${REPO} "$@"

	cleanup
}

build_variant "$@"
