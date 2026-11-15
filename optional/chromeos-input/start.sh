#!/bin/bash
set -euo pipefail
umask 077
[ "$(id -u)" = 0 ] || { echo 'Start requires sudo on the ChromeOS host.' >&2; exit 1; }
control=/usr/local/libexec/workbench-input
runtime=/run/chromeos-workbench-input
socket="$runtime/control.sock"
# Geometry is root-owned configuration installed alongside this script.
. /usr/local/etc/chromeos-workbench-input/geometry.conf
[ ! -L "$runtime" ] || { echo 'Refusing symlink runtime directory.' >&2; exit 1; }
install -d -m 755 -o root -g root "$runtime"
if "$control" --send "$socket" ping >/dev/null 2>&1; then echo 'Input helper already running.'; exit 0; fi
rm -f -- "$runtime/helper.log"
nohup "$control" --daemon "$socket" "$(id -u chronos)" "$(id -g chronos)" "$WIDTH" "$HEIGHT" >"$runtime/helper.log" 2>&1 </dev/null &
for attempt in 1 2 3 4 5; do
  if "$control" --send "$socket" ping >/dev/null 2>&1; then echo 'Input helper ready; daemon runs as chronos.'; exit 0; fi
  sleep 1
done
cat "$runtime/helper.log" >&2
exit 1
