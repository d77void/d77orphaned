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

	Builds the d77orphaned live ISO (recovery, diagnostics, careful forensics).
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

ORIG_ARGS=("$@")
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

# Keep the build away from the host's boot files. mklive.sh installs
# memtest86+ into a helper root that has no /bin/sh, so XBPS runs the
# package's post-install script on the host, and that script runs the host's
# grub-mkconfig on /boot/grub/grub.cfg (os-prober included). Run the whole
# build in a private mount namespace with an empty tmpfs over /boot: the
# script then finds no /boot/grub and does nothing. Build mounts also stay
# inside the namespace.
if [ -z "${D77_BUILD_NS:-}" ]; then
	if [ "$(id -u)" -ne 0 ]; then
		echo "$PROGNAME: must be run as root" >&2
		exit 1
	fi
	grubcfg_state() { stat -c '%Y %s' /boot/grub/grub.cfg 2>/dev/null || echo absent; }
	before=$(grubcfg_state)
	rc=0
	D77_BUILD_NS=1 unshare --mount --propagation private -- \
		sh -c 'mount -t tmpfs -o mode=0755,size=16m tmpfs /boot && exec "$0" "$@"' \
		"$0" "${ORIG_ARGS[@]}" || rc=$?
	if [ "$(grubcfg_state)" != "$before" ]; then
		echo "$PROGNAME: ERROR: the host's /boot/grub/grub.cfg changed during the build" >&2
		rc=1
	fi
	exit $rc
fi

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
# D17: NetworkManager (nmtui) manages the network; dhcpcd stays installed
# for manual use but is no longer started at boot.
PKGS_NET="iproute2 iputils dhcpcd wpa_supplicant NetworkManager openssh curl rsync"
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
# D17: desktop basics asked for after the first tests on real hardware.
# feh sets pwm's wallpaper; mullvad-browser comes from the d77void repo.
PKGS_DESKTOP="mullvad-browser font-hack-ttf feh conky papirus-icon-theme ranger"
# D18 group A (docs/PACKAGE_INVENTORY.md): what the sessions need to work as
# in d77void. upower: Utumno's battery; pipewire & co: sound and the volume
# keys (pactl); mate-polkit: password prompts for graphical programs.
PKGS_DESKTOP="$PKGS_DESKTOP upower pipewire wireplumber alsa-pipewire pulseaudio-utils pavucontrol mate-polkit"
PKGS_DESKTOP="$PKGS_DESKTOP nerd-fonts-symbols-ttf noto-fonts-emoji font-awesome6 arc-theme qt6ct nwg-look"
PKGS_DESKTOP="$PKGS_DESKTOP xdg-desktop-portal xdg-desktop-portal-gtk xdg-desktop-portal-wlr qt5-wayland xdg-utils xdg-user-dirs"
PKGS_DESKTOP="$PKGS_DESKTOP htop inxi bash-completion nano unzip wget bc zathura zathura-pdf-poppler"
# As in d77void's pwm startup: screen lock (pwm's super+t runs slock, which
# d77-slock provides), lock after 5 idle minutes, and a compositor.
PKGS_DESKTOP="$PKGS_DESKTOP d77-slock xautolock xcompmgr"
# D18 group B: Grml-like tools. Not dmraid (runit's 03-filesystems.sh runs
# "dmraid -i -ay" at boot whenever it is installed) and not bcache-tools (its
# udev rule and dracut module register bcache devices on their own).
PKGS_TOOLS="mc ncdu tree screen psmisc sysstat iotop moreutils mbuffer"
PKGS_TOOLS="$PKGS_TOOLS lshw lm_sensors memtester stress fio cpuid cpupower acpi"
PKGS_TOOLS="$PKGS_TOOLS dislocker xmount afflib extundelete gpart jfsutils xfsdump fuse-exfat"
PKGS_TOOLS="$PKGS_TOOLS bind-utils whois ipcalc iftop nethogs iperf3 net-tools wireguard-tools openvpn lftp links"
PKGS_TOOLS="$PKGS_TOOLS fuse-sshfs nfs-utils cifs-utils hexedit ltrace binwalk zip cabextract lz4 lzop unp minicom tio kexec-tools gnupg"

# acpi-gpe-guard is not a package: its service dir is placed by
# _include_base and linked into runsvdir there, not via -S.
SERVICES="acpid dbus polkitd greetd NetworkManager chronyd"

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
	install -Dm755 ./common/d77orphaned/wasp-wallpaper.sh \
		"$INCLUDEDIR"/etc/d77orphaned/wasp-wallpaper.sh
	# Optional encrypted persistence on the stick (D22). Nothing runs it at boot.
	install -Dm755 ./common/d77orphaned/d77-persist "$INCLUDEDIR"/usr/bin/d77-persist
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

# PipeWire as in d77void's setup_pipewire: pipewire starts wireplumber and
# pipewire-pulse itself, and ALSA programs go through it. Both sessions
# start pipewire (pwm-startup.sh, wasp's config.lua).
_include_audio() {
	mkdir -p "$INCLUDEDIR"/etc/pipewire/pipewire.conf.d "$INCLUDEDIR"/etc/alsa/conf.d
	ln -sf /usr/share/examples/wireplumber/10-wireplumber.conf "$INCLUDEDIR"/etc/pipewire/pipewire.conf.d/
	ln -sf /usr/share/examples/pipewire/20-pipewire-pulse.conf "$INCLUDEDIR"/etc/pipewire/pipewire.conf.d/
	ln -sf /usr/share/alsa/alsa.conf.d/50-pipewire.conf "$INCLUDEDIR"/etc/alsa/conf.d/
	ln -sf /usr/share/alsa/alsa.conf.d/99-pipewire-default.conf "$INCLUDEDIR"/etc/alsa/conf.d/
}

# The user documentation (d77void/orphaned-docs), readable without a network:
# the mdBook site in /usr/share/doc/d77orphaned/html and its Markdown sources
# in .../md, opened with d77-docs. Built from a checkout of orphaned-docs next
# to this repository (or D77_DOCS_DIR) with mdbook on the build host. Without
# either, the image is built without the documentation, with a warning.
_include_docs() {
	local docs="${D77_DOCS_DIR:-../orphaned-docs}" dest="$INCLUDEDIR"/usr/share/doc/d77orphaned
	install -Dm755 ./common/d77orphaned/d77-docs "$INCLUDEDIR"/usr/bin/d77-docs
	install -Dm644 ./common/d77orphaned/d77-docs.desktop "$INCLUDEDIR"/usr/share/applications/d77-docs.desktop
	if [ ! -f "$docs/book.toml" ] || ! command -v mdbook >/dev/null 2>&1; then
		echo "$PROGNAME: WARNING: no documentation in the image (need $docs and mdbook)" >&2
		return 0
	fi
	docs=$(cd "$docs" && pwd -P)
	mdbook build "$docs" -d "$dest/html" >/dev/null || { echo "$PROGNAME: mdbook build failed" >&2; exit 1; }
	mkdir -p "$dest/md"
	cp -r "$docs/src/." "$dest/md/"
	echo "$PROGNAME: documentation from $docs ($(git -C "$docs" rev-parse --short HEAD 2>/dev/null || echo unknown)) added to the image"
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
	# postsetup.sh writes the SOURCES text next to the ISO as well.
	export D77_SOURCES_OUT="$(pwd -P)/${IMG%.iso}.SOURCES.txt"

	PKGS="$PKGS_DISKS $PKGS_RECOVERY $PKGS_FS $PKGS_VOLUMES $PKGS_BOOT $PKGS_NET $PKGS_NETDIAG $PKGS_FORENSICS $PKGS_HW $PKGS_OPS $PKGS_X11 $PKGS_WAYLAND $PKGS_LOGIN $PKGS_D77TOOLS $PKGS_DESKTOP $PKGS_TOOLS"

	_include_identity
	_include_base
	_include_integrity
	_include_audio
	_include_docs
	include_greetd

	# shellcheck disable=SC2086
	./mklive.sh -a "$ARCH" -o "$IMG" -p "$PKGS" -S "$SERVICES" -I "$INCLUDEDIR" \
		-T "d77orphaned" -x "$(pwd -P)/postsetup.sh" ${REPO} "$@"

	cleanup
}

build_variant "$@"
