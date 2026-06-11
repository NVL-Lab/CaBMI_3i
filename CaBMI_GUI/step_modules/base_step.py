"""
Shared helpers for CaBMI Run GUI step modules.

The Run GUI owns the window, workflow, state machine, logging, and completion
logic. Step modules own the settings shown for one step and the run/load
behavior for that step.
"""

from __future__ import annotations

from tkinter import filedialog, ttk
from typing import Any


SettingsSpec = dict[str, dict[str, Any]]


def build_settings_panel(gui: Any, parent: Any, settings: SettingsSpec) -> bool:
    """Render a normal step settings panel from a module-owned settings spec."""
    if not settings:
        ttk.Label(parent, text="No editable settings for this step.").grid(row=1, column=0, sticky="w")
        return True

    for row_index, (key, meta) in enumerate(settings.items(), start=1):
        gui.add_step_setting_row(row_index, key, meta)
    return True


def collect_settings(gui: Any, settings: SettingsSpec) -> dict[str, Any]:
    """Collect values from a module-owned settings spec and write editable values back to their sources."""
    collected: dict[str, Any] = {}
    for key, var in gui.step_setting_vars.items():
        meta = settings.get(key, {})
        value = gui.coerce_value(var.get(), meta.get("type", "str"))
        collected[key] = value

        source = meta.get("source")
        if source and not meta.get("readonly"):
            gui.deep_set(source, value)

    return collected


def placeholder_run(gui: Any, step: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    """Default run behavior for steps whose backend is not connected yet."""
    return {
        "message": "Placeholder step completed. Backend function not connected yet.",
        "step_id": step.get("id", ""),
    }


def default_load(gui: Any, step: dict[str, Any], params: dict[str, Any]) -> dict[str, Any] | None:
    """Default load behavior for steps that can load a previous output file."""
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
