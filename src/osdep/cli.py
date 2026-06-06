#!/usr/bin/env python3
"""
CLI commands for dependency management.

Provides the generic ``osdep`` command-line interface for installing, validating,
and uninstalling OpenStudio and OpenStudio-HPXML.
"""

import click

from .config import resolve_config
from .manager import DependencyManager


def validate_dependencies(
    interactive=True,
    skip_deps=False,
    check_only=False,
    install_quiet=False,
    hpxml_path=None,
    openstudio_path=None,
    config=None,
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
    """
    manager = DependencyManager(
        interactive=interactive,
        skip_deps=skip_deps,
        install_quiet=install_quiet,
        hpxml_path=hpxml_path,
        openstudio_path=openstudio_path,
        config=config,
    )

    if check_only:
        return manager.check_only()
    else:
        return manager.validate_all()


def verify_installation(config=None, hpxml_path=None, openstudio_path=None):
    """
    Verify a working OpenStudio + OpenStudio-HPXML installation.

    This is the generic verification step: it confirms the dependency binaries are
    present and detected. Consuming applications can layer their own
    application-specific verification (e.g. running a conversion) on top of this.

    Args:
        config (DependencyConfig|dict): Required versions. Default: None.
        hpxml_path (str|Path): Custom OpenStudio-HPXML path. Default: None.
        openstudio_path (str|Path): Custom OpenStudio path. Default: None.

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
    return resolve_config(overrides)


def main():
    """Main entry point for the generic ``osdep`` dependency tool."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="osdep",
        description="Install and manage OpenStudio, EnergyPlus, and OpenStudio-HPXML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                        # Check dependencies and prompt to install if missing
  %(prog)s --check-only           # Only check dependencies, don't install
  %(prog)s --auto-install         # Automatically install missing dependencies (no prompts)
  %(prog)s --verify               # Verify a working installation
  %(prog)s --uninstall            # Uninstall OpenStudio and OpenStudio-HPXML
  %(prog)s --openstudio-version 3.11.0 --check-only   # Override the required version
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
        help="Override the required OpenStudio version",
    )
    parser.add_argument(
        "--openstudio-sha",
        type=str,
        metavar="SHA",
        help="Override the required OpenStudio build hash",
    )
    parser.add_argument(
        "--hpxml-version",
        type=str,
        metavar="VERSION",
        help="Override the required OpenStudio-HPXML version",
    )

    args = parser.parse_args()
    config = _build_config_overrides(args)

    if args.verify:
        success = verify_installation(
            config=config,
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
        )
    elif args.uninstall:
        manager = DependencyManager(
            interactive=True,  # Uninstall is always interactive for safety
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            config=config,
        )
        success = manager.uninstall_dependencies()
    elif args.check_only:
        success = validate_dependencies(
            check_only=True,
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            config=config,
        )
    elif args.install_quiet or args.auto_install:
        success = validate_dependencies(
            interactive=False,
            install_quiet=True,
            skip_deps=args.skip_deps,
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            config=config,
        )
    else:
        # Default interactive mode
        success = validate_dependencies(
            interactive=True,
            skip_deps=args.skip_deps,
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            config=config,
        )

    sys.exit(0 if success else 1)
