#!/bin/sh
# mksources.sh <rootfs> <output file>
#
# Writes the SOURCES text for a d77orphaned image: where to get the
# source code of every package installed in <rootfs>, plus a written offer
# for the GPL software. One line per source package, with its version,
# licenses, binary packages and a link to its source.
#
# Void packages: https://sources.voidlinux.org/<sourcepkg>-<version>/ holds
# the source archives each package was built from, and the templates are in
# void-packages. d77void packages: templates in d77void/srcpkgs-d77, and the
# upstream homepage.
set -eu
ROOTFS="$1"
OUT="$2"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# One query per property for all installed packages ("<pkgver>: <value>").
for prop in sourcepkg source-revisions license repository homepage; do
	xbps-query -r "$ROOTFS" -s '' -p "$prop" >"$tmp/$prop"
done
xbps-query -r "$ROOTFS" -l | awk '{print $2}' >"$tmp/pkgvers"

awk '
	BEGIN { OFS = "\t" }
	FNR == 1 { prop = FILENAME; sub(".*/", "", prop) }
	prop != "pkgvers" {
		i = index($0, ": "); pv = substr($0, 1, i - 1); v[prop, pv] = substr($0, i + 2); next
	}
	{
		pv = $0
		name = pv; sub(/-[^-]*$/, "", name)
		ver = pv; sub(/^.*-/, "", ver); sub(/_[0-9]+$/, "", ver)
		src = v["sourcepkg", pv]
		if (src == "") { src = v["source-revisions", pv]; sub(/:.*/, "", src) }
		if (src == "") src = name
		repo = v["repository", pv]; home = v["homepage", pv]
		if (repo ~ /voidlinux\.org/) url = "https://sources.voidlinux.org/" src "-" ver "/"
		else if (repo ~ /d77void/) url = "https://github.com/d77void/srcpkgs-d77/tree/main/srcpkgs/" src " (" home ")"
		else url = (home != "" ? home : "unknown") " (repository: " repo ")"
		print src, ver, v["license", pv], name, url, home
	}' "$tmp/sourcepkg" "$tmp/source-revisions" "$tmp/license" "$tmp/repository" "$tmp/homepage" "$tmp/pkgvers" >"$tmp/rows"

{
	cat <<-EOF
	d77orphaned: source code of the software in this image
	=======================================================

	This image is made of binary packages from Void Linux and from the d77void
	repository. Many of them are under the GNU GPL or similar licenses, which
	entitle you to their complete corresponding source code.

	One package, nmap, is under the Nmap Public Source License (NPSL 0.95),
	which is not an OSI-approved open source license; Void ships it in its
	"nonfree" repository. Its license text is in /usr/share/licenses/nmap/.
	The license texts of the other packages are in /usr/share/licenses/.

	Where to find the source
	------------------------

	- Void Linux packages: https://sources.voidlinux.org/<package>-<version>/
	  holds the exact source archives each package was built from (the link
	  is given for every package below). The build recipes (templates and
	  patches) are in https://github.com/void-linux/void-packages, under
	  srcpkgs/<package>; a template's "distfiles" line is the original
	  download address, should the archive be missing from that server.
	- d77void packages: the templates are in
	  https://github.com/d77void/srcpkgs-d77, under srcpkgs/<package>; the
	  source is at the project's homepage, given in brackets.
	- The scripts that build this image: https://github.com/d77void/d77orphaned

	Written offer
	-------------

	For at least three years after this image is published, anyone can get
	the complete corresponding source code of any program in it, for no more
	than the cost of providing it, by opening an issue at:

	    https://github.com/d77void/d77orphaned/issues

	Packages
	--------

	Source package, version, licenses, binary packages in this image, source
	and the project's homepage.

	EOF
	sort -t "$(printf '\t')" -k1,1 -k4,4 "$tmp/rows" | awk -F '\t' '
		function flush() {
			if (key == "") return
			printf "%s %s\n  license: %s\n  packages: %s\n  source: %s\n", src, ver, lic, pkgs, url
			if (home != "") printf "  homepage: %s\n", home
			printf "\n"
		}
		{
			k = $1 "\t" $2
			if (k != key) { flush(); key = k; src = $1; ver = $2; lic = $3; pkgs = $4; url = $5; home = $6; next }
			pkgs = pkgs " " $4
			if (index(lic, $3) == 0) lic = lic ", " $3
		}
		END { flush() }'
} >"$OUT"

echo "mksources: $(grep -c '^  source: ' "$OUT") source packages written to $OUT"
