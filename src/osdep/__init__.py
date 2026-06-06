"""
osdep — reusable OpenStudio + OpenStudio-HPXML dependency manager.

Provides modular detection, validation, and installation of OpenStudio and
OpenStudio-HPXML for any consuming application. Required versions ship as
package defaults and can be overridden per-call (via ``config=``) or globally
via :func:`set_default_config`.
"""

import shutil
from pathlib import Path

from .cli import main
from .cli import validate_dependencies
from .cli import verify_installation
from .config import DependencyConfig
from .config import get_default_config
from .config import resolve_config
from .config import set_default_config
from .download_utils import download_file
from .download_utils import safe_echo
from .manager import DependencyManager
from .platform_utils import get_default_hpxml_path
from .platform_utils import get_default_openstudio_path
from .platform_utils import get_openstudio_paths
from .platform_utils import get_user_data_dir


# Lightweight helper functions (don't create DependencyManager instances!)
def get_dependency_paths(config=None):
    """Get all dependency paths in a single call."""
    cfg = resolve_config(config)
    openstudio_binary = get_openstudio_binary(cfg)
    hpxml_os_path = get_hpxml_os_path(cfg)

    # EnergyPlus is bundled with OpenStudio
    energyplus_binary = None
    if openstudio_binary:
        openstudio_dir = Path(openstudio_binary).parent.parent
        if Path(openstudio_binary).name == "openstudio.exe":
            energyplus_binary = str(openstudio_dir / "EnergyPlus" / "energyplus.exe")
        else:
            energyplus_binary = str(openstudio_dir / "EnergyPlus" / "energyplus")

        if not Path(energyplus_binary).exists():
            energyplus_binary = None

    return {
        "openstudio_binary": openstudio_binary,
        "hpxml_os_path": hpxml_os_path,
        "energyplus_binary": energyplus_binary,
    }


def get_openstudio_binary(config=None):
    """Get OpenStudio binary path without creating DependencyManager."""
    cfg = resolve_config(config)
    paths = get_openstudio_paths(cfg.openstudio_version, cfg.openstudio_sha, None)

    for path in paths:
        if Path(path).exists():
            return str(path)

    # Fallback to system PATH
    system_path = shutil.which("openstudio")
    if system_path:
        return system_path

    return None


def get_hpxml_os_path(config=None):
    """Get OpenStudio-HPXML path without creating DependencyManager."""
    cfg = resolve_config(config)
    hpxml_path = get_default_hpxml_path(cfg.openstudio_hpxml_version, None)

    if hpxml_path.exists():
        return str(hpxml_path)

    return None


def get_energyplus_binary(config=None):
    """Get EnergyPlus binary path."""
    paths = get_dependency_paths(config)
    return paths["energyplus_binary"]


# Aliases for backward compatibility
get_openstudio_path = get_openstudio_binary
get_openstudio_hpxml_path = get_hpxml_os_path
get_openstudio_path_static = get_openstudio_binary
get_openstudio_hpxml_path_static = get_hpxml_os_path

# Export all public APIs
__all__ = [
    # Core classes and functions
    "DependencyManager",
    "DependencyConfig",
    "validate_dependencies",
    "verify_installation",
    "main",
    # Config injection
    "resolve_config",
    "set_default_config",
    "get_default_config",
    # Download utilities
    "download_file",
    "safe_echo",
    # Compatibility functions
    "get_dependency_paths",
    "get_openstudio_binary",
    "get_hpxml_os_path",
    "get_energyplus_binary",
    "get_openstudio_path",
    "get_openstudio_hpxml_path",
    "get_openstudio_path_static",
    "get_openstudio_hpxml_path_static",
    # Platform utilities
    "get_user_data_dir",
    "get_openstudio_paths",
    "get_default_hpxml_path",
    "get_default_openstudio_path",
]
