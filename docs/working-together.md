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

Physical sleep/wake is pending. Do not suspend only the Linux guest and describe
that as a ChromeOS lid/suspend test. A full reboot is a separate test, with its
own manual host startup when applicable.
