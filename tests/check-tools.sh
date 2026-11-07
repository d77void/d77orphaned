#!/bin/sh
# T7 — run inside the live system (as root).
# For every package passed on the command line (default: all installed),
# check that each ELF executable it ships resolves all its shared
# libraries, and that the expected commands exist. Prints a summary and
# exits non-zero on any failure.

pkgs="$*"
[ -z "$pkgs" ] && pkgs=$(xbps-query -l | awk '{print $2}' | xargs -n1 xbps-uhelper getpkgname)

fail=0; checked=0
for p in $pkgs; do
	for f in $(xbps-query -f "$p" 2>/dev/null | grep -E '^/usr/(s?bin|libexec)/'); do
		{ [ -f "$f" ] && [ -x "$f" ]; } || continue
		head -c4 "$f" 2>/dev/null | grep -q 'ELF' || continue
		checked=$((checked+1))
		missing=$(ldd "$f" 2>/dev/null | grep 'not found')
		if [ -n "$missing" ]; then
			echo "FAIL $p $f: $missing"
			fail=$((fail+1))
		fi
	done
done

# Commands the PoC promises (APPROVAL_GATE §2.2–2.5).
for c in lsblk parted gdisk smartctl nvme hdparm sdparm sg_inq lsscsi ddrescue \
	testdisk photorec partclone.ext4 fsarchiver mkfs.ext4 xfs_repair btrfs mkfs.vfat \
	mkfs.exfat ntfs-3g fsck.f2fs mcopy cryptsetup lvm mdadm efibootmgr efivar os-prober \
	ip ping dhcpcd wpa_supplicant ssh curl rsync tcpdump nmap traceroute mtr drill nc \
	socat arp-scan dcfldd ewfacquire mmls fls foremost dmidecode lspci lsusb hwinfo \
	chntpw f3probe lynis tmux vim less man lsof strace pv zstd 7z mksquashfs chronyd \
	Xorg startx pwm st dmenu_run dbus-launch wasp wasp-session qs qsd77 matugen \
	wmenu-run alacritty dunst awww greetd dwl; do
	if ! command -v "$c" >/dev/null 2>&1; then
		echo "MISSING command $c"
		fail=$((fail+1))
	fi
done

echo "T7: checked $checked ELF executables; failures: $fail"
[ "$fail" -eq 0 ]
