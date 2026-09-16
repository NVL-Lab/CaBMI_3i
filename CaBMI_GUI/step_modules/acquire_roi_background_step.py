from __future__ import annotations
from typing import Any
from .base_step import build_settings_panel, collect_settings, default_load, placeholder_run

SETTINGS = {
    "roi_background_frames": {
        "label": "ROI background frames",
        "source": "runtime.task_set.roi.background_frames",
        "type": "int",
        "default": 100,
        "help": "Temporary GUI-side parameter. It will be passed to the backend once get_roi_bg supports it.",
    },
    "slidebook_data_dir": {
        "label": "Slidebook data folder",
        "source": "runtime.exp_info.sldy_dir",
        "type": "path_dir",
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
