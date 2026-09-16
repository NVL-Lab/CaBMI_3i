"""
Fallback module for protocol steps that do not have their own module yet.
"""

from __future__ import annotations

from typing import Any

from .base_step import default_load, placeholder_run


def build_panel(gui: Any, parent: Any, step: dict[str, Any]) -> bool:
    return False


def run(gui: Any, step: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    return placeholder_run(gui, step, params)


def load(gui: Any, step: dict[str, Any], params: dict[str, Any]) -> dict[str, Any] | None:
    return default_load(gui, step, params)
