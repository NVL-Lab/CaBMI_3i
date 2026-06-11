"""
Fallback module for protocol steps that do not have real backend code yet.

This preserves the current Run GUI behavior: unknown/unimplemented steps still
complete as placeholders when Run is pressed, and loadable steps still use a
simple file picker when Load is pressed.
"""

from __future__ import annotations

from tkinter import filedialog
from typing import Any


def build_panel(gui: Any, parent: Any, step: dict[str, Any]) -> bool:
    return False


def run(gui: Any, step: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    return {
        "message": "Placeholder step completed. Backend function not connected yet.",
        "step_id": step.get("id", ""),
    }


def load(gui: Any, step: dict[str, Any], params: dict[str, Any]) -> dict[str, Any] | None:
    path = filedialog.askopenfilename(
        title=step.get("load_label", "Load output"),
        filetypes=[("All files", "*.*")],
    )
    if not path:
        return None

    return {
        "loaded_file": path,
        "message": f"Loaded output for step: {step.get('name', step.get('id', 'unknown step'))}",
    }
