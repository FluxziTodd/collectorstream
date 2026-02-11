"""Reports generation package for CollectorStream."""

from .generate import generate_all, DEFAULT_OUTPUT
from .landing import generate_landing_page
from .styles import CSS_APP, CSS_LANDING

__all__ = ['generate_all', 'generate_landing_page', 'DEFAULT_OUTPUT', 'CSS_APP', 'CSS_LANDING']
