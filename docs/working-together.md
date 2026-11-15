# Working with two Chromebooks

Use the coordinator for editing/review and the worker for browser checks and
Linux test runs. Keep independent local working copies. Push a reviewed commit,
fetch it on the worker and test that exact commit. Do not edit one worktree from
two sessions or run simultaneous controllers against one browser tab.

The existing dedicated pinned SSH config can run a test suite without starting
another model session:

```sh
ssh -F ~/.ssh/workbench_config workbench-worker
cd ~/projects/chromebook-browser-bridge
git status --short
git rev-parse HEAD
python3 -m unittest discover -p 'test_*.py'
node --test test_worker.cjs test_persistence.cjs test_input_visibility.cjs
```

Use your configured SSH alias/config path. Inspect local changes before updating
source; do not discard worker edits. This uses the worker CPU for ordinary tests;
it does not pool memory or model allowances. Keep its connected browser tab
visible for input, using explicit focus when needed.

## Recovery checks

A brief worker bridge-service restart was tested on November15,2026. After the
service restarted, a fresh heartbeat reported the same connected work tab and
extension0.3.1 without another owner reconnect. The worker then ran all25 Python
and26 JavaScript checks successfully. This tests service recovery, not sleep.

For a physical sleep/wake check, save work and first run the health command.
Record the worker's connected tab using its browser status command. Close only
the worker lid for about30 seconds, reopen it, unlock if needed and open Linux
Terminal if Linux does not resume automatically. Run health/status again.
Verify SSH works, the browser heartbeat is fresh and the intended tab remains
connected. Allow up to a minute for an enabled persistent work mode to recover.
Record any manual step needed; do not call it automatic if you opened Linux or
clicked Start. Honor Disconnect/banner cancellation; it is a deliberate pause,
not a recovery failure to override.

One owner-performed Lenovo lid-close/reopen check passed on November15: the
owner pressed Space after reopening, without unlocking, launching Linux or
reconnecting the bridge. Pinned SSH, a fresh browser heartbeat and snapshot
worked; the connected tab matched the pre-lid baseline. Both bridges ran0.3.1.
Hardware suspend depth/duration was not instrumented, so this proves continuity
through that lid cycle, not deep-suspend or repeated-cycle reliability.

Do not suspend only the Linux guest and describe
that as a ChromeOS lid/suspend test. A full reboot is a separate test, with its
own manual host startup when applicable.

## Plugged-in availability

For an attended setup that needs to accept remote work during idle periods, use
ChromeOS Settings → System preferences → Power (older versions: Device → Power).
Set only the plugged-in idle setting to **Keep display on** and keep the lid open.
Leave battery sleep, lid-close sleep and screen-lock choices unchanged. This uses
the native setting; it does not need a guest-Linux inhibitor or a keep-awake
extension. The Linux guest's sleep policy is not a substitute for ChromeOS's.

[Google's current power-setting instructions](https://support.google.com/chromebook/answer/3420029?hl=en)
explain the control. A sleeping worker was unreachable during our portfolio
preview, then returned healthy after the owner woke it. A subsequent15-minute mixed AC/battery check passed all16 connection/heartbeat
observations; see docs/validation.md for the exact scenario and limits. Do not infer that a
working wake/reconnect test means a sleeping device remains reachable.

Validate with spaced SSH and authenticated browser-status observations for at
least15 minutes after changing the setting, while leaving the laptop untouched.
Record AC power, fresh heartbeats and whether the connected tab changes. Avoid
keyboard/mouse activity from the test, which would defeat an idle check. Report
sampling intervals and any gaps rather than claiming uninterrupted availability.
