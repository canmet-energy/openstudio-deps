"""
Integration tests for Linux OpenStudio and HPXML installation.

These tests verify the complete installation workflow on Linux,
including downloading, extracting, and validating dependencies.

Run with:  pytest -m integration tests/integration/test_linux_installation.py -v
"""

import os
import platform
import shutil
import tempfile
from pathlib import Path

import pytest

from osdep import DependencyManager


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific tests")
@pytest.mark.integration
class TestLinuxInstallation:
    """Integration tests for Linux OpenStudio + HPXML installation."""

    @pytest.fixture(autouse=True)
    def setup_temp_paths(self, tmp_path):
        """Create isolated temp directories so tests don't pollute the real system."""
        self.openstudio_path = tmp_path / "openstudio"
        self.hpxml_path = tmp_path / "openstudio-hpxml"

    def _make_manager(self, **overrides):
        defaults = dict(
            interactive=False,
            install_quiet=True,
            openstudio_path=self.openstudio_path,
            hpxml_path=self.hpxml_path,
        )
        defaults.update(overrides)
        return DependencyManager(**defaults)

    # --------------------------------------------------------------------- #
    # OpenStudio
    # --------------------------------------------------------------------- #

    def test_install_openstudio(self):
        """Full download-extract-validate cycle for OpenStudio on Linux."""
        dm = self._make_manager()

        result = dm._install_openstudio()
        assert result is True, "OpenStudio installation should succeed"

        # The binary should now exist under the target path
        binary = self.openstudio_path / "bin" / "openstudio"
        assert binary.exists(), f"Expected binary at {binary}"

        # Smoke-test the binary
        import subprocess

        proc = subprocess.run(
            [str(binary), "--version"], capture_output=True, text=True, timeout=15
        )
        assert proc.returncode == 0, f"openstudio --version failed: {proc.stderr}"
        assert dm.REQUIRED_OPENSTUDIO_VERSION in proc.stdout

    # --------------------------------------------------------------------- #
    # OpenStudio-HPXML
    # --------------------------------------------------------------------- #

    def test_install_openstudio_hpxml(self):
        """Full download-extract-validate cycle for OpenStudio-HPXML."""
        dm = self._make_manager()

        result = dm._install_openstudio_hpxml()
        assert result is True, "HPXML installation should succeed"

        # Workflow script must be present
        workflow = self.hpxml_path / "workflow" / "run_simulation.rb"
        assert workflow.exists(), f"Expected workflow script at {workflow}"

    # --------------------------------------------------------------------- #
    # Full dependency workflow
    # --------------------------------------------------------------------- #

    def test_install_dependencies_end_to_end(self):
        """install_dependencies() should install both components and validate."""
        dm = self._make_manager()

        result = dm.install_dependencies()
        assert result is True, "install_dependencies should succeed"

        # OpenStudio should be satisfied (may be at tmp_path or already on PATH)
        from osdep.validators import check_openstudio, check_openstudio_hpxml

        assert check_openstudio(dm), "OpenStudio should be detected after install"
        assert check_openstudio_hpxml(dm), "HPXML should be detected after install"

    # --------------------------------------------------------------------- #
    # Uninstall
    # --------------------------------------------------------------------- #

    def test_uninstall_openstudio(self):
        """Install then uninstall OpenStudio; directory should be removed."""
        dm = self._make_manager()

        # Install first
        assert dm._install_openstudio() is True

        # Uninstall
        assert dm._uninstall_openstudio() is True

        # Installation directory should be gone
        assert not self.openstudio_path.exists(), "Install dir should be removed after uninstall"

    def test_uninstall_openstudio_hpxml(self):
        """Install then uninstall HPXML; directory should be removed."""
        dm = self._make_manager()

        # Install first
        assert dm._install_openstudio_hpxml() is True

        # Uninstall
        assert dm._uninstall_openstudio_hpxml() is True

        # Installation directory should be gone
        assert not self.hpxml_path.exists(), "Install dir should be removed after uninstall"
