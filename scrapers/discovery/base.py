"""Abstract base for discovery sources."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..core.schema import DiscoveryCandidate


class DiscoverySource(ABC):
    """One per discovery signal (a vendor Models API, a models page, an RSS feed).

    ``discover()`` returns every model name the source currently advertises, as
    raw ``DiscoveryCandidate`` objects. Filtering against the registry (deciding
    which are actually *new*) happens downstream in ``core.discovery`` — sources
    stay dumb and just report what they see. A source that can't run (missing
    API key, network error) returns ``[]`` and logs; it never raises.
    """

    source: str = ""

    @abstractmethod
    def discover(self) -> list[DiscoveryCandidate]:
        ...

    def __repr__(self) -> str:
        return f"<DiscoverySource {self.source}>"
