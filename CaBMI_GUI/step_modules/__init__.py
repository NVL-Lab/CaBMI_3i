"""
Step-module registry for the CaBMI Run GUI.

To add a real implementation later:
    1. Create step_modules/<step_id>_step.py
    2. Import it here
    3. Add it to STEP_MODULES using the step id from protocol_workflow.py

No run_session_gui.py changes should be needed for normal step additions.
"""

from __future__ import annotations

from typing import Any

from . import initialize_session_step, placeholder_step


STEP_MODULES: dict[str, Any] = {
    "initialize_session": initialize_session_step,
}


def get_step_module(step_id: str) -> Any:
    """Return a module for the requested step id, or the placeholder module."""
    return STEP_MODULES.get(step_id, placeholder_step)
