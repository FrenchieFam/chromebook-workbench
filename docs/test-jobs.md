# Bounded worker test jobs

Run from an owner-trusted Linux checkout. The runner adds no daemon, network
listener, model session or paid dependency. It starts one detached Python process
for a fixed test suite and exits when finished. Available suites are:

- `browser-bridge`: Python and JavaScript suites in `~/projects/chromebook-browser-bridge`.
- `workbench`: Python helper tests in `~/projects/chromebook-workbench`.

```sh
python3 tools/job_runner.py start browser-bridge --timeout 120
python3 tools/job_runner.py status JOB_ID_FROM_START
```

The start command returns before tests finish. Invoke it over the existing pinned
SSH connection, then use status later. Jobs require a clean checkout and record
its commit. Results and bounded logs live in the private local directory
`~/.local/state/chromebook-workbench/jobs/JOB_ID/`; do not copy them to a public
repo. A failed test records its exit code; a busy project is refused immediately
instead of queued indefinitely. A timeout terminates the test process group.

## Limits that matter

This is trusted-code orchestration, not a sandbox. Tests run as the Linux user
and can access that user's files. Fixed command names do not make malicious repo
code safe. Review source before running it; do not use this for arbitrary pull
requests. Logs may contain test output with private data. Log size is bounded
with a2MiB child file-size limit; excessive output can fail a test.

The Linux advisory lock is held by the runner and inherited by its direct test
child. It is released when all owning descriptors close; a leftover lock-file
pathname does not itself mean a lock is held. The lock coordinates these runners,
not other editors or manually started tests. It cannot constrain a malicious test
that escapes its process group or closes inherited descriptors.

A detached process can continue after its SSH client exits. It cannot execute
while the whole machine is asleep or powered off. Timeouts use the Linux monotonic
clock and are not an external wall-clock watchdog across machine suspension.
An OOM-killed runner or reboot may leave a partial running report; status checks
recorded process identity (boot and start time) and reports interruption without
restarting. Queued reports can remain if launch fails before the runner starts.
Inspect private logs and processes instead of treating a stale report as success.

Four regression tests exercise failure exit codes, busy/released kernel locks,
timeout termination of a child/grandchild group, changed-checkout refusal and
job-ID traversal rejection. See docs/validation.md for actual device checks.
