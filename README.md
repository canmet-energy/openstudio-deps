# openstudio-deps (`osdep`)

A reusable installer and validator for [OpenStudio](https://github.com/NREL/OpenStudio)
and [OpenStudio-HPXML](https://github.com/NREL/OpenStudio-HPXML) dependencies.

Extracted from the [H2K-HPXML](https://github.com/canmet-energy/h2k-hpxml) project so that
any application needing a managed OpenStudio toolchain can reuse it.

## Features

- Cross-platform (Windows portable + Linux) OpenStudio install/validate/uninstall
- OpenStudio-HPXML download and extraction
- Binary detection across standard install locations and `PATH`
- Version configuration **injected by the consumer**, with sensible package defaults

## Install

```bash
pip install openstudio-deps        # once published
# or, during development, as a path dependency:
pip install -e /path/to/openstudio-deps
```

## CLI

```bash
osdep --check-only          # check dependencies, don't install
osdep --auto-install        # install missing dependencies (no prompts)
osdep --verify              # verify a working installation
osdep --uninstall           # remove dependencies
osdep --openstudio-version 3.11.0 --check-only   # override required version
```

## Library usage

```python
import osdep
from osdep import DependencyConfig

# Option A: inject your required versions globally (recommended for apps)
osdep.set_default_config(DependencyConfig(
    openstudio_version="3.11.0",
    openstudio_sha="241b8abb4d",
    openstudio_hpxml_version="v1.9.1",
))

osdep.validate_dependencies(check_only=True)
binary = osdep.get_openstudio_path()        # uses the injected versions

# Option B: pass config per-call
cfg = {"openstudio_version": "3.11.0", "openstudio_sha": "241b8abb4d",
       "openstudio_hpxml_version": "v1.9.1"}
osdep.get_openstudio_binary(config=cfg)
```

If you never inject a config, the package-shipped defaults
(`src/osdep/resources/dependency_versions.json`) are used.
