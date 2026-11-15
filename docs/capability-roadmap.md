# Practical capability roadmap

Research checked November15,2026. The existing setup already edits/publishes code,
runs remote Linux commands and controls an owner-connected browser tab. More root
access is not a prerequisite for the next portfolio project.

## Build useful reliability first

1. Measured15-minute mixed-power availability passed16 samples; extend testing
   only for a concrete new workload or failure, rather than treating it as24/7 proof.
2. Use bounded, persistent test jobs so SSH interruption does not lose a test's
   result. Keep a single writer/controller per repo/tab.
3. Put short build/test/definition-of-done guidance in each project. Codex
   [AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
   describes project instructions. They are context, not a security boundary.

The test runner is implemented separately in tools/job_runner.py. It calls fixed
ordinary test suites, not another AI agent. It cannot prevent machine sleep.

## Optional timed system wake — implemented in Browser Bridge0.4.0

Chrome's [power API](https://developer.chrome.com/docs/extensions/reference/api/power)
supports system wakefulness while allowing display dim/off. Browser Bridge now
provides an owner-enabled1/15/30/60-minute session with optional power permission,
countdown, Stop and release on disconnect/expiry/tab loss/restart. There is no
remote enable command. [Behavior and limits](https://github.com/FrenchieFam/chromebook-browser-bridge/blob/main/docs/keep-awake.md)
include session reconciliation and scheduling caveats.

A real one-minute expiry and a configured15-minute battery idle-Sleep session
passed on Lenovo: the owner confirmed screen off, sampled SSH/browser heartbeats
stayed healthy, and the request was inactive after its deadline. Both Chromebooks
run0.4.0; Samsung's wake session stays off. Tests are27 Python+44 JavaScript.
This does not establish closed-lid/critical-battery/managed-policy overrides,
continuous availability or browser input visibility while the display is off.
It is one-device screen-off evidence, not a battery-runtime benchmark.

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
