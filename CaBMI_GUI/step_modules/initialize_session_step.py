"""
Initialize Session step for the CaBMI Run GUI.

This module contains the same initialization behavior that previously lived in
run_session_gui.py. It intentionally does not implement any protocol acquisition
logic.
"""

from __future__ import annotations

from typing import Any

from ..gui_config_adapter import build_main_protocol_runtime, make_json_safe


def build_panel(gui: Any, parent: Any, step: dict[str, Any]) -> bool:
    # Use the generic settings panel defined by protocol_workflow.py.
    return False


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
        # For now initialization should still block ROI steps if the
        # Slidebook folder/save path is not valid.
        raise RuntimeError("Initialization failed:\n" + "\n".join(errors))

    gui.write_runtime_config_used()
    return {
        "message": "Session initialized.",
        "runtime_state": make_json_safe(gui.runtime_state),
    }
