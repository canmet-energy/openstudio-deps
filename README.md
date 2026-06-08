# openstudio-deps (`osdep`)

A reusable installer and validator for [OpenStudio](https://github.com/NREL/OpenStudio)
and [OpenStudio-HPXML](https://github.com/NREL/OpenStudio-HPXML) dependencies.

Extracted from the [H2K-HPXML](https://github.com/canmet-energy/h2k-hpxml) project so that
any application needing a managed OpenStudio toolchain can reuse it.

## Features

- **User-space installation** — installs OpenStudio and HPXML to the current
  user's home directory (no admin rights required for the binaries themselves)
- Cross-platform support (Windows portable tarball + Linux tarball)
- Binary detection across standard install locations and `PATH`
- Version configuration **injected by the consumer**, with sensible package defaults
- Path-sharing API so consuming applications can locate installed binaries

## Install

```bash
pip install openstudio-deps        # once published
# or, during development, as a path dependency:
pip install -e /path/to/openstudio-deps
```

## Use cases

### 1. CLI (manual / interactive)

Run `osdep` from a terminal to check, install, or remove dependencies:

```bash
osdep                       # interactive — prompts to install if missing
osdep --check-only          # report status without installing
osdep --auto-install        # install missing dependencies (no prompts)
osdep --verify              # verify a working installation
osdep --uninstall           # remove installed dependencies
osdep --openstudio-version 3.11.0 --check-only   # override the required version
```

### 2. Dockerfile

Pre-install the system libraries OpenStudio needs, then let `osdep` handle
the user-space binary installation at build time. The installer detects
`DOCKER_BUILD_CONTEXT=true` and skips interactive prompts automatically.

```dockerfile
FROM ubuntu:24.04

# System libraries required by OpenStudio (need root)
RUN apt-get update && apt-get install -y \
    libgfortran5 libgomp1 libssl3 libx11-6 libxext6 \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

ENV DOCKER_BUILD_CONTEXT=true

RUN pip install openstudio-deps && osdep --auto-install
```

### 3. Devcontainer post-create command

Add `osdep` to your `postCreateCommand` so dependencies are ready as soon as
the container starts. System libraries should be installed in the Dockerfile
(see above); the post-create step handles the user-space binaries.

```jsonc
// .devcontainer/devcontainer.json
{
  "postCreateCommand": "pip install -e '.[dev]' && osdep --auto-install"
}
```

### 4. Python library API

Consuming applications can install dependencies and retrieve their paths
programmatically. This is the primary use case for packaging `osdep` as a
library — it lets your application ensure the toolchain is present and then
locate the binaries without hard-coding paths.

```python
import osdep

# --- Install (if missing) -------------------------------------------
osdep.validate_dependencies(install_quiet=True, interactive=False)

# --- Locate binaries -------------------------------------------------
paths = osdep.get_dependency_paths()
# {
#     "openstudio_binary":  "~/.local/share/OpenStudio-3.11.0/bin/openstudio",
#     "hpxml_os_path":      "~/.local/share/OpenStudio-HPXML-v1.9.1",
#     "energyplus_binary":  "~/.local/share/OpenStudio-3.11.0/EnergyPlus/energyplus",
# }

# Use the paths directly
import subprocess
subprocess.run([paths["openstudio_binary"], "--version"])
```

Individual accessors are also available:

```python
osdep.get_openstudio_binary()   # str | None
osdep.get_hpxml_os_path()       # str | None
osdep.get_energyplus_binary()   # str | None
```

#### Version configuration

By default `osdep` uses the versions shipped in
`src/osdep/resources/dependency_versions.json`. You can override them
globally or per-call:

```python
from osdep import DependencyConfig

# Option A: inject globally (recommended for apps)
osdep.set_default_config(DependencyConfig(
    openstudio_version="3.11.0",
    openstudio_sha="241b8abb4d",
    openstudio_hpxml_version="v1.9.1",
))
osdep.validate_dependencies(check_only=True)

# Option B: pass per-call
cfg = {"openstudio_version": "3.11.0", "openstudio_sha": "241b8abb4d",
       "openstudio_hpxml_version": "v1.9.1"}
osdep.get_openstudio_binary(config=cfg)
```
