# Practical capability roadmap

Research checked November15,2026. The existing setup already edits/publishes code,
runs remote Linux commands and controls an owner-connected browser tab. More root
access is not a prerequisite for the next portfolio project.

## Build useful reliability first

1. Finish measured idle availability and record observed AC/battery changes.
2. Use bounded, persistent test jobs so SSH interruption does not lose a test's
   result. Keep a single writer/controller per repo/tab.
3. Put short build/test/definition-of-done guidance in each project. Codex
   [AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
   describes project instructions. They are context, not a security boundary.

The test runner is implemented separately in tools/job_runner.py. It calls fixed
ordinary test suites, not another AI agent. It cannot prevent machine sleep.

## A useful optional power improvement

Chrome's [power API](https://developer.chrome.com/docs/extensions/reference/api/power)
can request `system` wakefulness while allowing the display to dim/turn off.
A small timed, owner-enabled control could save screen power compared with
permanent Keep display on. It would need the `power` permission, explicit enable,
a visible expiry, release on Disconnect/timeout, restart reconciliation, and
physical battery/AC testing. It must not claim to override lid close, shutdown,
critical battery or policy. This remains a proposal; no permission was added. Keeping Linux jobs reachable
with the screen off does not establish that native Chrome input remains visible
or usable; test those cases separately before claiming browser availability.

## Use maintained browser tooling when a project needs it

[Playwright's extension](https://playwright.dev/mcp/configuration/browser-extension)
can connect to existing browser tabs. Evaluate it against a concrete missing
capability (for example a complex form) before expanding our custom bridge.
It has not been installed or benchmarked on these Chromebooks. Broader tooling
is not evidence that our owner-tab/stop rules should be removed.

## Task-specific external access

GitHub publication and shared project Drive files already work. Connect further
services only for an actual task: a test SMS provider for a live messaging pilot,
for example, requires its own cost, account and delivery/opt-out validation. The
current missed-call project stays a simulation. No payment, email-sending or
customer-account access is needed to polish its portfolio case study.

A future existing homelab PC could run heavier test/browser workloads over the
private network when it is available. This does not combine Chromebook RAM or
increase model allowances. No additional subscriptions are needed for this plan.

## Second opinion and verification

An owner-authorized DeepSeek design review recommended persistent artifacts and
power validation. Its proposed stale-lock problem was checked against
[Linux flock documentation](https://man7.org/linux/man-pages/man2/flock.2.html):
locks track open file descriptions, not the continued existence of a lock-file
pathname. The implementation therefore uses nonblocking OS locks rather than a
new heartbeat/lock-deletion watchdog. Advice was treated as a hypothesis and
checked; no external chat instructions were executed directly.
