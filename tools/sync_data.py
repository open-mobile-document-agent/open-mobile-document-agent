"""Copy schemas, registry and examples into the package before building a release."""
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dest = Path(__file__).resolve().parent / "omda_tools" / "_data"
shutil.rmtree(dest, ignore_errors=True)
for name in ("schemas", "registry", "examples"):
    shutil.copytree(root / name, dest / name)
print(f"synced into {dest}")
