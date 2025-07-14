""" pdffiller constants. """

__all__ = [
    "ENV_NO_COLOR",
    "ENV_CLICOLOR_FORCE",
    "ENV_PDFFILLER_COLOR_DARK",
]

ENV_NO_COLOR = "NO_COLOR"
""" Disable ANSI colors. """

ENV_CLICOLOR_FORCE = "CLICOLOR_FORCE"
"""ANSI colors should be enabled.

Different from 0 to enforce ANSI colors
"""

ENV_PDFFILLER_COLOR_DARK = "PDFFILLER_COLOR_DARK"
"""Use dark ANSI color scheme.

It must be different from 0 to enforce dark colors
"""
