"""
Initialize Session step for the CaBMI Run GUI.

This module contains initialization behavior only. It does not implement ROI,
baseline, BMI, calibration, or other protocol acquisition logic.
"""

from __future__ import annotations

from typing import Any

from ..gui_config_adapter import build_main_protocol_runtime, make_json_safe
from .base_step import build_settings_panel, collect_settings


SETTINGS = {
    "slidebook_data_dir": {
        "label": "Slidebook data folder",
        "source": "runtime.exp_info.sldy_dir",
        "type": "path_dir",
        "help": "Folder where Slidebook is currently writing/has written imaging data.",
    },
    "save_path": {
        "label": "Session save folder",
        "source": "runtime.path_data.save_path",
        "type": "path_dir",
        "readonly": True,
    },
    "frame_rate_hz": {
        "label": "Frame rate (Hz)",
        "source": "runtime.task_set.im.frame_rate",
        "type": "float",
    },
}


def build_panel(gui: Any, parent: Any, step: dict[str, Any]) -> bool:
    return build_settings_panel(gui, parent, SETTINGS)


def collect_params(gui: Any, step: dict[str, Any]) -> dict[str, Any]:
    return collect_settings(gui, SETTINGS)


def run(gui: Any, step: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    if not gui.session_config_path:
        raise RuntimeError("No session_config.json loaded.")

    # If the operator edited the Slidebook folder before initialization,
    # write it into the in-memory config before building runtime_state.
    slidebook_dir = params.get("slidebook_data_dir")
    if slidebook_dir:
        gui.session_config.setdefault("settings_used", {}).setdefault("imaging", {})[
            "slidebook_default_dir"
        ] = slidebook_dir

    gui.runtime_state = build_main_protocol_runtime(
        gui.session_config,
        gui.session_config_path,
        create_save_path=True,
    )

    errors = gui.runtime_state.get("errors", [])
    warnings = gui.runtime_state.get("warnings", [])
    for warning in warnings:
        gui.log(f"Warning: {warning}")
    if errors:
        raise RuntimeError("Initialization failed:\n" + "\n".join(errors))

    gui.write_runtime_config_used()
    return {
        "message": "Session initialized.",
        "runtime_state": make_json_safe(gui.runtime_state),
    }
