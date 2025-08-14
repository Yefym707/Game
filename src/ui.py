"""Utility functions for colored terminal output using ANSI codes."""

# Simple wrapper – can be extended for Windows support (e.g. colorama) if needed.

RESET = "\x1b[0m"
BOLD = "\x1b[1m"

COLORS = {
    "black": "\x1b[30m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
}

def color(text: str, color: str, bold: bool = False) -> str:
    code = COLORS.get(color, "")
    prefix = BOLD + code if bold else code
    return f"{prefix}{text}{RESET}"
