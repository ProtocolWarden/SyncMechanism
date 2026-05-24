# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main`  | ✅ Yes     |

Only the current `main` branch receives security fixes.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report security issues privately by emailing **coding.projects.1642@proton.me**.

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations (optional)

You will receive an acknowledgment within 72 hours. We aim to release a fix
within 14 days of a confirmed report, depending on severity and complexity.

## Scope

SyncMechanism downloads, installs, and launches Syncthing, and registers a
login-startup entry. The primary security surface is:

- **Binary download/install** — `install.py` fetches version-pinned Syncthing
  release archives from `github.com/syncthing/syncthing` over HTTPS and
  extracts them; a compromised release or man-in-the-middle could deliver a
  malicious binary.
- **Privileged install** — on Linux the binary is installed via `sudo install`
  into `/usr/local/bin`.
- **Archive extraction** — release archives are extracted with `extractall`;
  path-traversal entries in a malicious archive are a concern.
- **Login-startup registration** — writes an XDG autostart entry (Linux) or an
  HKCU Run registry value (Windows) that launches the tray at login.

## Out of Scope

- Vulnerabilities in Syncthing itself; those are upstream concerns.
- Vulnerabilities in any private layer that integrates this mechanism.
- Issues requiring physical access to the host machine.
