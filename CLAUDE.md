# CLAUDE.md

Instructions for Claude and other AI agents working in this repository are in [AGENTS.md](AGENTS.md).
Read it first, then [CHANGELOG.md](CHANGELOG.md) for what changed recently.

Key facts that are easy to miss:

- **The app is called Tapis** (Javanese for a sieve or filter). It was called **Noise Filter** until
  v0.11.0 (2026-11-23). The repository moved from `SkillsHUB-Electronics/Noise-Filter` to
  `SkillsHUB-Electronics/tapis`; old links redirect. If a local clone still points to the old URL, run
  `git remote set-url origin https://github.com/SkillsHUB-Electronics/tapis`.
- New names: `Tapis.exe`, `Tapis-Setup-<version>.exe`, `C:\Program Files\Tapis`, `%APPDATA%\Tapis`,
  command-line companion `tapisctl` (was `nfctl`), MCP server `tapis`, pip command `tapis`.
- Old names kept on purpose: Python package `noise_filter`, C++ core `nf-core` / `nf-cli`, Cloudflare
  Worker `noise-filter-samples` (installed apps upload to its URL). Do not rename them without a
  migration plan.
- User data from the old name is moved by `noise_filter/paths.py`; the "Start with Windows" entry by
  `noise_filter/ui/autostart.py` and the installer.
- Default branch: `ccr-b550d426-d4tmx2`. Releases are published by the maintainer.
- v0.11.1 (2026-11-23): microphone/network errors are explained to the user. Audio errors go through
  `noise_filter/audio/errors.py` + `noise_filter/ui/mic_help.py`, HTTPS through `noise_filter/net.py`
  (Windows trust store). "Record noise" opens only the microphone (`nf:none` output). The sample
  Worker was verified working from Windows runners; failed uploads come from users' PCs or networks.
