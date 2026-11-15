# Chromebook workbench development

This is a small Python/standard-library toolkit with optional native C/Python input.
Keep installation lightweight and preserve the existing ChromeOS/Linux boundaries.

Run `python3 -m unittest discover -s tests` for helper changes. For optional host
input changes, also run `make -C optional/chromeos-input all check`. Do not require
ChromeOS admin access or modify power/boot settings as part of ordinary tests.

Never commit pairing configs, auth caches, keys, device endpoints, private notes,
account screenshots or test-job logs. Use synthetic fixtures in public tests.
Generated results stay outside source worktrees. Use one writer per worktree.

Read docs/validation.md and working-together.md before changing capability claims.
Distinguish unit tests, live checks, one lid cycle and full reboot recovery. A
job runner is not a sandbox or an AI agent. Do not silently add network listeners,
model sessions, scheduled agent loops or browser reattachment.
