# Command line and AI control

The running app can be controlled from a terminal, a script or an AI assistant. The installer adds
`tapisctl.exe` (a console companion of `Tapis.exe`) and can put it on `PATH`. From source, the
same commands are `tapis ctl …`.

## Commands

Every command prints JSON. Exit code `0` = ok, `1` = error, `3` = the app is not running.

```powershell
tapisctl status                                # on/off, devices, every setting, levels, latency
tapisctl start                                 # opens the app in the tray first if needed
tapisctl stop
tapisctl set strength=1.3 highpass_hz=100 denoise=ai gate_enabled=off
tapisctl set vocal_mode=on mix=0.8             # singing: keep harmonics, blend in 20 % original
tapisctl devices
tapisctl device --input "USB" --output "CABLE Input" [--exclusive | --shared]
tapisctl presets                               # list EQ presets
tapisctl preset voice_clarity hum_50           # tick these presets (merged into one EQ)
tapisctl preset --clear
tapisctl learn                                 # learn room noise for 3 s (filter on, stay quiet)
tapisctl launch | show | hide | quit
tapisctl help                                  # every setting with its range
```

Changes made by command go through the same controls as the window, so the window, the tray and
the saved settings always match. While the EQ presets are locked, `preset` is refused and `status`
reports `eq_locked`.

## MCP server for AI apps

`tapisctl mcp` speaks the [Model Context Protocol](https://modelcontextprotocol.io) over stdio with
these tools: `get_status`, `start_filter`, `stop_filter`, `set_settings`, `list_devices`,
`select_devices`, `list_eq_presets`, `set_eq_presets`, `learn_noise`, `show_window`, `hide_window`,
`quit_app`.

In the app, **Settings › Command line & AI control › Copy MCP setting** copies the entry for you.

Claude Desktop (`claude_desktop_config.json`):

```json
{"mcpServers": {"tapis": {"command": "C:\\Program Files\\Tapis\\tapisctl.exe", "args": ["mcp"]}}}
```

Claude Code:

```powershell
claude mcp add tapis -- "C:\Program Files\Tapis\tapisctl.exe" mcp
```

## How it works

The app listens on a local named pipe, `\\.\pipe\SkillsHUB.Tapis.<user>`, that only the
signed-in Windows user can open. Nothing listens on the network. Each request and answer is one
JSON line:

```text
{"cmd": "set", "args": {"strength": 1.2}}   ->   {"ok": true, "result": {...}}
```

The implementation is in [`noise_filter/remote.py`](../noise_filter/remote.py) (protocol),
[`noise_filter/ctl.py`](../noise_filter/ctl.py) (command line) and
[`noise_filter/mcp_server.py`](../noise_filter/mcp_server.py) (MCP).
