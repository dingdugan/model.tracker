"""Pydantic schemas for scraper output."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


Modality = Literal["text", "image", "audio", "video", "code", "embedding"]
ModelStatus = Literal["active", "preview", "deprecated", "retired"]


class ModelRecord(BaseModel):
    """One model entry. Vendor scrapers emit these."""

    vendor_id: str
    slug: str                           # 'gpt-5', 'claude-opus-4-7'
    name: str                           # display name
    aliases: list[str] = Field(default_factory=list)  # extra external names that
                                        # resolve to this model: benchmark display
                                        # names, dated snapshots, platform-specific
                                        # IDs. slug + name are matched automatically.
    family: Optional[str] = None        # 'gpt', 'claude', 'gemini'
    release_date: Optional[date] = None
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    modalities: list[Modality] = Field(default_factory=lambda: ["text"])
    is_open_weight: bool = False
    license: Optional[str] = None       # SPDX id or shorthand: 'apache-2.0','mit','llama-4','gemma','proprietary'
    parameters_b: Optional[float] = None
    status: ModelStatus = "active"
    announcement_url: Optional[str] = None
    description: Optional[str] = None

    @property
    def id(self) -> str:
        return f"{self.vendor_id}/{self.slug}"


class PriceRecord(BaseModel):
    """One price quote. Input/output in USD per million tokens."""

    model_id: str
    input_per_mtok: Optional[float] = None
    output_per_mtok: Optional[float] = None
    cached_input_per_mtok: Optional[float] = None
    cache_write_per_mtok: Optional[float] = None
    batch_input_per_mtok: Optional[float] = None
    batch_output_per_mtok: Optional[float] = None
    currency: str = "USD"
    effective_date: date = Field(default_factory=date.today)
    source_url: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()


class BenchmarkRecord(BaseModel):
    """One (model, benchmark) score."""

    model_id: str
    benchmark_name: str                 # 'arena-elo' | 'mmlu' | ...
    score: float
    score_unit: Literal["elo", "pct", "pass@1", "raw"]
    score_max: Optional[float] = None   # 100 for pct, null for elo
    source: str                         # 'lmsys' | 'artificial-analysis' | 'official'
    source_url: Optional[str] = None
    measured_at: Optional[date] = None


class DiscoveryCandidate(BaseModel):
    """A model name seen in the wild that does NOT resolve to a known model.

    Emitted by discovery sources (vendor Models APIs, pages) and by ingestion
    scrapers when a reported name fails to resolve. It is only ever *proposed* —
    the discovery layer never writes to the models table.
    """

    source: str                          # 'vendor-api:anthropic' | 'benchmark:lmsys' | ...
    reported_name: str                   # raw name/id as the source reported it
    vendor_guess: Optional[str] = None   # best-effort vendor id
    raw_context: dict = Field(default_factory=dict)


class ScrapeResult(BaseModel):
    """What every vendor / benchmark scraper returns."""

    vendor_id: Optional[str] = None
    benchmark: Optional[str] = None
    models: list[ModelRecord] = Field(default_factory=list)
    prices: list[PriceRecord] = Field(default_factory=list)
    benchmarks: list[BenchmarkRecord] = Field(default_factory=list)
    unresolved: list[DiscoveryCandidate] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def label(self) -> str:
        return self.vendor_id or self.benchmark or "unknown"

    def summary(self) -> str:
        return (
            f"{self.label}: "
            f"{len(self.models)} models, "
            f"{len(self.prices)} prices, "
            f"{len(self.benchmarks)} scores"
        )
