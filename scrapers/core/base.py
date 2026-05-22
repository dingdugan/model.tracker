"""Abstract base for vendor and benchmark scrapers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .schema import ScrapeResult


class VendorScraper(ABC):
    """One per vendor. Subclasses override `scrape()`."""

    vendor_id: str = ""

    @abstractmethod
    def scrape(self) -> ScrapeResult:
        ...

    def __repr__(self) -> str:
        return f"<VendorScraper {self.vendor_id}>"


class BenchmarkScraper(ABC):
    """One per benchmark source (lmsys, artificial_analysis, academic)."""

    benchmark: str = ""

    @abstractmethod
    def scrape(self) -> ScrapeResult:
        ...

    def __repr__(self) -> str:
        return f"<BenchmarkScraper {self.benchmark}>"
