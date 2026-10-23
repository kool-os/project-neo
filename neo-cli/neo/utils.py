"""Utility functions for neo."""
import os
import shutil
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from rich.console import Console
from rich.table import Table
from neo.sudo_helper import run_sudo_command

console = Console()

# Mapping of known aliases to canonical backend names
BACKEND_ALIASES = {
    "ebuild": "ebuild",
    "portage": "ebuild",
    "emerge": "ebuild",
    "flatp": "flatp",
    "flatpak": "flatp",
    "brew": "brew",
    "homebrew": "brew",
    "linuxbrew": "brew",
    "cask": "cask",
    "ebins": "ebins",
    "binpkg": "ebins",
    "binary": "ebins",
}

def check_command_exists(cmd: str) -> bool:
    """Check if an executable command exists in PATH or standard paths."""
    if shutil.which(cmd):
        return True
    common_paths = [
        f"/home/linuxbrew/.linuxbrew/bin/{cmd}",
        f"/usr/bin/{cmd}",
        f"/usr/local/bin/{cmd}",
        f"/opt/bin/{cmd}",
    ]
    for p in common_paths:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return True
    return False

def parse_package_spec(spec: str) -> Tuple[str, Optional[str]]:
    """
    Parse a package specification string into (package_name, backend_alias).
    Supports formats like:
      - 'vim:ebuild'
      - 'vim :ebuild'
      - 'firefox :flatp'
      - 'python' -> ('python', None)
      - 'app-editors/vim' -> ('app-editors/vim', None)
    """
    cleaned = spec.strip()
    if ":" in cleaned:
        # Check right-most colon
        idx = cleaned.rfind(":")
        candidate_pkg = cleaned[:idx].strip()
        candidate_backend = cleaned[idx + 1:].strip().lower()

        # Check if candidate_backend is a recognized alias
        if candidate_backend in BACKEND_ALIASES:
            return candidate_pkg, BACKEND_ALIASES[candidate_backend]

    return cleaned, None

def run_command(
    cmd: Union[str, List[str]],
    sudo: bool = False,
    capture: bool = True,
    print_output: bool = True,
    line_callback: Optional[Callable[[str], None]] = None,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[int, str]:
    """
    Run a shell command with optional sudo support and real-time streaming.
    Returns (returncode, output_text).
    """
    if sudo:
        return run_sudo_command(
            cmd=cmd,
            capture=capture,
            print_output=print_output,
            line_callback=line_callback,
        )

    # Prepare command
    if isinstance(cmd, str):
        cmd_args = cmd
        shell_mode = True
    else:
        cmd_args = cmd
        shell_mode = False

    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)

    # Ensure linuxbrew is in PATH
    brew_bin = "/home/linuxbrew/.linuxbrew/bin"
    if brew_bin not in cmd_env.get("PATH", ""):
        cmd_env["PATH"] = f"{brew_bin}:{cmd_env.get('PATH', '')}"

    output_lines: List[str] = []

    try:
        proc = subprocess.Popen(
            cmd_args,
            shell=shell_mode,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=cmd_env,
        )

        with proc.stdout:
            for line in iter(proc.stdout.readline, ""):
                output_lines.append(line)
                if print_output:
                    try:
                        sys.stdout.write(line)
                        sys.stdout.flush()
                    except Exception:
                        pass
                if line_callback:
                    try:
                        line_callback(line)
                    except Exception:
                        pass

        proc.wait()
        return proc.returncode, "".join(output_lines)

    except Exception as e:
        err = f"Failed to execute command '{cmd}': {e}\n"
        if print_output:
            try:
                sys.stderr.write(err)
            except Exception:
                pass
        if line_callback:
            try:
                line_callback(err)
            except Exception:
                pass
        return 1, err

def format_table(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> Table:
    """
    Construct a Rich Table from a list of dicts.
    """
    table = Table(title=title, show_header=True, header_style="bold cyan")

    if not data:
        table.add_column("Info")
        table.add_row("No packages found.")
        return table

    if not columns:
        columns = ["name", "version", "backend", "installed", "description"]

    # Filter columns that exist in at least one item
    actual_columns = [col for col in columns if any(col in d for d in data)]
    if not actual_columns:
        actual_columns = list(data[0].keys())

    for col in actual_columns:
        header_name = col.replace("_", " ").title()
        if col == "name":
            table.add_column(header_name, style="bold green")
        elif col == "version":
            table.add_column(header_name, style="yellow")
        elif col == "backend":
            table.add_column(header_name, style="magenta")
        elif col == "installed":
            table.add_column(header_name, style="cyan", justify="center")
        else:
            table.add_column(header_name)

    for row in data:
        row_vals = []
        for col in actual_columns:
            val = row.get(col, "")
            if col == "installed":
                row_vals.append("✓" if val else "✗")
            else:
                row_vals.append(str(val) if val is not None else "")
        table.add_row(*row_vals)

    return table
