# Recovery, updates and removal

## Normal startup

Open Linux on both Chromebooks. Check the user service and filtered/local status:

```sh
systemctl --user is-active workbench-tailscaled.service
~/bin/workbench-tailscale status
```

On the worker also check `systemctl is-active ssh` and its private `serve status`.
The Linux environments must be running before the connection can work. These
user services do not boot Linux at ChromeOS startup. The private cross-device
route has not yet been checked across a full physical reboot.

If authentication is needed, use the printed login flow for your existing
account. Do not delete node state to troubleshoot ordinary connectivity. Do not
recreate SSH host keys or remove a known-host pin to silence a mismatch.

For browser control, start Linux and inspect the extension's state. Persistence
can retry the dedicated work tab; Disconnect/banner cancellation remains a pause
until the owner explicitly resumes. Exact prior conversation/page restoration
is not guaranteed. Keep v0.3.0's work tab visible for coordinate input.

## Updates

Tailscale binaries are installed under `~/.local/share/tailscale-workbench` and do
not auto-update. The source pins the recorded version. To update, review the
upstream release, intentionally update the installer version, verify its package
checksum and run the tests. Preserve local node state and service/wrapper config.
Do not overwrite an unrelated existing installation to make an upgrade work.

Browser Bridge updates require rerunning its installer from reviewed source and
reloading the installed Chrome extension. Editing extension files alone does not
update the running worker. Pending actions may be lost during service restart;
inspect page state before retrying mutations.

## Stop and remove this addition

```sh
systemctl --user disable --now workbench-tailscaled.service
```

That stops the new transport without deleting its private identity/state. To
remove just the worker's mapping:

```sh
~/bin/workbench-tailscale serve --tcp=2222 off
```

For full removal, deliberately remove only the unit, installed binaries/wrapper,
dedicated SSH config/public pin and authorized client-key line created for this
setup. Decide separately whether to revoke the device in Tailscale and delete its
private state. Keep other homelab devices, server settings and keys intact.
Remove the browser extension/service/MCP registration through its own guide.

Optional native host input has a separate manual startup and stop procedure in
its README. This toolkit does not modify boot firmware or rootfs verification.

## Backups

Use Git for reviewed source and branches. Small per-device Markdown handoffs can
live in a private Drive project folder. Confirm that the other machine received
a file: a local mounted-file readback is not a cloud synchronization guarantee.
Keep live repos, Codex SQLite databases, installed dependencies and account state
local. Do not use a shared Codex directory as a conversation-sync mechanism.

A credential-excluding source ZIP is not a full-machine backup. Keep any private
Linux backup or key-recovery material separate from this public repository and
coordinate disruptive restore/reboot operations with the device owner.
