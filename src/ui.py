# Небольшая утилита для цветного вывода в терминал (ANSI).
# Простая обёртка — можно расширять для поддержки Windows (colorama) при необходимости.

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
    "white": "\x
