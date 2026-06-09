
"""
run_session_gui.py

Prototype Run Session window for CaBMI.

This window is intentionally separated from the configuration GUI.

Purpose:
    - Load or receive a session_config.json
    - Build the list of protocol steps from active capabilities
    - Let the experimenter run steps one by one
    - Track status, notes, and step completion

This prototype does NOT call the real CaBMI acquisition functions yet.
Each step currently runs as a simulated/dummy step.
"""

from __future__ import annotations

import json
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from gui_config_adapter import build_main_protocol_runtime, make_json_safe


BASE_CABMI_STEPS = [
    {
        "id": "initialize_session",
        "name": "Initialize session",
        "description": "Load session config, verify paths, prepare runtime state.",
    },
    {
        "id": "acquire_roi_background",
        "name": "Acquire ROI background",
        "description": "Acquire image/background required for ROI extraction.",
    },
    {
        "id": "get_roi_data",
        "name": "Get ROI data",
        "description": "Load or process ROI masks/data for the current imaging field.",
    },
    {
        "id": "acquire_baseline",
        "name": "Acquire baseline",
        "description": "Acquire baseline neural activity.",
    },
    {
        "id": "select_ensembles",
        "name": "Select neuron ensembles",
        "description": "Plot baseline activity and select neuron ensembles.",
    },
    {
        "id": "calibrate_target",
        "name": "Calibrate target",
        "description": "Run baseline-to-target calibration and verify ROI selection.",
    },
    {
        "id": "start_bmi",
        "name": "Start BMI acquisition",
        "description": "Run the closed-loop BMI acquisition.",
    },
    {
        "id": "end_session",
        "name": "End session",
        "description": "Close devices, save logs, and mark session complete.",
    },
]


CAPABILITY_EXTRA_STEPS = {
    "reward": [
        {
            "id": "test_reward",
            "name": "Test reward device",
            "description": "Verify reward delivery device, COM port, and timing.",
            "insert_before": "start_bmi",
        }
    ],
    "auditory_feedback": [
        {
            "id": "test_auditory_feedback",
            "name": "Test auditory feedback",
            "description": "Play feedback tone and verify audio output.",
            "insert_before": "start_bmi",
        }
    ],
    "holography": [
        {
            "id": "prepare_holography",
            "name": "Prepare holography",
            "description": "Verify holographic stimulation parameters and targets.",
            "insert_before": "start_bmi",
        }
    ],
    "photopharm": [
        {
            "id": "prepare_photopharm",
            "name": "Prepare photopharm protocol",
            "description": "Verify activation/reset wavelengths and stimulation timing.",
            "insert_before": "start_bmi",
        }
    ],
    "behavior_camera": [
        {
            "id": "prepare_behavior_camera",
            "name": "Prepare behavior camera",
            "description": "Verify camera connection and recording settings.",
            "insert_before": "start_bmi",
        }
    ],
    "external_trigger": [
        {
            "id": "prepare_external_trigger",
            "name": "Prepare external trigger",
            "description": "Verify external trigger device and channel.",
            "insert_before": "start_bmi",
        }
    ],
}


STEP_STATUS_NOT_STARTED = "not_started"
STEP_STATUS_RUNNING = "running"
STEP_STATUS_DONE = "done"
STEP_STATUS_SKIPPED = "skipped"
STEP_STATUS_ERROR = "error"


STATUS_SYMBOLS = {
    STEP_STATUS_NOT_STARTED: "○",
    STEP_STATUS_RUNNING: "…",
    STEP_STATUS_DONE: "✓",
    STEP_STATUS_SKIPPED: "↷",
    STEP_STATUS_ERROR: "⚠",
}


class RunSessionGUI(tk.Tk):
    def __init__(self, session_config_path: str | Path | None = None):
        super().__init__()

        self.title("CaBMI Run Session")
        self.geometry("1100x750")

        self.session_config_path: Path | None = None
        self.session_config: dict = {}
        self.steps: list[dict] = []
        self.step_status: dict[str, str] = {}
        self.step_rows: dict[str, dict] = {}
        self.runtime_state: dict = {}
        self.run_events: list[dict] = []

        self._build_variables()
        self._build_layout()

        if session_config_path is not None:
            self.load_session_config(Path(session_config_path))

    def _build_variables(self):
        self.session_id_var = tk.StringVar(value="")
        self.animal_var = tk.StringVar(value="")
        self.project_var = tk.StringVar(value="")
        self.date_day_var = tk.StringVar(value="")
        self.config_path_var = tk.StringVar(value="")

    def _build_layout(self):
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(
            outer,
            text="CaBMI Run Session",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w", pady=(0, 10))

        top = ttk.LabelFrame(outer, text="Session")
        top.pack(fill="x", pady=(0, 8))

        ttk.Label(top, text="Config file").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(top, textvariable=self.config_path_var).grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Button(top, text="Load Config", command=self.browse_and_load_config).grid(row=0, column=2, padx=4)

        ttk.Label(top, text="Session ID").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Label(top, textvariable=self.session_id_var).grid(row=1, column=1, sticky="w", pady=3)

        top.columnconfigure(1, weight=1)

        main = ttk.PanedWindow(outer, orient="horizontal")
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, padding=4)
        right = ttk.Frame(main, padding=4)
        main.add(left, weight=2)
        main.add(right, weight=1)

        self._build_steps_panel(left)
        self._build_log_panel(right)

        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(8, 0))

        ttk.Button(bottom, text="Save Run Log", command=self.save_run_log).pack(side="right", padx=4)

    def _build_steps_panel(self, parent):
        steps_box = ttk.LabelFrame(parent, text="Protocol steps")
        steps_box.pack(fill="both", expand=True)

        self.steps_container = ttk.Frame(steps_box)
        self.steps_container.pack(fill="both", expand=True)

    def _build_log_panel(self, parent):
        notes_box = ttk.LabelFrame(parent, text="Run notes")
        notes_box.pack(fill="both", expand=True, pady=(0, 8))

        self.run_notes_text = tk.Text(notes_box, height=12, wrap="word")
        notes_scroll = ttk.Scrollbar(notes_box, orient="vertical", command=self.run_notes_text.yview)
        self.run_notes_text.configure(yscrollcommand=notes_scroll.set)
        self.run_notes_text.pack(side="left", fill="both", expand=True)
        notes_scroll.pack(side="right", fill="y")

        log_box = ttk.LabelFrame(parent, text="Run log")
        log_box.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_box, height=12, wrap="word")
        log_scroll = ttk.Scrollbar(log_box, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

    def browse_and_load_config(self):
        path = filedialog.askopenfilename(
            title="Select session_config.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        self.load_session_config(Path(path))

    def load_session_config(self, path: Path):
        try:
            with path.open("r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            messagebox.showerror("Load failed", str(e))
            return

        self.session_config_path = path
        self.session_config = config
        self.config_path_var.set(str(path))

        self.session_id_var.set(config.get("session_id", ""))
        self.project_var.set(config.get("project", ""))
        self.animal_var.set(config.get("animal_id", ""))
        self.date_day_var.set(f"{config.get('date', '')} / {config.get('day', '')}")

        self.steps = self.build_steps_from_config(config)
        self.step_status = {step["id"]: STEP_STATUS_NOT_STARTED for step in self.steps}

        self.render_steps()
        self.log(f"Loaded session config: {path}")
        self.log(f"Built {len(self.steps)} protocol steps.")

    def build_steps_from_config(self, config: dict) -> list[dict]:
        settings = config.get("settings_used", {})
        capabilities = settings.get("capabilities", {})

        steps = [dict(step) for step in BASE_CABMI_STEPS]

        for cap_name, enabled in capabilities.items():
            if not enabled:
                continue

            extra_steps = CAPABILITY_EXTRA_STEPS.get(cap_name, [])
            for step in extra_steps:
                self.insert_step(steps, dict(step))

        return steps

    @staticmethod
    def insert_step(steps: list[dict], step: dict):
        insert_before = step.pop("insert_before", None)

        if insert_before is None:
            steps.append(step)
            return

        for i, existing in enumerate(steps):
            if existing["id"] == insert_before:
                steps.insert(i, step)
                return

        steps.append(step)

    def render_steps(self):
        for child in self.steps_container.winfo_children():
            child.destroy()

        self.step_rows = {}

        header = ttk.Frame(self.steps_container)
        header.grid(row=0, column=0, sticky="ew", padx=4, pady=2)
        ttk.Label(header, text="Status", width=8).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Step", width=28).grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Description").grid(row=0, column=2, sticky="w")
        ttk.Label(header, text="Actions").grid(row=0, column=3, sticky="w")

        for i, step in enumerate(self.steps, start=1):
            self.render_step_row(i, step)

        self.steps_container.columnconfigure(0, weight=1)

    def render_step_row(self, row_index: int, step: dict):
        row = ttk.Frame(self.steps_container)
        row.grid(row=row_index, column=0, sticky="ew", padx=4, pady=3)

        status_var = tk.StringVar(value=self.format_status(step["id"]))
        status_label = ttk.Label(row, textvariable=status_var, width=8)
        status_label.grid(row=0, column=0, sticky="w")

        step_label = ttk.Label(row, text=step["name"], width=28)
        step_label.grid(row=0, column=1, sticky="w")

        desc_label = ttk.Label(row, text=step.get("description", ""), wraplength=360)
        desc_label.grid(row=0, column=2, sticky="w", padx=(4, 8))

        buttons = ttk.Frame(row)
        buttons.grid(row=0, column=3, sticky="e")

        ttk.Button(buttons, text="Run", command=lambda s=step: self.run_step(s)).pack(side="left", padx=2)
        ttk.Button(buttons, text="Repeat", command=lambda s=step: self.repeat_step(s)).pack(side="left", padx=2)
        ttk.Button(buttons, text="Skip", command=lambda s=step: self.skip_step(s)).pack(side="left", padx=2)

        row.columnconfigure(2, weight=1)

        self.step_rows[step["id"]] = {
            "status_var": status_var,
            "row": row,
        }

    def format_status(self, step_id: str) -> str:
        status = self.step_status.get(step_id, STEP_STATUS_NOT_STARTED)
        return f"{STATUS_SYMBOLS.get(status, '?')} {status}"

    def update_step_status(self, step_id: str, status: str):
        self.step_status[step_id] = status
        row = self.step_rows.get(step_id)
        if row:
            row["status_var"].set(self.format_status(step_id))

    def run_step(self, step: dict):
        step_id = step["id"]
        self.update_step_status(step_id, STEP_STATUS_RUNNING)
        self.log(f"Running step: {step['name']}")

        try:
            self.run_step_handler(step)
        except Exception as e:
            self.update_step_status(step_id, STEP_STATUS_ERROR)
            self.log(f"ERROR in step {step['name']}: {e}")
            messagebox.showerror("Step failed", str(e))
            return

        self.update_step_status(step_id, STEP_STATUS_DONE)
        self.log(f"Completed step: {step['name']}")

    def repeat_step(self, step: dict):
        self.log(f"Repeating step: {step['name']}")
        self.run_step(step)

    def skip_step(self, step: dict):
        step_id = step["id"]
        self.update_step_status(step_id, STEP_STATUS_SKIPPED)
        self.log(f"Skipped step: {step['name']}")

    def run_step_handler(self, step: dict):
        """Dispatch protocol steps.

        Only Initialize Session is connected to real logic for now.
        Other steps remain placeholders until their backend functions are wired.
        """
        step_id = step["id"]

        if step_id == "initialize_session":
            self.initialize_session()
            return

        self.run_dummy_step(step)

    def initialize_session(self):
        """Prepare runtime variables expected by the original CaBMI protocol.

        This replaces the beginning of main_protocol.py:
            exp_info = get_exp_info()
            task_set = get_bmi_settings(save=True)
            fb_set = get_fb_settings()
            path_data = {...}

        The Run GUI gets those values from session_config.json instead of
        asking for them interactively.
        """
        if not self.session_config:
            raise RuntimeError("No session_config.json is loaded.")
        if not self.session_config_path:
            raise RuntimeError("Session config path is missing.")

        runtime = build_main_protocol_runtime(
            self.session_config,
            session_config_path=self.session_config_path,
            create_save_path=True,
        )

        for warning in runtime.get("warnings", []):
            self.log(f"WARNING: {warning}")

        errors = runtime.get("errors", [])
        if errors:
            for error in errors:
                self.log(f"INITIALIZATION ERROR: {error}")
            raise RuntimeError("Initialize session failed. " + " ".join(errors))

        self.runtime_state = runtime

        self.log(f"Session directory: {runtime.get('session_dir', '')}")
        self.log(f"Slidebook path: {runtime['path_data'].get('sldy_path')}")
        self.log("Prepared old protocol variables: exp_info, task_set, fb_set, path_data.")

        self.add_run_event(
            event_type="initialize_session",
            status="done",
            details={
                "session_id": self.session_config.get("session_id", ""),
                "session_dir": runtime.get("session_dir", ""),
                "warnings": runtime.get("warnings", []),
                "prepared_variables": ["exp_info", "task_set", "fb_set", "path_data"],
            },
        )

        # Persist immediately so initialization is recorded even if the session
        # stops before the user manually presses Save Run Log.
        self.save_run_log(show_message=False)

    def add_run_event(self, event_type: str, status: str, details: dict | None = None):
        self.run_events.append(
            {
                "time": datetime.now().isoformat(timespec="seconds"),
                "event_type": event_type,
                "status": status,
                "details": details or {},
            }
        )

    def run_dummy_step(self, step: dict):
        """
        Placeholder for real protocol integration.

        Later, this will dispatch by step id:
            acquire_roi_background -> get_roi_bg(...)
            acquire_baseline -> baseline_acqnvs_3i(...)
            start_bmi -> bmi_acqnvs_3i(...)
        """
        self.add_run_event(
            event_type=step["id"],
            status="dummy_done",
            details={"name": step.get("name", "")},
        )
        return

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def save_run_log(self, show_message: bool = True):
        if not self.session_config_path:
            messagebox.showwarning("No session", "Load a session config first.")
            return

        log_path = self.session_config_path.parent / "run_log.json"

        data = {
            "session_config": str(self.session_config_path),
            "saved": datetime.now().isoformat(timespec="seconds"),
            "step_status": self.step_status,
            "run_events": self.run_events,
            "runtime_state": make_json_safe(self.runtime_state),
            "run_notes": self.run_notes_text.get("1.0", "end").strip(),
            "log_text": self.log_text.get("1.0", "end").strip(),
        }

        try:
            with log_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return

        if show_message:
            messagebox.showinfo("Run log saved", f"Saved run log:\n{log_path}")
        self.log(f"Saved run log: {log_path}")


if __name__ == "__main__":
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    app = RunSessionGUI(config_path)
    app.mainloop()
