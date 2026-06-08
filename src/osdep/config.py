#!/usr/bin/env python3
"""
Dependency version configuration for osdep.

The package ships sensible default versions (``resources/dependency_versions.json``).
Consumers may override them by passing a :class:`DependencyConfig` (or a plain dict)
into :class:`~osdep.manager.DependencyManager` / the module-level helpers, or by
calling :func:`set_default_config` once at startup to apply an override globally.
"""

import json
from dataclasses import dataclass
from functools import lru_cache

REQUIRED_FIELDS = ("openstudio_version", "openstudio_sha", "openstudio_hpxml_version")

# Module-level injected default. When set (via set_default_config), it is used by
# resolve_config() whenever no explicit overrides are passed. This is what lets a
# consuming application select its required versions once and have every zero-arg
# helper call (get_openstudio_binary(), etc.) resolve to those versions.
_DEFAULT_CONFIG = None


@dataclass(frozen=True)
class DependencyConfig:
    """Required versions for OpenStudio and OpenStudio-HPXML."""

    openstudio_version: str
    openstudio_sha: str
    openstudio_hpxml_version: str

    @classmethod
    def from_dict(cls, data):
        """Build a DependencyConfig from a dict, validating required fields.

        If ``openstudio_sha`` is missing but ``openstudio_version`` matches a
        known version in the catalog, the SHA is resolved automatically.
        """
        # Auto-resolve SHA from catalog if not provided
        if "openstudio_sha" not in data and "openstudio_version" in data:
            sha = lookup_openstudio_sha(data["openstudio_version"])
            if sha:
                data = {**data, "openstudio_sha": sha}

        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            raise ValueError(
                f"Missing required dependency configuration: {', '.join(missing)}. "
                f"Required fields: {', '.join(REQUIRED_FIELDS)}"
            )
        return cls(
            openstudio_version=data["openstudio_version"],
            openstudio_sha=data["openstudio_sha"],
            openstudio_hpxml_version=data["openstudio_hpxml_version"],
        )

    def as_dict(self):
        """Return a plain dict (backward-compatible with the old config dict)."""
        return {
            "openstudio_version": self.openstudio_version,
            "openstudio_sha": self.openstudio_sha,
            "openstudio_hpxml_version": self.openstudio_hpxml_version,
        }


def _load_packaged_defaults():
    """Load the package-shipped default versions from resources/dependency_versions.json."""
    from importlib import resources

    with (
        resources.files("osdep.resources")
        .joinpath("dependency_versions.json")
        .open(encoding="utf-8") as f
    ):
        return json.load(f)


@lru_cache(maxsize=1)
def _load_version_catalog():
    """Load the version catalog mapping OpenStudio versions to build SHAs."""
    from importlib import resources

    with (
        resources.files("osdep.resources")
        .joinpath("version_catalog.json")
        .open(encoding="utf-8") as f
    ):
        return json.load(f)


def lookup_openstudio_sha(version):
    """Look up the build SHA for a known OpenStudio version.

    Args:
        version (str): OpenStudio version (e.g., "3.11.0")

    Returns:
        str or None: The 10-character build SHA, or None if not in the catalog.
    """
    catalog = _load_version_catalog()
    entry = catalog.get("openstudio", {}).get(version)
    return entry["sha"] if entry else None


def get_compatible_hpxml_versions(openstudio_version):
    """Return the list of HPXML versions compatible with an OpenStudio version.

    Args:
        openstudio_version (str): OpenStudio version (e.g., "3.11.0")

    Returns:
        list[str]: Compatible HPXML version tags, or empty list if unknown.
    """
    catalog = _load_version_catalog()
    entry = catalog.get("openstudio", {}).get(openstudio_version)
    return entry.get("compatible_hpxml", []) if entry else []


def check_version_compatibility(openstudio_version, hpxml_version):
    """Check whether an OpenStudio and HPXML version pair is compatible.

    Args:
        openstudio_version (str): OpenStudio version (e.g., "3.11.0")
        hpxml_version (str): HPXML version tag (e.g., "v1.9.1")

    Returns:
        list[str]: Warning messages. Empty list if compatible or unknown.
    """
    warnings = []
    catalog = _load_version_catalog()
    os_entry = catalog.get("openstudio", {}).get(openstudio_version)
    hpxml_entry = catalog.get("openstudio_hpxml", {}).get(hpxml_version)

    if os_entry and hpxml_version not in os_entry.get("compatible_hpxml", []):
        compatible = ", ".join(os_entry["compatible_hpxml"])
        warnings.append(
            f"HPXML {hpxml_version} is not listed as compatible with "
            f"OpenStudio {openstudio_version}. Compatible HPXML versions: {compatible}"
        )

    if hpxml_entry and hpxml_entry.get("openstudio") != openstudio_version:
        warnings.append(
            f"HPXML {hpxml_version} expects OpenStudio {hpxml_entry['openstudio']}, "
            f"not {openstudio_version}"
        )

    return warnings


def get_known_openstudio_versions():
    """Return all OpenStudio versions in the catalog.

    Returns:
        list[str]: Version strings sorted newest-first.
    """
    catalog = _load_version_catalog()
    versions = list(catalog.get("openstudio", {}).keys())
    versions.sort(key=lambda v: [int(x) for x in v.split(".")], reverse=True)
    return versions


def resolve_config(overrides=None):
    """Resolve a :class:`DependencyConfig`.

    Resolution order:
    1. If ``overrides`` is a DependencyConfig, use it directly.
    2. If ``overrides`` is a dict, merge it over the packaged defaults.
    3. If ``overrides`` is None and a module default was set via
       :func:`set_default_config`, use that.
    4. Otherwise, use the package-shipped defaults.

    Args:
        overrides: A DependencyConfig, a dict of version fields, or None.

    Returns:
        DependencyConfig: The resolved configuration.
    """
    if isinstance(overrides, DependencyConfig):
        return overrides

    if overrides is None:
        if _DEFAULT_CONFIG is not None:
            return _DEFAULT_CONFIG
        return DependencyConfig.from_dict(_load_packaged_defaults())

    if isinstance(overrides, dict):
        defaults = _load_packaged_defaults()
        merged = {**defaults, **overrides}
        # If the caller overrode openstudio_version (to a *different* version)
        # but not openstudio_sha, try to resolve the SHA from the catalog.
        if (
            "openstudio_version" in overrides
            and "openstudio_sha" not in overrides
            and overrides["openstudio_version"] != defaults.get("openstudio_version")
        ):
            catalog_sha = lookup_openstudio_sha(overrides["openstudio_version"])
            if catalog_sha:
                merged["openstudio_sha"] = catalog_sha
        return DependencyConfig.from_dict(merged)

    raise TypeError(
        f"overrides must be a DependencyConfig, dict, or None, not {type(overrides).__name__}"
    )


def set_default_config(config):
    """Set the module-level default configuration applied to zero-arg resolutions.

    A consuming application calls this once at startup to inject its required
    versions, so every subsequent ``resolve_config()`` with no overrides (and thus
    every zero-arg helper call) uses those versions.

    Args:
        config: A DependencyConfig or a dict of version fields.
    """
    global _DEFAULT_CONFIG
    _DEFAULT_CONFIG = resolve_config(config)


def get_default_config():
    """Return the currently injected module default, or None if unset."""
    return _DEFAULT_CONFIG
