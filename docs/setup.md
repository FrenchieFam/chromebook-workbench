# Two-device setup

Use your own ChromeOS profile on each machine. Linux filesystem access is
separate from ChromeOS host access. Free space from `df -h /` describes the Linux
virtual disk, not space used by other ChromeOS profiles. Assess storage before
considering cleanup; this setup does not require a reset.

## 1. Userspace link on each device

Prerequisites: x86_64 Linux, Python 3.10+, OpenSSH client (`ssh`, `ssh-keyscan`,
`ssh-keygen`), and a working systemd user session. Install Git to clone this repo.
The source tests use standard-library mocks rather than a live Tailscale account.

```sh
git clone https://github.com/FrenchieFam/chromebook-workbench.git
cd chromebook-workbench
python3 tools/setup_userspace.py --name workbench-coordinator
```

On the worker use `--name workbench-worker`. Review the installer before running
it. It runs as the normal user; no sudo, system package repository, kernel tunnel,
SSH server or account login is created by the installer. Its private state and
Unix socket live under user-only directories.

Use the printed command on each device:

```sh
~/bin/workbench-tailscale up --hostname=workbench-coordinator --accept-dns=false --accept-routes=false --timeout=10s
```

Substitute the worker name on the other machine. Open each login URL yourself and
choose the same existing tailnet. A timeout while waiting for approval is not a
reason to delete state. Inspect `~/bin/workbench-tailscale status` afterward. Do
not put login URLs, auth keys, node state or account screenshots in shared notes.

This is [userspace networking](https://tailscale.com/docs/concepts/userspace-networking),
not a system-wide VPN. Normal programs do not automatically acquire tailnet
routes; our SSH configuration uses `tailscale nc` through the dedicated socket.
Do not add an exit node, advertise routes, enable Tailscale SSH or change global
ACLs just to follow this guide. An existing tailnet policy must permit the
coordinator to reach the worker's chosen TCP port.

## 2. Key-only OpenSSH on the worker

Run service configuration from a worker-local terminal. Inspect an existing SSH
setup before changing it, especially if it already serves other users/ports.
Install `openssh-server` if absent. Preserve the original configuration and use a
separate drop-in. The intended effective settings are:

```text
Port 2222
AuthenticationMethods publickey
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
AllowUsers YOUR_LINUX_USER
```

Replace the user placeholder. Keep `.ssh` mode0700 and `authorized_keys` mode0600,
owned by that user. On the coordinator create a dedicated identity if you do not
already have one:

```sh
ssh-keygen -t ed25519 -f "$HOME/.ssh/workbench_worker" -C workbench-coordinator
```

Keep its private key local. If you choose a passphrase, unlock it through your
local SSH agent before batch commands. Add only the matching `.pub` line to the
worker's `authorized_keys`, idempotently. A private Drive project folder or another
trusted channel can carry that **public** key; it must not carry the private key.

On the worker, create `/run/sshd` if validation needs it, then validate before
starting/restarting the service:

```sh
sudo install -d -m 755 /run/sshd
sudo /usr/sbin/sshd -t
sudo /usr/sbin/sshd -T
sudo systemctl enable --now ssh
```

If an already-running service needs its new port applied, restart it from the
local worker terminal after validation. Verify the listener with `ss -lnt` and
confirm the effective auth policy, rather than assuming the drop-in won over
another setting. Print the PUBLIC ED25519 host-key fingerprint:

```sh
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub -E sha256
```

Transfer that fingerprint through your trusted handoff/owner channel. Never copy
the private `/etc/ssh/ssh_host_*_key` files.

## 3. Private TCP mapping and verified client pin

On the worker, inspect existing Serve settings, then add only the intended
[private raw TCP mapping](https://tailscale.com/docs/reference/tailscale-cli/serve):

```sh
~/bin/workbench-tailscale serve status
~/bin/workbench-tailscale serve --bg --tcp=2222 tcp://127.0.0.1:2222
~/bin/workbench-tailscale ip -4
```

Use Serve, not public Funnel. On the coordinator substitute your actual tailnet
hostname, worker user and independently obtained fingerprint:

```sh
python3 tools/connect_worker.py \
  --host WORKER_TAILNET_NAME \
  --user YOUR_WORKER_LINUX_USER \
  --identity "$HOME/.ssh/workbench_worker" \
  --fingerprint 'SHA256:YOUR_WORKER_ED25519_FINGERPRINT'
```

The helper obtains the offered key through a temporary loopback bridge to
`tailscale nc`, compares the fingerprint **before authentication**, and creates
separate `.ssh/workbench-worker.conf` and `.known_hosts` files. A mismatch or a
conflicting existing file aborts. It does not weaken global SSH settings.

```sh
ssh -F "$HOME/.ssh/workbench-worker.conf" workbench-worker 'id -un; uname -m'
scp -F "$HOME/.ssh/workbench-worker.conf" file.txt workbench-worker:~/
```

Both Linux environments must remain running. A relayed Tailscale connection can
work even when direct peer connectivity is unavailable; measure your actual
workload before making performance claims.

## 4. Browser bridge

On the worker, follow the public [Browser Bridge README](https://github.com/FrenchieFam/chromebook-browser-bridge).
Share Downloads with Linux in the ChromeOS Files app first. Install its runtime
and generated extension there, using worker-specific credentials; never copy a
paired coordinator extension or generated config.js to the worker or to Drive.
The owner loads the unpacked extension and connects a normal page or starts a
persistent work tab. The extension-page Developer mode switch is separate from
ChromeOS boot Developer Mode.

From the coordinator:

```sh
python3 tools/remote_browser.py --config "$HOME/.ssh/workbench-worker.conf" -- status
python3 tools/remote_browser.py --config "$HOME/.ssh/workbench-worker.conf" -- snapshot
```

The remote helper preserves JSON quoting. Screenshot `--output` paths refer to
the WORKER filesystem; copy the resulting file back explicitly if needed and
keep private screenshots out of Git/Drive. For Codex stdio MCP:

```sh
codex mcp add worker-browser -- ssh -F "$HOME/.ssh/workbench-worker.conf" workbench-worker python3 .local/share/chromebook-browser-bridge/mcp_server.py
```

The remote relative path assumes OpenSSH starts in the worker's home directory.
Verify it if your server has a custom working directory. Existing Codex sessions
may need MCP reload/new-session discovery; the CLI helper is available immediately.
Check the selected tab's status and a fresh snapshot before page actions.

## Why the ChromeOS forwarding page was not our connection path

A local HTTP canary worked from native Chrome's `localhost` on the worker, while
the same port on its Wi-Fi address refused connections from both coordinator
Linux and coordinator ChromeOS. That isolated host-local reachability from LAN
reachability; reinstalling an already-working sshd was not justified.

Chromium's [Baguette change](https://chromium.googlesource.com/chromium/src/+/7cf262e10286597f10b93cd85e2f25c034bf5117)
disables the classic port-forwarding menu for that backend. Its automatic
[localhost-forwarding documentation](https://www.chromium.org/chromium-os/developer-library/reference/security/port-forwarding/)
excludes port2222, reserved for Files-app SFTP. Our backend evidence supported a
direct ChromeOS VM; its exact Baguette identity was not conclusively established.
Do not promise that merely changing ports makes a service LAN-accessible. The
private userspace link avoids relying on that behavior, with no router rules or
ChromeOS host changes.
