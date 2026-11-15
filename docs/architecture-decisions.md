# Architecture research and decisions

Reviewed November15,2026. This is a small personal engineering project tested on
two Chromebooks; these choices are not a universal browser-automation benchmark.

## Keep the ChromeOS/Linux boundary explicit

[Chromium's Linux environment documentation](https://www.chromium.org/chromium-os/developer-library/guides/containers/containers-and-vms/)
explains how Linux and ChromeOS are separated. Linux tools alone do not imply
control of the native ChromeOS browser. We keep Linux SSH, the owner-connected
browser extension, and optional native host input as separate access paths.
The optional host helper has a different privilege requirement; it is not
necessary for the browser bridge and its generalized installer has not been
verified on another device.

## Use userspace transport for this setup

[Tailscale userspace networking](https://tailscale.com/docs/concepts/userspace-networking)
supports environments without a kernel tunnel device. In our tested setup,
ChromeOS host-local forwarding worked while the tested LAN route refused
connections. Userspace Tailscale plus pinned, key-only OpenSSH provided a working
private route. This does not prove that LAN forwarding fails on every Chromebook,
or that a relay is faster than a direct connection. No throughput claim is made.

## Prefer an explicit owner-connected tab

[Chrome's debugger API](https://developer.chrome.com/docs/extensions/reference/api/debugger)
provides CDP transport and targets a debuggee by tab ID. Our tool surface keeps
commands bound to that connection and offers explicit focus rather than silently
switching to the owner's active tab. Chrome's debugger permission itself remains
powerful; our application restrictions do not narrow the platform permission.
Disconnect and banner cancellation must be honored.

## Consider existing tools before growing a custom bridge

[Playwright's existing-browser extension](https://playwright.dev/mcp/configuration/browser-extension)
and [Chrome DevTools existing-session configuration](https://developer.chrome.com/docs/devtools/agents/get-started/configuration/)
are established alternatives for attaching automation to browser sessions.
They were researched, not installed or benchmarked on these two Chromebooks.
We do not claim they lack features, fail on ChromeOS, or are less secure.

The reason to keep this small bridge is its tested fit with this specific
owner-selected ChromeOS tab workflow and its compact Python/extension source.
If broad iframe/shadow-DOM support or more complete browser automation becomes
necessary, evaluate an existing maintained tool before expanding the custom API.

## Make the case study about evidence

The useful result is a reproducible workflow and a demonstrated debugging lesson:
a successful input RPC did not prove the page changed. Actual observation led to
visibility-aware input and a same-target focus action. Public documentation keeps
unit checks, live browser checks, one lid cycle, and a full reboot distinct.
Private endpoints, pairing credentials, account state and handoffs are not source
material for the public portfolio.
