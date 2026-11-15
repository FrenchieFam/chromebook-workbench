# Validation and limits

Recorded November14,2026 (Pacific). Two x86_64/4GB Chromebooks: Samsung4/Celeron
N4020 and Lenovo/AMD A6-9220C (exact Lenovo model not identified), Debian13 guests.
No claim about all Chromebook models, managed policy, hardware acceleration or
production/unattended reliability.

## Original live setup

- Userspace Tailscale1.104.7 user services active as ordinary UID/GID1000/1000;
  state/runtime0700, state file0600, no kernel TUN, DNS/route acceptance or public
  Funnel enabled. Owner authenticated both nodes to an existing personal tailnet.
- Worker OpenSSH2222 validated locally, with publickey-only auth, root/password/
  keyboard-interactive disabled and one allowed Linux user.
- ED25519 fingerprint matched the worker's independently shared public value
  BEFORE first remote authentication. Key-only remote command returned the
  expected user, architecture and Codex CLI0.169.0.
- SCP/SFTP transfers/readback passed in both directions; generated temporary
  test files were removed. Relay path worked; no direct path or speed benchmark
  was claimed.
- Browser Bridgev0.3.0 passed22Python+17JS tests on Lenovo. Its portable installer
  produced local private config/token0600, a running service and MCP registration.
  Owner loaded the Chrome extension and started persistent mode.
- Actual browser navigation, snapshot, apostrophe text transport, checkbox click,
  native select, button result, screenshot and390x844/no overflow checks passed.
  Viewport/start page restored and temporary fixture server stopped afterward.
- Background clicks initially returnedOK without changing a checkbox. Once the
  owner made the connected worker tab visible, coordinate input passed. This
  limitation is recorded rather than hidden by unit-test success.
- Original Samsung host-input implementation was live-tested for full screenshot,
  absolute touch tap, ASCII shortcuts, native Quick Settings, bounded pointer-
  aware drag, vertical touch scrolling and long-press context menus. True mouse
  right/middle/wheel and ordinary HTML5 mouse drag/drop did not work as assumed;
  the wrapper rejects unsupported mouse/wheel actions. No claim of arbitrary
  file dragging, Unicode entry, multi-monitor or universal system-dialog control.

## Generalized public source

The generic userspace script adapts that tested setup to caller-chosen hostnames.
Eight standard-library tests cover download-checksum refusal, preserving existing
executables/config on a conflicting unit, repeatable isolated install with paths
containing spaces/private state, actual SSH-config parsing, host-key mismatch/
changed-pin refusal, unsafe-host rejection and literal JSON/shell-metacharacter
transport through a real shell. The generalized fingerprint-pinning and remote-browser helpers also passed a
real SSH command and authenticated browser-status call against the existing worker,
using a temporary client configuration. The tests use temporary keys/mocks; they do not
claim a fresh Tailscale account installation on every distro.

Optional native source compiles statically with warnings as errors; C pipe tests
check ASCII maps, invalid shortcuts, bounded drag endpoints/button release and
text limits. Five Python tests check screenshot freshness/geometry and rejecting
unsupported mouse actions. Shell syntax checks pass. Generic host paths/installer
are NOT deployed over the private working Samsung helper during packaging and
have not been installed on Lenovo. The original native helper passed one physical
reboot/manual-startup check; the NEW cross-device tailnet route has not.

## Browser visibility follow-up — November15,2026

Browser Bridge0.3.1 passed25Python+26JS tests and actual Lenovo Chrome checks.
Hidden click/type/key were refused without changing the form; explicit focus
made the same connected tab visible. Text/checkbox/select/button and390x844
checks passed. Viewport/start page restored and temporary fixture stopped.
Minimized windows remain physically untested.

## Still open

Other hardware/architectures, independent security review, multiple physical
reboot/sleep cycles, changed Wi-Fi/VM addresses, throughput measurements, minimized
browser/window cases, and generalized native-host installation on another device.
Do not infer that two4GB computers form one8GB memory space or double an account's
model allowance. No background agent task loop or database sync is included.

## Detached test-job verification — November15,2026

The helper suite now has16 tests:8 setup/transport,4 health-state and4 job-runner
cases. On the Lenovo, a detached browser-bridge job against release0.3.1 ran25
Python+26JavaScript checks and saved a passed result with both exit codes0.
A separate detached workbench job at a994e7e ran all16 helper tests successfully.
Both launch SSH commands returned before completion; a later independent SSH
connection retrieved results. This verifies launcher-session independence, not
survival of machine sleep or power loss. Job logs/boot IDs remain private.
