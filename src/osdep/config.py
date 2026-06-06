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
        """Build a DependencyConfig from a dict, validating required fields."""
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
        merged = {**_load_packaged_defaults(), **overrides}
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
