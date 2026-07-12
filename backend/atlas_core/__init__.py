"""Atlas core: the framework-free simulation engine and city data layer.

This package deliberately has no dependency on FastAPI, the database, or Redis.
Those live in the ``api`` and ``atlas_core.persistence`` layers, which depend on
this core — never the reverse.
"""

__version__ = "0.1.0"
