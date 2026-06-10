"""
protocol_workflow.py

Small workflow/state helpers for the CaBMI Run GUI.

This file intentionally contains no Tkinter code.  The Run GUI uses these
step definitions to render the sequential workflow, decide which step is
active, and record whether each step was completed by running the backend or by
loading a previously generated output file.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


STATUS_LOCKED = "locked"
STATUS_READY = "ready"
STATUS_RUNNING = "running"
STATUS_WAITING_DECISION = "waiting_decision"
STATUS_DONE = "done"
STATUS_NEEDS_RERUN = "needs_rerun"
STATUS_SKIPPED = "skipped"
STATUS_ERROR = "error"

COMPLETION_RUN = "generated"
COMPLETION_LOAD = "loaded"
COMPLETION_ACCEPT = "accepted"
COMPLETION_SKIP = "skipped"

STATUS_SYMBOLS = {
    STATUS_LOCKED: "🔒",
    STATUS_READY: "○",
    STATUS_RUNNING: "…",
    STATUS_WAITING_DECISION: "?",
    STATUS_DONE: "✓",
    STATUS_NEEDS_RERUN: "↻",
    STATUS_SKIPPED: "↷",
    STATUS_ERROR: "⚠",
}


@dataclass
class StepSpec:
    id: str
    name: str
    description: str
    can_run: bool = True
    can_load: bool = False
    can_skip: bool = False
    can_repeat: bool = True
    required: bool = True
    settings: dict[str, Any] = field(default_factory=dict)
    load_label: str = "Load output"
    insert_before: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = deepcopy(self.__dict__)
        return data


BASE_CABMI_STEPS: list[StepSpec] = [
    StepSpec(
        id="initialize_session",
        name="Initialize session",
        description="Load the saved session config and prepare legacy CaBMI runtime variables.",
        can_load=False,
        can_repeat=True,
        settings={
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
        },
    ),
    StepSpec(
        id="acquire_roi_background",
        name="Acquire ROI background",
        description="Acquire the short recording/background used to extract ROIs.",
        can_load=True,
        settings={
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
        },
        load_label="Load ROI background file",
    ),
    StepSpec(
        id="get_roi_data",
        name="Get ROI data",
        description="Load or process ROI masks/data for the current imaging field.",
        can_load=True,
        settings={
            "roi_data_file": {
                "label": "ROI data file",
                "source": "step_outputs.get_roi_data.file",
                "type": "file",
                "default": "",
            },
        },
        load_label="Load ROI data file",
    ),
    StepSpec(
        id="acquire_baseline",
        name="Acquire baseline",
        description="Acquire baseline neural activity.",
        can_load=True,
        settings={
            "baseline_len_sec": {
                "label": "Baseline length (s)",
                "source": "runtime.task_set.baseline_len",
                "type": "int",
            },
        },
        load_label="Load baseline file",
    ),
    StepSpec(
        id="select_ensembles",
        name="Select neuron ensembles",
        description="Plot baseline activity and select neuron ensembles.",
        can_load=True,
        settings={
            "ensemble_count": {
                "label": "Number of ensembles",
                "source": "runtime.task_set.cb.ensemble_count",
                "type": "int",
            },
            "neurons_per_ensemble": {
                "label": "Neurons per ensemble",
                "source": "runtime.task_set.cb.neurons_per_ensemble",
                "type": "int",
            },
        },
        load_label="Load ensemble selection",
    ),
    StepSpec(
        id="calibrate_target",
        name="Calibrate target",
        description="Run baseline-to-target calibration and verify ROI selection.",
        can_load=True,
        settings={
            "load_calibration": {
                "label": "Load calibration instead of recompute",
                "source": "runtime.task_set.expt.calib.load",
                "type": "bool",
            },
        },
        load_label="Load calibration file",
    ),
    StepSpec(
        id="generate_random_stim",
        name="Generate random stimulation vector",
        description="Generate or load the random stimulation vector used by BMI acquisition.",
        can_load=True,
        settings={
            "ihsi_mean": {
                "label": "IHSI mean",
                "source": "runtime.task_set.rs.ihsi_mean",
                "type": "float",
            },
            "ihsi_range": {
                "label": "IHSI range",
                "source": "runtime.task_set.rs.ihsi_range",
                "type": "float",
            },
        },
        load_label="Load stimulation vector",
    ),
    StepSpec(
        id="start_bmi",
        name="Start BMI acquisition",
        description="Run the closed-loop BMI acquisition.",
        can_load=False,
        settings={
            "bmi_len_sec": {
                "label": "BMI length (s)",
                "source": "runtime.task_set.bmi_len",
                "type": "int",
            },
        },
    ),
    StepSpec(
        id="end_session",
        name="End session",
        description="Close devices, save logs, and mark session complete.",
        can_load=False,
        can_repeat=False,
    ),
]


CAPABILITY_EXTRA_STEPS: dict[str, list[StepSpec]] = {
    "reward": [
        StepSpec(
            id="test_reward",
            name="Test reward device",
            description="Verify the reward device/controller before BMI acquisition.",
            can_load=False,
            can_skip=True,
            insert_before="start_bmi",
            settings={
                "reward_device": {
                    "label": "Reward device",
                    "source": "runtime.fb_set.arduino.reward_device",
                    "type": "str",
                },
                "controller_port": {
                    "label": "Controller port",
                    "source": "runtime.fb_set.arduino.com",
                    "type": "str",
                },
            },
        )
    ],
    "auditory_feedback": [
        StepSpec(
            id="test_auditory_feedback",
            name="Test auditory feedback",
            description="Play feedback tone and verify audio output.",
            can_load=False,
            can_skip=True,
            insert_before="start_bmi",
            settings={
                "tone_frequency_hz": {
                    "label": "Tone frequency (Hz)",
                    "source": "runtime.fb_set.tone.frequency_hz",
                    "type": "float",
                },
                "tone_duration_sec": {
                    "label": "Tone duration (s)",
                    "source": "runtime.fb_set.tone.duration_sec",
                    "type": "float",
                },
            },
        )
    ],
    "holography": [
        StepSpec(
            id="prepare_holography",
            name="Prepare holography",
            description="Verify holographic stimulation parameters and targets.",
            can_load=True,
            can_skip=True,
            insert_before="start_bmi",
            load_label="Load holography calibration",
        )
    ],
    "photopharm": [
        StepSpec(
            id="prepare_photopharm",
            name="Prepare photopharm protocol",
            description="Verify activation/reset wavelengths and stimulation timing.",
            can_load=False,
            can_skip=True,
            insert_before="start_bmi",
        )
    ],
    "behavior_camera": [
        StepSpec(
            id="prepare_behavior_camera",
            name="Prepare behavior camera",
            description="Verify camera connection and recording settings.",
            can_load=False,
            can_skip=True,
            insert_before="start_bmi",
        )
    ],
    "external_trigger": [
        StepSpec(
            id="prepare_external_trigger",
            name="Prepare external trigger",
            description="Verify external trigger device and channel.",
            can_load=False,
            can_skip=True,
            insert_before="start_bmi",
        )
    ],
}


def build_steps_from_config(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Build ordered protocol steps from active capabilities."""
    settings = config.get("settings_used", {}) or {}
    capabilities = settings.get("capabilities", {}) or {}

    steps = [step.as_dict() for step in BASE_CABMI_STEPS]

    for cap_name, enabled in capabilities.items():
        if not enabled:
            continue
        for extra in CAPABILITY_EXTRA_STEPS.get(cap_name, []):
            insert_step(steps, extra.as_dict())

    return steps


def insert_step(steps: list[dict[str, Any]], step: dict[str, Any]) -> None:
    insert_before = step.pop("insert_before", None)
    if not insert_before:
        steps.append(step)
        return

    for i, existing in enumerate(steps):
        if existing["id"] == insert_before:
            steps.insert(i, step)
            return

    steps.append(step)


def first_unfinished_required_step_index(steps: list[dict[str, Any]], statuses: dict[str, str]) -> int | None:
    for i, step in enumerate(steps):
        status = statuses.get(step["id"], STATUS_LOCKED)
        if status not in {STATUS_DONE, STATUS_SKIPPED}:
            return i
    return None
