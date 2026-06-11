"""
Base definitions for CaBMI Run GUI step modules.

A step module may implement any of these functions:

    build_panel(gui, parent, step) -> bool
        Build a custom settings panel for this step. Return True if the custom
        panel was rendered. Return False to let run_session_gui.py use the
        generic settings panel from protocol_workflow.py.

    run(gui, step, params) -> dict
        Execute the step and return a JSON-serializable result dictionary.

    load(gui, step, params) -> dict | None
        Load previously generated output for this step. Return None if the user
        cancelled the operation.

The gui argument is the RunSessionGUI instance. This keeps future step modules
powerful without forcing run_session_gui.py to know protocol-specific details.
"""

from __future__ import annotations

from typing import Any


def build_panel(gui: Any, parent: Any, step: dict[str, Any]) -> bool:
    """Default: no custom panel; use the generic settings panel."""
    return False
