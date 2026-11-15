# Trust and boundaries

This is an early personal toolkit, not an independently audited remote-management
platform. Review its scripts and deploy only to computers/accounts you control.

- Use a dedicated client key and key-only, non-root OpenSSH user. Independently
  compare the worker's PUBLIC host-key fingerprint before first authentication.
  The pairing tool never treats network keyscan output alone as trusted.
- Tailscale account/policy controls transport access; ordinary OpenSSH still
  authenticates the Linux user. The setup does not enable Tailscale SSH, public
  Funnel, router forwarding, exit nodes or route advertisements.
- The normal-user daemon uses a private local state directory, runtime directory,
  Unix socket and0077 umask. Node/login state and SSH private keys stay on their
  respective devices. Static-package updates are manual. The published SHA-256
  checks download integrity; it is obtained from the same HTTPS package origin
  and is not independent protection against a compromised package publisher.
- Existing tailnet peers may have access under your policy. A Serve mapping is
  not a substitute for reviewing that policy, and userspace mode is not claimed
  to be a complete per-port firewall. This guide does not rewrite your ACLs.
- Browser Bridge has its own bearer token and tab-selection/stop boundaries.
  Its host/VM HTTP hop is not TLS. Do not publish a generated config.js, copy it
  between devices or expose port8765 publicly. Page content remains untrusted.
- Both agents must honor Disconnect, canceled debugging banners and explicit
  stops. SSH access must not be used to undo an owner-requested stop or silently
  re-enable browser control. Assign one writer/controller per worktree/tab.
- Optional host input is a much stronger privilege boundary: uinput devices are
  opened as root and retained by a daemon after dropping to chronos. Other
  processes under that same user can operate the private socket. It is not a
  multi-user authorization system. Its root-opened log has a root-owned parent,
  preventing the user-replaceable-log-path issue found in the original prototype.

## Public-source policy

This repo intentionally contains no paired extension configs, private SSH keys,
Tailscale state/login URLs, Codex auth caches/databases, private handoffs, actual
tailnet addresses/names/fingerprints, account screenshots or unrelated personal
backups. Generated fixtures/test keys live in temporary directories only.

Do not import your entire ~/.codex, ~/.ssh, Downloads or Drive into a public repo.
Report a reproduction with harmless fixtures; redact credentials and account
content. If a credential was exposed, revoke/rotate it before sharing evidence.
