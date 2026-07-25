from __future__ import annotations

class SourceUnavailable(Exception):
    """Raised when a market-data source cannot return usable data this run."""
