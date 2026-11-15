# Optional ChromeOS host input

Advanced, optional source for an owner-admin-enabled x86_64 ChromeOS host. The
normal two-device SSH/browser setup does not need this component.

**Prerequisite:** you already have authorized, key-authenticated host SSH/admin
access and a writable `/usr/local`. Setting up boot Developer Mode can erase
local data; this repository does not enable it, disable rootfs verification,
change firmware, or turn it into a base-setup requirement. Keep other profiles
intact. The original tested owner chose manual startup and retained rootfs
protection. Generic installer paths are adapted source, not a universal installer
verified across hardware.

## Build and inspect

In x86_64 Linux with GCC/static libc development files:

```sh
make all check
```

Review `input.c`, `start.sh` and `install-host.sh`. Copy only the built
`workbench-input`, startup and installer scripts to a ChromeOS-readable folder.
On the already-admin-enabled HOST, install using the actual desktop dimensions:

```sh
sudo bash /path/to/install-host.sh 1366 768
```

The dimensions above are an example from the original test. Config is root-owned
under `/usr/local/etc/chromeos-workbench-input`; binary is
`/usr/local/libexec/workbench-input`. Runtime parent is root-owned0755, socket
chronos-owned0600, and root's log is inside that root-owned parent with0077 umask.
The C daemon opens uinput as root, clears groups and drops UID/GID to chronos
before accepting bounded named input commands from chronos/root. No shell-exec
protocol, TCP listener or automatic boot hook is created. Prior installs get a
root-only timestamped backup. Stop destroys the virtual devices; the next root
startup removes a stale socket.

Configure a pinned OpenSSH host alias called `chromeos-host` yourself. Do not
copy another owner's host/client private keys. Then from Linux:

```sh
python3 desktop.py --ssh-host chromeos-host info
python3 desktop.py --ssh-host chromeos-host screenshot --output /tmp/desktop.png
# Inspect the screenshot before input.
python3 desktop.py --ssh-host chromeos-host move 600 400
python3 desktop.py --ssh-host chromeos-host click left
python3 desktop.py --ssh-host chromeos-host key ctrl+l
python3 desktop.py --ssh-host chromeos-host text 'https://example.com/'
python3 desktop.py --ssh-host chromeos-host key enter
python3 desktop.py --ssh-host chromeos-host drag 600 500 600 300 600
```

Coordinates refer to the FULL desktop, not a browser viewport. Pointer actions
require a screenshot less than120seconds old matching the helper's configured
geometry. A mismatch blocks input; it does not recalibrate the device. There is
no guessed legacy geometry fallback. `--downloads` overrides the detected shared
Downloads directory. Screenshot capture uses the native Ctrl+Overview shortcut,
creates a PNG in ChromeOS Downloads, may replace clipboard contents, and shows a
native toast. Treat captures as private; no video recording is implemented.
Freshness/size checks cannot determine app focus. Inspect before input, coordinate
with the owner and do not type while they are typing.

This absolute device acts as TOUCH input. Long-press via
`drag X Y X Y 900` can open a touch context menu and may select text. Vertical
swipes and pointer-aware controls worked in the original test; ordinary HTML5
mouse/file dragging did not. True right/middle click and wheel are rejected by
the wrapper. ASCII entry only, at most1000characters, no implicit Enter. Arbitrary
dialogs, Unicode, multi-monitor and unattended desktop control remain unverified.

## Recovery and stop

After a full host restart, restore your existing host SSH access as you normally
do, then manually run on the HOST:

```sh
sudo /usr/local/etc/chromeos-workbench-input/start.sh
```

From Linux, `python3 desktop.py stop` stops input. No boot-start behavior was
added. Explicit owner stops and canceled browser debugging banners must not be
worked around through native input; browser and desktop scopes remain distinct.
For removal, stop it and deliberately remove only these named installed paths;
retain your unrelated SSH setup and rootfs protection.

See the root validation record for original live tests versus generalized-source
checks. Chromium's [uinput reference](https://chromium.googlesource.com/chromiumos/platform2/+/main/screen-capture-utils/uinput.cc)
explicitly describes the absolute-pointer approach as touch with left-button
support; do not advertise it as a full mouse implementation.
