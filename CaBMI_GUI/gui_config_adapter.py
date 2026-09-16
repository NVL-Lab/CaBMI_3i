"""
gui_config_adapter.py

Compatibility layer between the new CaBMI GUI session_config.json format
and the variable dictionaries expected by the original main_protocol.py code.

The goal is not to redesign the old protocol yet. The goal is to let the Run GUI
prepare the same objects that main_protocol.py currently builds interactively:

    exp_info
    task_set
    fb_set
    path_data

Those objects are stored in runtime_state and later passed to the real CaBMI
backend functions step by step.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_path(value: Any) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    return Path(text).expanduser().resolve()


def build_main_protocol_runtime(
    session_config: dict[str, Any],
    session_config_path: str | Path | None = None,
    create_save_path: bool = True,
) -> dict[str, Any]:
    """
    Convert a GUI session config into old main_protocol.py-compatible objects.

    Parameters
    ----------
    session_config:
        Dictionary loaded from session_config.json.
    session_config_path:
        Path to session_config.json. If provided, the parent folder is used as
        the canonical save_path because config_manager.py saves the config next
        to the future data folder.
    create_save_path:
        Create path_data['save_path'] when task_set['save'] is true.

    Returns
    -------
    runtime_state:
        Dictionary with exp_info, task_set, fb_set, path_data, warnings, errors,
        and initialization metadata.
    """
    settings = deepcopy(session_config.get("settings_used", {}))
    capabilities = settings.get("capabilities", {}) or {}

    cabmi = settings.get("cabmi", {}) or {}
    imaging = settings.get("imaging", {}) or {}
    reward = settings.get("reward", {}) or {}
    auditory = settings.get("auditory_feedback", {}) or {}
    random_stim = settings.get("random_stimulation", {}) or {}
    custom = settings.get("custom", {}) or {}

    session_path = Path(session_config_path).expanduser().resolve() if session_config_path else None
    save_path = session_path.parent if session_path else _as_path(custom.get("save_path"))

    # Slidebook information is intentionally permissive because the first GUI
    # version does not control the microscope. A real path is still required
    # before ROI acquisition can be run reliably.
    slidebook_path = (
        _as_path(custom.get("sldy_path"))
        or _as_path(imaging.get("slidebook_file"))
        or _as_path(imaging.get("slidebook_path"))
        or _as_path(imaging.get("slidebook_default_dir"))
    )

    if slidebook_path:
        sldy_dir = str(slidebook_path.parent if slidebook_path.suffix else slidebook_path)
        sldy_name = slidebook_path.name if slidebook_path.suffix else str(custom.get("sldy_name", ""))
    else:
        sldy_dir = ""
        sldy_name = ""

    exp_info = {
        "animal": session_config.get("animal_id", ""),
        "date": session_config.get("date", ""),
        "day": session_config.get("day", ""),
        "expt": session_config.get("experiment", ""),
        "project": session_config.get("project", ""),
        "session_id": session_config.get("session_id", ""),
        "save_base_dir": str(save_path.parent.parent.parent.parent.parent) if save_path and len(save_path.parts) >= 5 else "",
        "sldy_dir": sldy_dir,
        "sldy_name": sldy_name,
    }

    baseline_len = _as_int(cabmi.get("baseline_len_sec"), 300)
    bmi_len = _as_int(cabmi.get("bmi_len_sec"), 1800)
    frame_rate = _as_float(imaging.get("frame_rate_hz"), 30.0)

    task_set = {
        "save": True,
        "baseline_len": baseline_len,
        "bmi_len": bmi_len,
        "f0_win": _as_int(cabmi.get("f0_win"), 30),
        "im": {
            "frame_rate": frame_rate,
        },
        "cb": {
            "baseline_len": baseline_len,
            "bmi_len": bmi_len,
            "ensemble_count": _as_int(cabmi.get("ensemble_count"), 2),
            "neurons_per_ensemble": _as_int(cabmi.get("neurons_per_ensemble"), 3),
            "sec_per_reward_range": cabmi.get("sec_per_reward_range", [20, 60]),
        },
        "rs": {
            "ihsi_mean": _as_float(random_stim.get("ihsi_mean"), 10.0),
            "ihsi_range": _as_float(random_stim.get("ihsi_range"), 3.0),
        },
        "expt": {
            "calib": {
                "load": _as_bool(cabmi.get("load_calibration"), False),
            }
        },
        "capabilities": deepcopy(capabilities),
    }

    fb_enabled = _as_bool(auditory.get("enabled"), _as_bool(capabilities.get("auditory_feedback"), False))
    reward_enabled = _as_bool(reward.get("enabled"), _as_bool(capabilities.get("reward"), False))

    fb_set = {
        "fb_bool": fb_enabled,
        "reward_bool": reward_enabled,
        "tone": {
            "frequency_hz": _as_float(auditory.get("tone_frequency_hz"), 7000.0),
            "duration_sec": _as_float(auditory.get("tone_duration_sec"), 1.0),
        },
        "arduino": {
            "com": str(reward.get("arduino_com", "")),
            "baudrate": _as_int(reward.get("arduino_baudrate"), 9600),
            "reward_device": str(reward.get("reward_device", "solenoid")),
        },
    }

    path_data = {
        "sldy_path": slidebook_path,
        "save_path": save_path,
    }

    warnings: list[str] = []
    errors: list[str] = []

    if save_path is None:
        errors.append("Could not determine save_path. Load a saved session_config.json.")
    elif create_save_path and task_set.get("save", True):
        save_path.mkdir(parents=True, exist_ok=True)

    if slidebook_path is None:
        errors.append(
            "Slidebook path is missing. Set Imaging → slidebook_default_dir or custom sldy_path before ROI acquisition."
        )
    elif not slidebook_path.exists():
        errors.append(f"Slidebook path does not exist: {slidebook_path}")

    if reward_enabled and not fb_set["arduino"]["com"]:
        warnings.append("Reward is enabled, but no Arduino COM port is configured.")

    return {
        "initialized_at": datetime.now().isoformat(timespec="seconds"),
        "session_config_path": str(session_path) if session_path else "",
        "session_dir": str(save_path) if save_path else "",
        "exp_info": exp_info,
        "task_set": task_set,
        "fb_set": fb_set,
        "path_data": path_data,
        "warnings": warnings,
        "errors": errors,
    }


def make_json_safe(value: Any) -> Any:
    """Convert Paths and nested values into JSON-serializable objects."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [make_json_safe(v) for v in value]
    return value
