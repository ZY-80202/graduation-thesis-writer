"""Compatibility entrypoint for graduation-thesis-writer.

The implementation package remains ``thesis_skill`` because Python module names
cannot contain hyphens. Use ``python -m graduation_thesis_writer`` as the local
command entrypoint.
"""

from thesis_skill import __version__

__all__ = ["__version__"]
