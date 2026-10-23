"""Sudo operations helper using pexpect and config-managed credentials."""
import getpass
import os
import re
import sys
from typing import Callable, List, Optional, Tuple, Union
import pexpect
from neo.config import get_sudo_password, set_sudo_password

_SESSION_SUDO_PASSWORD: Optional[str] = None

def get_or_prompt_sudo_password() -> str:
    """Retrieve sudo password from config, session cache, or prompt the user."""
    global _SESSION_SUDO_PASSWORD
    if _SESSION_SUDO_PASSWORD:
        return _SESSION_SUDO_PASSWORD

    configured = get_sudo_password()
    if configured:
        _SESSION_SUDO_PASSWORD = configured
        return configured

    # If running interactively, prompt
    if sys.stdin.isatty():
        pwd = getpass.getpass("[neo] sudo password required: ")
        if pwd:
            _SESSION_SUDO_PASSWORD = pwd
            # Prompt whether to save
            try:
                save_choice = input("[neo] Save password to ~/.config/neo/config.toml? [y/N]: ").strip().lower()
                if save_choice in ("y", "yes"):
                    set_sudo_password(pwd, store=True)
            except Exception:
                pass
            return pwd

    # Fallback to default testing password if non-interactive
    _SESSION_SUDO_PASSWORD = "kdekde"
    return "kdekde"

def run_sudo_command(
    cmd: Union[str, List[str]],
    timeout: Optional[int] = 3600,
    capture: bool = True,
    print_output: bool = True,
    line_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[int, str]:
    """
    Executes a command using sudo and pexpect, supplying the password automatically.
    Returns (exit_code, output_text).
    """
    password = get_or_prompt_sudo_password()

    if isinstance(cmd, list):
        command_str = " ".join(cmd)
    else:
        command_str = cmd

    # Form sudo invocation: sudo -S to read from stdin, or spawn direct sudo
    sudo_cmd = f"sudo -k {command_str}"

    output_lines: List[str] = []

    try:
        child = pexpect.spawn(
            sudo_cmd,
            encoding="utf-8",
            codec_errors="replace",
            timeout=timeout,
            dimensions=(30, 120),
            env={**os.environ, "TERM": "dumb", "SUDO_ASKPASS": ""},
        )

        # Match potential sudo password prompt
        prompt_index = child.expect(
            [
                pexpect.TIMEOUT,
                pexpect.EOF,
                r"\[sudo\] password for .*: ?",
                r"Password: ?",
                r"password for .*: ?",
            ],
            timeout=5,
        )

        if prompt_index in (2, 3, 4):
            child.sendline(password)
        elif prompt_index == 1:
            # Command already completed without asking for password
            pass

        # Stream output line by line
        while True:
            try:
                line = child.readline()
                if not line:
                    break
                # Filter out raw password prompt lines
                if re.search(r"password for |Password:", line, re.IGNORECASE):
                    continue
                output_lines.append(line)
                if print_output:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                if line_callback:
                    line_callback(line)
            except pexpect.TIMEOUT:
                continue
            except pexpect.EOF:
                break

        child.close()
        exit_code = child.exitstatus if child.exitstatus is not None else 0
        return exit_code, "".join(output_lines)

    except pexpect.ExceptionPexpect as e:
        error_msg = f"Sudo execution error: {e}\n"
        if print_output:
            sys.stderr.write(error_msg)
        if line_callback:
            line_callback(error_msg)
        return 1, error_msg
