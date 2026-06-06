"""Tests for osdep config injection and the public API surface."""

import osdep
import pytest
from osdep import DependencyConfig
from osdep import resolve_config
from osdep import set_default_config
from osdep.config import _load_packaged_defaults


@pytest.fixture(autouse=True)
def _reset_default_config():
    """Ensure the module-level injected default doesn't leak between tests."""
    import osdep.config as cfgmod

    saved = cfgmod._DEFAULT_CONFIG
    cfgmod._DEFAULT_CONFIG = None
    yield
    cfgmod._DEFAULT_CONFIG = saved


def test_packaged_defaults_present():
    defaults = _load_packaged_defaults()
    assert defaults["openstudio_version"]
    assert defaults["openstudio_sha"]
    assert defaults["openstudio_hpxml_version"]


def test_resolve_config_uses_packaged_defaults_when_none():
    cfg = resolve_config()
    defaults = _load_packaged_defaults()
    assert cfg.openstudio_version == defaults["openstudio_version"]
    assert cfg.openstudio_hpxml_version == defaults["openstudio_hpxml_version"]


def test_resolve_config_passthrough_dataclass():
    c = DependencyConfig("1.0.0", "deadbeef", "v2.0.0")
    assert resolve_config(c) is c


def test_resolve_config_partial_dict_merges_over_defaults():
    defaults = _load_packaged_defaults()
    cfg = resolve_config({"openstudio_version": "9.9.9"})
    assert cfg.openstudio_version == "9.9.9"
    # untouched fields fall back to packaged defaults
    assert cfg.openstudio_sha == defaults["openstudio_sha"]
    assert cfg.openstudio_hpxml_version == defaults["openstudio_hpxml_version"]


def test_from_dict_validates_required_fields():
    with pytest.raises(ValueError):
        DependencyConfig.from_dict({"openstudio_version": "1.0.0"})


def test_resolve_config_rejects_bad_type():
    with pytest.raises(TypeError):
        resolve_config(12345)


def test_set_default_config_affects_zero_arg_resolution():
    set_default_config(DependencyConfig("3.0.0", "aaa", "v3.0.0"))
    assert resolve_config().openstudio_version == "3.0.0"
    # explicit overrides still win over the injected default
    assert resolve_config({"openstudio_version": "4.0.0"}).openstudio_version == "4.0.0"


def test_manager_uses_injected_config():
    set_default_config(DependencyConfig("3.0.0", "aaa", "v3.0.0"))
    m = osdep.DependencyManager(interactive=False)
    assert m.REQUIRED_OPENSTUDIO_VERSION == "3.0.0"
    assert m.OPENSTUDIO_BUILD_HASH == "aaa"
    assert m.REQUIRED_HPXML_VERSION == "v3.0.0"


def test_manager_explicit_config_overrides_injected():
    set_default_config(DependencyConfig("3.0.0", "aaa", "v3.0.0"))
    m = osdep.DependencyManager(interactive=False, config={"openstudio_version": "5.5.5"})
    assert m.REQUIRED_OPENSTUDIO_VERSION == "5.5.5"


def test_public_api_exports():
    for name in [
        "DependencyManager",
        "DependencyConfig",
        "validate_dependencies",
        "verify_installation",
        "get_openstudio_binary",
        "get_hpxml_os_path",
        "get_openstudio_path",
        "set_default_config",
        "resolve_config",
        "download_file",
        "safe_echo",
    ]:
        assert hasattr(osdep, name), f"missing public export: {name}"
