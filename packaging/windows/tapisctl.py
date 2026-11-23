"""Console companion of Tapis.exe (PyInstaller): `tapisctl status`, `tapisctl start`, `tapisctl mcp`, ...

Tapis.exe is a windowed program, so it cannot print to a terminal or talk over stdin/stdout.
tapisctl.exe is the same code built as a console program for terminals, scripts and AI agents.
"""
import sys

from noise_filter.cli import main

if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["mcp"]:
        sys.exit(main(["mcp"]))
    sys.exit(main(["ctl", *(args or ["--help"])]))
