"""Resolves voice model and hubert checkpoint paths.

The voice models (~3.7 GB) and the hubert speech encoder (~190 MB) are bundled
inside the app so it can be distributed as a single self-contained artifact
with no reliance on download URLs. In a source checkout the same paths exist
in the repo (populated by download_models.py).
"""
import os
import sys
from pathlib import Path

HUBERT_FILENAME = "checkpoint_best_legacy_500.pt"


def get_resource_path(relative_path):
    """Absolute path to a bundled resource, in dev and under PyInstaller."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)


def get_models_dir():
    return Path(get_resource_path("models"))


def get_hubert_path():
    return Path(get_resource_path(
        os.path.join("so-vits-svc", "so-vits-svc-4.1-Stable", "pretrain", HUBERT_FILENAME)))


def installed_models():
    """Names of models that are present (model.pth + config.json)."""
    models_dir = get_models_dir()
    found = []
    if not models_dir.is_dir():
        return found
    for entry in sorted(models_dir.iterdir()):
        if (entry / "model.pth").is_file() and (entry / "config.json").is_file():
            found.append(entry.name)
    return found


def missing_components():
    """Human-readable names of components missing from the bundle/checkout."""
    missing = [f"voice model {m}" for m in
               ("female-1", "female-2", "female-3", "female-4",
                "male-1", "male-2", "male-3")
               if m not in set(installed_models())]
    if not get_hubert_path().is_file():
        missing.append("speech encoder (hubert)")
    return missing
