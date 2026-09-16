from __future__ import annotations
from typing import Any
from .base_step import build_settings_panel, collect_settings, default_load, placeholder_run

SETTINGS = {
    "baseline_len_sec": {
        "label": "Baseline length (s)",
        "source": "runtime.task_set.baseline_len",
        "type": "int",
    },
}

def build_panel(gui: Any, parent: Any, step: dict[str, Any]) -> bool:
    return build_settings_panel(gui, parent, SETTINGS)

def collect_params(gui: Any, step: dict[str, Any]) -> dict[str, Any]:
    return collect_settings(gui, SETTINGS)

def run(gui: Any, step: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    return placeholder_run(gui, step, params)

def load(gui: Any, step: dict[str, Any], params: dict[str, Any]) -> dict[str, Any] | None:
    return default_load(gui, step, params)
