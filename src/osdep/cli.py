#!/usr/bin/env python3
"""
CLI commands for dependency management.

Provides the generic ``osdep`` command-line interface for installing, validating,
and uninstalling OpenStudio and OpenStudio-HPXML.
"""

import click

from .config import (
    check_version_compatibility,
    get_compatible_hpxml_versions,
    get_known_openstudio_versions,
    resolve_config,
)
from .manager import DependencyManager


def validate_dependencies(
    interactive=True,
    skip_deps=False,
    check_only=False,
    install_quiet=False,
    hpxml_path=None,
    openstudio_path=None,
    config=None,
    include_hpxml=False,
):
    """
    Convenience function to validate OpenStudio dependencies.

    Args:
        interactive (bool): Whether to prompt user for installation choices.
            Default: True
        skip_deps (bool): Skip all dependency validation. Default: False
        check_only (bool): Only check dependencies, don't install.
            Default: False
        install_quiet (bool): Automatically install missing dependencies.
            Default: False
        hpxml_path (str|Path): Custom OpenStudio-HPXML installation path.
            Default: None (use environment variables or defaults)
        openstudio_path (str|Path): Custom OpenStudio installation path.
            Default: None (use environment variables or defaults)
        config (DependencyConfig|dict): Required versions. Default: None
            (use the injected module default or packaged defaults).
        include_hpxml (bool): Also install/check OpenStudio-HPXML.
            Default: False (OpenStudio only)

    Returns:
        bool: True if all dependencies are satisfied or successfully
            installed, False otherwise

    Example:
        >>> # Interactive validation with prompts
        >>> validate_dependencies()

        >>> # Automatic installation with custom paths
        >>> validate_dependencies(install_quiet=True, interactive=False, hpxml_path="/custom/hpxml")

        >>> # Check only, no installation
        >>> validate_dependencies(check_only=True)

        >>> # Install OpenStudio and HPXML
        >>> validate_dependencies(install_quiet=True, include_hpxml=True)
    """
    manager = DependencyManager(
        interactive=interactive,
        skip_deps=skip_deps,
        install_quiet=install_quiet,
        hpxml_path=hpxml_path,
        openstudio_path=openstudio_path,
        config=config,
        include_hpxml=include_hpxml,
    )

    if check_only:
        return manager.check_only()
    else:
        return manager.validate_all()


def verify_installation(config=None, hpxml_path=None, openstudio_path=None, include_hpxml=False):
    """
    Verify a working OpenStudio + OpenStudio-HPXML installation.

    This is the generic verification step: it confirms the dependency binaries are
    present and detected. Consuming applications can layer their own
    application-specific verification (e.g. running a conversion) on top of this.

    Args:
        config (DependencyConfig|dict): Required versions. Default: None.
        hpxml_path (str|Path): Custom OpenStudio-HPXML path. Default: None.
        openstudio_path (str|Path): Custom OpenStudio path. Default: None.
        include_hpxml (bool): Also verify OpenStudio-HPXML. Default: False.

    Returns:
        bool: True if all dependencies are detected, False otherwise.
    """
    click.echo("🧪 OpenStudio Dependency Verification")
    click.echo("=" * 40)

    manager = DependencyManager(
        interactive=False,
        config=config,
        hpxml_path=hpxml_path,
        openstudio_path=openstudio_path,
        include_hpxml=include_hpxml,
    )
    ok = manager.check_only()

    click.echo("\n" + "=" * 40)
    if ok:
        click.echo("🎉 Verification passed!")
    else:
        click.echo("⚠️  Verification failed. Run 'osdep --auto-install' to install dependencies.")
    return ok


def _build_config_overrides(args):
    """Build a config override dict from CLI version flags, or None if none given."""
    overrides = {}
    if args.openstudio_version:
        overrides["openstudio_version"] = args.openstudio_version
    if args.openstudio_sha:
        overrides["openstudio_sha"] = args.openstudio_sha
    if args.hpxml_version:
        overrides["openstudio_hpxml_version"] = args.hpxml_version
    if not overrides:
        return None
    # Merge over packaged/injected defaults so partial overrides are allowed
    cfg = resolve_config(overrides)
    warnings = check_version_compatibility(cfg.openstudio_version, cfg.openstudio_hpxml_version)
    for w in warnings:
        click.echo(click.style(f"WARNING: {w}", fg="yellow"), err=True)
    return cfg


def main():
    """Main entry point for the generic ``osdep`` dependency tool."""
    import argparse
    import sys

    os_versions = get_known_openstudio_versions()
    hpxml_by_os = {
        v: get_compatible_hpxml_versions(v) for v in os_versions
    }
    version_lines = "\n".join(
        f"  OpenStudio {v}:  {', '.join(hpxml_by_os[v])}"
        for v in os_versions
    )

    parser = argparse.ArgumentParser(
        prog="osdep",
        description="Install and manage OpenStudio, EnergyPlus, and OpenStudio-HPXML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available versions:
{version_lines}

Examples:
  %(prog)s                        # Check dependencies and prompt to install if missing
  %(prog)s --check-only           # Only check dependencies, don't install
  %(prog)s --auto-install         # Automatically install missing dependencies (no prompts)
  %(prog)s --verify               # Verify a working installation
  %(prog)s --uninstall            # Uninstall OpenStudio and OpenStudio-HPXML
  %(prog)s --openstudio-version 3.10.0 --auto-install  # Install a specific version
  %(prog)s --with-hpxml --auto-install             # Also install OpenStudio-HPXML
        """,
    )

    parser.add_argument(
        "--check-only", action="store_true", help="Only check dependencies, don't install"
    )
    parser.add_argument(
        "--auto-install",
        action="store_true",
        help="Automatically install missing dependencies without prompts (recommended)",
    )
    parser.add_argument(
        "--install-quiet",
        action="store_true",
        help="Alias for --auto-install",
    )
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency validation")
    parser.add_argument(
        "--with-hpxml",
        action="store_true",
        help="Also install/check/uninstall OpenStudio-HPXML (not included by default)",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall OpenStudio and OpenStudio-HPXML dependencies",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify a working OpenStudio + OpenStudio-HPXML installation",
    )
    parser.add_argument(
        "--hpxml-path", type=str, metavar="PATH", help="Custom OpenStudio-HPXML installation path"
    )
    parser.add_argument(
        "--openstudio-path", type=str, metavar="PATH", help="Custom OpenStudio installation path"
    )
    parser.add_argument(
        "--openstudio-version",
        type=str,
        metavar="VERSION",
        help=f"Override the required OpenStudio version (valid: {', '.join(os_versions)})",
    )
    parser.add_argument(
        "--openstudio-sha",
        type=str,
        metavar="SHA",
        help="Override the required OpenStudio build hash",
    )
    all_hpxml = sorted(
        {v for versions in hpxml_by_os.values() for v in versions},
        reverse=True,
    )
    parser.add_argument(
        "--hpxml-version",
        type=str,
        metavar="VERSION",
        help=f"Override the required OpenStudio-HPXML version (valid: {', '.join(all_hpxml)})",
    )

    args = parser.parse_args()
    config = _build_config_overrides(args)

    if args.verify:
        success = verify_installation(
            config=config,
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            include_hpxml=args.with_hpxml,
        )
    elif args.uninstall:
        manager = DependencyManager(
            interactive=True,  # Uninstall is always interactive for safety
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            config=config,
            include_hpxml=args.with_hpxml,
        )
        success = manager.uninstall_dependencies()
    elif args.check_only:
        success = validate_dependencies(
            check_only=True,
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            config=config,
            include_hpxml=args.with_hpxml,
        )
    elif args.install_quiet or args.auto_install:
        success = validate_dependencies(
            interactive=False,
            install_quiet=True,
            skip_deps=args.skip_deps,
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            config=config,
            include_hpxml=args.with_hpxml,
        )
    else:
        # Default interactive mode
        success = validate_dependencies(
            interactive=True,
            skip_deps=args.skip_deps,
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            config=config,
            include_hpxml=args.with_hpxml,
        )

    sys.exit(0 if success else 1)
