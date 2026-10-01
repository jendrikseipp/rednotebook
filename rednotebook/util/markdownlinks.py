"""Escape links emitted by the editor and the legacy markup converter."""

from urllib.parse import quote


def escape_destination(url):
    """Encode Markdown delimiters without changing URI syntax or percent escapes."""
    return quote(url, safe="/:?#[]@!$&'*+,;=%")


def escape_label(text):
    """Keep brackets and backslashes literal inside a link or image label."""
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
