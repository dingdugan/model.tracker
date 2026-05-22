"""Dynamic registry: import every module in vendors/ + benchmarks/ and collect scrapers."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable

from .base import BenchmarkScraper, VendorScraper


def discover_vendor_scrapers() -> list[VendorScraper]:
    return list(_discover("scrapers.vendors", VendorScraper))


def discover_benchmark_scrapers() -> list[BenchmarkScraper]:
    return list(_discover("scrapers.benchmarks", BenchmarkScraper))


def _discover(package_name: str, base_cls: type) -> Iterable:
    pkg = importlib.import_module(package_name)
    seen: set[str] = set()
    for mod_info in pkgutil.iter_modules(pkg.__path__):
        if mod_info.name.startswith("_"):
            continue
        module_full = f"{package_name}.{mod_info.name}"
        module = importlib.import_module(module_full)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if not (
                isinstance(attr, type)
                and issubclass(attr, base_cls)
                and attr is not base_cls
                and not attr.__name__.startswith("_")
            ):
                continue
            # Only register if the class was defined in THIS module (not imported)
            if getattr(attr, "__module__", None) != module_full:
                continue
            # Skip abstract subclasses that don't set the identifier
            ident = getattr(attr, "vendor_id", None) or getattr(attr, "benchmark", None)
            if not ident:
                continue
            key = f"{module_full}.{attr.__name__}"
            if key in seen:
                continue
            seen.add(key)
            yield attr()
