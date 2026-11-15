#!/bin/bash
# Run only on an already-admin-enabled, owner-controlled x86_64 ChromeOS host.
set -euo pipefail
umask 077
[ "$(id -u)" = 0 ] || { echo 'Run with sudo on ChromeOS.' >&2; exit 1; }
[ "$(uname -m)" = x86_64 ] || { echo 'This build is x86_64 only.' >&2; exit 1; }
width="${1:-1366}"
height="${2:-768}"
[[ "$width" =~ ^[0-9]{3,4}$ && "$height" =~ ^[0-9]{3,4}$ ]] || { echo 'Supply width height in pixels.' >&2; exit 1; }
((width >= 320 && width <= 8192 && height >= 320 && height <= 8192)) || exit 1
source_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
"$source_dir/workbench-input" --version
config=/usr/local/etc/chromeos-workbench-input
[ ! -L "$config" ] || { echo 'Refusing symlink config directory.' >&2; exit 1; }
install -d -m 755 -o root -g root /usr/local/libexec "$config"
if [ -x /usr/local/libexec/workbench-input ]; then
  backup="$config/before-$(date +%Y%m%d-%H%M%S)"
  install -d -m 700 "$backup"
  cp -p /usr/local/libexec/workbench-input "$backup/"
  for name in start.sh geometry.conf; do if [ -f "$config/$name" ]; then cp -p "$config/$name" "$backup/"; fi; done
  /usr/local/libexec/workbench-input --send /run/chromeos-workbench-input/control.sock stop >/dev/null 2>&1 || true
  sleep 1
fi
install -m 755 "$source_dir/workbench-input" /usr/local/libexec/workbench-input
install -m 755 "$source_dir/start.sh" "$config/start.sh"
printf 'WIDTH=%s\nHEIGHT=%s\n' "$width" "$height" >"$config/geometry.conf"
chmod 600 "$config/geometry.conf"
"$config/start.sh"
echo 'Installed. No boot hook, SSH listener, rootfs or firmware changes were made.'
echo 'After a host restart, manually run: sudo /usr/local/etc/chromeos-workbench-input/start.sh'
