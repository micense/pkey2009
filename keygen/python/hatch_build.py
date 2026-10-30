"""Bundle the repo-root ``res/`` data into the package at build time.

``res/`` lives at the repository root (it is shared with the web build) and is
the single source of truth. A wheel/sdist must be self-contained, so copy the
data into ``pkey2009/res/`` during the build and register it as an artifact.

When the wheel is built from an unpacked sdist, ``../../res`` is absent but
``pkey2009/res`` is already present (it was included in the sdist), so the copy
is simply skipped.
"""

import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

DATA_FILES = ("crc_full_masks.json", "sku_catalog.json")


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        root = Path(self.root)
        src = root.parent.parent / "res"  # repo-root res/
        dst = root / "pkey2009" / "res"
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            for name in DATA_FILES:
                shutil.copy2(src / name, dst / name)
        # Ensure the data is packaged even though pkey2009/res/ is git-ignored.
        build_data.setdefault("artifacts", []).append("pkey2009/res/*.json")
