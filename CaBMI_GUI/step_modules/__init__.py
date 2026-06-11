"""
Step-module registry for the CaBMI Run GUI.

protocol_workflow.py decides which steps exist and in what order.
This registry maps each step id to the module that owns that step's settings UI,
run behavior, and load behavior.
"""

from __future__ import annotations

from typing import Any

from . import (
    acquire_baseline_step,
    acquire_roi_background_step,
    calibrate_target_step,
    end_session_step,
    generate_random_stim_step,
    get_roi_data_step,
    initialize_session_step,
    placeholder_step,
    prepare_behavior_camera_step,
    prepare_external_trigger_step,
    prepare_holography_step,
    prepare_photopharm_step,
    select_ensembles_step,
    start_bmi_step,
    test_auditory_feedback_step,
    test_reward_step,
)


STEP_MODULES: dict[str, Any] = {
    "initialize_session": initialize_session_step,
    "acquire_roi_background": acquire_roi_background_step,
    "get_roi_data": get_roi_data_step,
    "acquire_baseline": acquire_baseline_step,
    "select_ensembles": select_ensembles_step,
    "calibrate_target": calibrate_target_step,
    "generate_random_stim": generate_random_stim_step,
    "start_bmi": start_bmi_step,
    "end_session": end_session_step,
    "test_reward": test_reward_step,
    "test_auditory_feedback": test_auditory_feedback_step,
    "prepare_holography": prepare_holography_step,
    "prepare_photopharm": prepare_photopharm_step,
    "prepare_behavior_camera": prepare_behavior_camera_step,
    "prepare_external_trigger": prepare_external_trigger_step,
}


def get_step_module(step_id: str) -> Any:
    """Return a module for the requested step id, or the placeholder module."""
    return STEP_MODULES.get(step_id, placeholder_step)
