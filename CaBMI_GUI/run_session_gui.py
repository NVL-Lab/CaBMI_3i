"""
run_session_gui.py

Run Session window for CaBMI.

This window is separated from the Configuration GUI. It loads a saved
session_config.json, builds a sequential protocol from active capabilities, and
lets the experimenter complete each step by running it or loading a previously
created output when appropriate.

Current implementation status:
    - Initialize session is connected to real config-adapter logic.
    - Later protocol steps are still placeholders until backend functions are
      connected one by one.
"""

from __future__ import annotations

import json
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from gui_config_adapter import build_main_protocol_runtime, make_json_safe
from protocol_workflow import (
    build_steps_from_config,
    STATUS_LOCKED,
    STATUS_READY,
    STATUS_RUNNING,
    STATUS_WAITING_DECISION,
    STATUS_DONE,
    STATUS_NEEDS_RERUN,
    STATUS_SKIPPED,
    STATUS_ERROR,
    STATUS_SYMBOLS,
    COMPLETION_RUN,
    COMPLETION_LOAD,
    COMPLETION_SKIP,
)


class RunSessionGUI(tk.Tk):
    def __init__(self, session_config_path: str | Path | None = None):
        super().__init__()

        self.title("CaBMI Run Session")
        self.geometry("1250x820")

        self.session_config_path: Path | None = None
        self.session_config: dict[str, Any] = {}
        self.steps: list[dict[str, Any]] = []
        self.step_status: dict[str, str] = {}
        self.step_results: dict[str, dict[str, Any]] = {}
        self.step_rows: dict[str, dict[str, Any]] = {}
        self.active_step_index: int | None = None
        self.runtime_state: dict[str, Any] = {}
        self.run_events: list[dict[str, Any]] = []
        self.step_setting_vars: dict[str, tk.Variable] = {}

        self._build_variables()
        self._build_layout()

        if session_config_path is not None:
            self.load_session_config(Path(session_config_path))

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_variables(self):
        self.session_id_var = tk.StringVar(value="")
        self.animal_var = tk.StringVar(value="")
        self.project_var = tk.StringVar(value="")
        self.date_day_var = tk.StringVar(value="")
        self.config_path_var = tk.StringVar(value="")
        self.active_step_name_var = tk.StringVar(value="No step selected")
        self.active_step_description_var = tk.StringVar(value="Load a session config to begin.")

    def _build_layout(self):
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(outer, text="CaBMI Run Session", font=("Segoe UI", 16, "bold"))
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

        self._build_left_panel(left)
        self._build_right_panel(right)

        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(8, 0))
        ttk.Button(bottom, text="Save Run Log", command=self.save_run_log).pack(side="right", padx=4)

    def _build_left_panel(self, parent):
        parent.rowconfigure(0, weight=3)
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        steps_box = ttk.LabelFrame(parent, text="Protocol steps")
        steps_box.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        canvas = tk.Canvas(steps_box, highlightthickness=0)
        scroll = ttk.Scrollbar(steps_box, orient="vertical", command=canvas.yview)
        self.steps_container = ttk.Frame(canvas)
        self.steps_container.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.steps_container, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        notes_box = ttk.LabelFrame(parent, text="Run notes")
        notes_box.grid(row=1, column=0, sticky="nsew")
        self.run_notes_text = tk.Text(notes_box, height=8, wrap="word")
        notes_scroll = ttk.Scrollbar(notes_box, orient="vertical", command=self.run_notes_text.yview)
        self.run_notes_text.configure(yscrollcommand=notes_scroll.set)
        self.run_notes_text.pack(side="left", fill="both", expand=True)
        notes_scroll.pack(side="right", fill="y")

    def _build_right_panel(self, parent):
        parent.rowconfigure(0, weight=0)
        parent.rowconfigure(1, weight=2)
        parent.rowconfigure(2, weight=1)
        parent.columnconfigure(0, weight=1)

        active_box = ttk.LabelFrame(parent, text="Active step")
        active_box.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(active_box, textvariable=self.active_step_name_var, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(6, 2))
        ttk.Label(active_box, textvariable=self.active_step_description_var, wraplength=420).pack(anchor="w", padx=8, pady=(0, 8))

        # Tabs on the right. Only the active step's settings are rendered here.
        self.right_notebook = ttk.Notebook(parent)
        self.right_notebook.grid(row=1, column=0, sticky="nsew", pady=(0, 8))

        self.settings_tab = ttk.Frame(self.right_notebook, padding=10)
        self.output_tab = ttk.Frame(self.right_notebook, padding=10)
        self.right_notebook.add(self.settings_tab, text="Step settings")
        self.right_notebook.add(self.output_tab, text="Step output")

        self.settings_frame = ttk.Frame(self.settings_tab)
        self.settings_frame.pack(fill="both", expand=True)

        actions = ttk.Frame(self.settings_tab)
        actions.pack(fill="x", pady=(10, 0))
        self.run_step_button = ttk.Button(actions, text="Run active step", command=self.run_active_step)
        self.load_step_button = ttk.Button(actions, text="Load output", command=self.load_active_step_output)
        self.skip_step_button = ttk.Button(actions, text="Skip step", command=self.skip_active_step)
        self.run_step_button.pack(side="left", padx=3)
        self.load_step_button.pack(side="left", padx=3)
        self.skip_step_button.pack(side="left", padx=3)

        ttk.Label(self.output_tab, text="Output / decisions / messages for active step").pack(anchor="w")
        self.step_output_text = tk.Text(self.output_tab, height=12, wrap="word")
        self.step_output_text.pack(fill="both", expand=True, pady=(6, 0))

        log_box = ttk.LabelFrame(parent, text="Run log")
        log_box.grid(row=2, column=0, sticky="nsew")
        self.log_text = tk.Text(log_box, height=10, wrap="word")
        log_scroll = ttk.Scrollbar(log_box, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

    # ------------------------------------------------------------------
    # Load config / workflow creation
    # ------------------------------------------------------------------

    def browse_and_load_config(self):
        path = filedialog.askopenfilename(
            title="Select session_config.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
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

        self.steps = build_steps_from_config(config)
        self.step_status = {}
        for idx, step in enumerate(self.steps):
            self.step_status[step["id"]] = STATUS_READY if idx == 0 else STATUS_LOCKED
        self.step_results = {}
        self.run_events = []
        self.runtime_state = {}
        self.active_step_index = 0 if self.steps else None

        self.render_steps()
        self.render_active_step()
        self.log(f"Loaded session config: {path}")
        self.log(f"Built {len(self.steps)} protocol steps.")

    # ------------------------------------------------------------------
    # Step rendering / state
    # ------------------------------------------------------------------

    def render_steps(self):
        for child in self.steps_container.winfo_children():
            child.destroy()

        self.step_rows = {}

        header = ttk.Frame(self.steps_container)
        header.grid(row=0, column=0, sticky="ew", padx=4, pady=2)
        ttk.Label(header, text="Status", width=15).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Step", width=28).grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Actions").grid(row=0, column=2, sticky="w")

        for i, step in enumerate(self.steps, start=1):
            self.render_step_row(i, step, i - 1)

        self.steps_container.columnconfigure(0, weight=1)

    def render_step_row(self, row_index: int, step: dict[str, Any], step_index: int):
        row = ttk.Frame(self.steps_container)
        row.grid(row=row_index, column=0, sticky="ew", padx=4, pady=3)

        status_var = tk.StringVar(value=self.format_status(step["id"]))
        status_label = ttk.Label(row, textvariable=status_var, width=15)
        status_label.grid(row=0, column=0, sticky="w")

        step_button = ttk.Button(row, text=step["name"], command=lambda i=step_index: self.select_step(i))
        step_button.grid(row=0, column=1, sticky="ew", padx=(0, 4))

        repeat_button = ttk.Button(row, text="Repeat", command=lambda i=step_index: self.repeat_step(i))
        repeat_button.grid(row=0, column=2, sticky="w")

        row.columnconfigure(1, weight=1)
        self.step_rows[step["id"]] = {
            "status_var": status_var,
            "step_button": step_button,
            "repeat_button": repeat_button,
            "row": row,
        }

        self.update_row_controls(step_index)

    def select_step(self, step_index: int):
        if not (0 <= step_index < len(self.steps)):
            return
        status = self.step_status.get(self.steps[step_index]["id"], STATUS_LOCKED)
        if status == STATUS_LOCKED:
            self.log(f"Step is locked: {self.steps[step_index]['name']}")
            return
        self.active_step_index = step_index
        self.render_active_step()
        self.refresh_all_row_controls()

    def format_status(self, step_id: str) -> str:
        status = self.step_status.get(step_id, STATUS_LOCKED)
        return f"{STATUS_SYMBOLS.get(status, '?')} {status}"

    def set_step_status(self, step_index: int, status: str):
        step = self.steps[step_index]
        self.step_status[step["id"]] = status
        row = self.step_rows.get(step["id"])
        if row:
            row["status_var"].set(self.format_status(step["id"]))
        self.update_row_controls(step_index)

    def unlock_next_step_if_needed(self, completed_index: int):
        next_index = completed_index + 1
        if next_index < len(self.steps):
            next_id = self.steps[next_index]["id"]
            if self.step_status.get(next_id) == STATUS_LOCKED:
                self.step_status[next_id] = STATUS_READY
        self.active_step_index = next_index if next_index < len(self.steps) else completed_index
        self.refresh_all_row_controls()
        self.render_active_step()

    def reset_downstream_steps(self, from_index: int):
        for i in range(from_index + 1, len(self.steps)):
            step_id = self.steps[i]["id"]
            if self.step_status.get(step_id) != STATUS_LOCKED:
                self.step_status[step_id] = STATUS_NEEDS_RERUN
            self.step_results.pop(step_id, None)
        self.refresh_all_row_controls()

    def repeat_step(self, step_index: int):
        step = self.steps[step_index]
        status = self.step_status.get(step["id"], STATUS_LOCKED)
        if status not in {STATUS_DONE, STATUS_SKIPPED, STATUS_ERROR, STATUS_NEEDS_RERUN}:
            self.log(f"Cannot repeat step yet: {step['name']}")
            return
        if not step.get("can_repeat", True):
            self.log(f"Step cannot be repeated: {step['name']}")
            return

        self.active_step_index = step_index
        self.step_status[step["id"]] = STATUS_READY
        self.reset_downstream_steps(step_index)
        self.render_active_step()
        self.refresh_all_row_controls()
        self.log(f"Repeating step; downstream steps marked for rerun: {step['name']}")

    def update_row_controls(self, step_index: int):
        if not (0 <= step_index < len(self.steps)):
            return
        step = self.steps[step_index]
        row = self.step_rows.get(step["id"])
        if not row:
            return
        status = self.step_status.get(step["id"], STATUS_LOCKED)
        row["step_button"].state(["!disabled"] if status != STATUS_LOCKED else ["disabled"])
        can_repeat = status in {STATUS_DONE, STATUS_SKIPPED, STATUS_ERROR, STATUS_NEEDS_RERUN} and step.get("can_repeat", True)
        row["repeat_button"].state(["!disabled"] if can_repeat else ["disabled"])
        row["status_var"].set(self.format_status(step["id"]))

    def refresh_all_row_controls(self):
        for i in range(len(self.steps)):
            self.update_row_controls(i)

    def get_active_step(self) -> tuple[int, dict[str, Any]] | tuple[None, None]:
        if self.active_step_index is None or not (0 <= self.active_step_index < len(self.steps)):
            return None, None
        return self.active_step_index, self.steps[self.active_step_index]

    # ------------------------------------------------------------------
    # Active step settings panel
    # ------------------------------------------------------------------

    def render_active_step(self):
        for child in self.settings_frame.winfo_children():
            child.destroy()
        self.step_setting_vars = {}
        self.step_output_text.delete("1.0", "end")

        step_index, step = self.get_active_step()
        if step is None:
            self.active_step_name_var.set("No step selected")
            self.active_step_description_var.set("Load a session config to begin.")
            self.run_step_button.state(["disabled"])
            self.load_step_button.state(["disabled"])
            self.skip_step_button.state(["disabled"])
            return

        status = self.step_status.get(step["id"], STATUS_LOCKED)
        self.active_step_name_var.set(step["name"])
        self.active_step_description_var.set(step.get("description", ""))

        ttk.Label(self.settings_frame, text=f"Status: {self.format_status(step['id'])}").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        settings = step.get("settings", {}) or {}
        if not settings:
            ttk.Label(self.settings_frame, text="No editable settings for this step.").grid(row=1, column=0, sticky="w")
        else:
            for row_index, (key, meta) in enumerate(settings.items(), start=1):
                self.add_step_setting_row(row_index, key, meta)

        previous_result = self.step_results.get(step["id"])
        if previous_result:
            self.step_output_text.insert("end", json.dumps(make_json_safe(previous_result), indent=2))

        can_act = status in {STATUS_READY, STATUS_NEEDS_RERUN, STATUS_ERROR}
        self.run_step_button.state(["!disabled"] if can_act and step.get("can_run", True) else ["disabled"])
        self.load_step_button.configure(text=step.get("load_label") or "Load output")
        self.load_step_button.state(["!disabled"] if can_act and step.get("can_load", False) else ["disabled"])
        self.skip_step_button.state(["!disabled"] if can_act and step.get("can_skip", False) else ["disabled"])

    def add_step_setting_row(self, row_index: int, key: str, meta: dict[str, Any]):
        label = meta.get("label", key)
        value = self.get_setting_value(meta)
        var = self.make_variable(meta.get("type", "str"), value)
        self.step_setting_vars[key] = var

        ttk.Label(self.settings_frame, text=label).grid(row=row_index, column=0, sticky="w", pady=4)

        entry = ttk.Entry(self.settings_frame, textvariable=var)
        entry.grid(row=row_index, column=1, sticky="ew", pady=4, padx=(6, 4))
        if meta.get("readonly"):
            entry.state(["readonly"])

        setting_type = meta.get("type", "str")
        if setting_type in {"path_dir", "file"} and not meta.get("readonly"):
            ttk.Button(
                self.settings_frame,
                text="Browse",
                command=lambda k=key, m=meta: self.browse_setting(k, m),
            ).grid(row=row_index, column=2, sticky="w", pady=4)

        help_text = meta.get("help")
        if help_text:
            ttk.Label(self.settings_frame, text=help_text, wraplength=380).grid(row=row_index + 100, column=0, columnspan=3, sticky="w", pady=(0, 4))

        self.settings_frame.columnconfigure(1, weight=1)

    def make_variable(self, setting_type: str, value: Any) -> tk.Variable:
        if setting_type == "bool":
            return tk.BooleanVar(value=bool(value))
        return tk.StringVar(value="" if value is None else str(value))

    def browse_setting(self, key: str, meta: dict[str, Any]):
        if meta.get("type") == "path_dir":
            path = filedialog.askdirectory(title=f"Select {meta.get('label', key)}")
        else:
            path = filedialog.askopenfilename(title=f"Select {meta.get('label', key)}")
        if path:
            self.step_setting_vars[key].set(path)

    def get_setting_value(self, meta: dict[str, Any]) -> Any:
        source = meta.get("source", "")
        value = self.deep_get(source)
        if value in (None, "") and "default" in meta:
            return meta["default"]
        return value

    def collect_active_step_settings(self) -> dict[str, Any]:
        _, step = self.get_active_step()
        if step is None:
            return {}
        collected = {}
        for key, var in self.step_setting_vars.items():
            meta = (step.get("settings", {}) or {}).get(key, {})
            value = self.coerce_value(var.get(), meta.get("type", "str"))
            collected[key] = value
            source = meta.get("source")
            if source and not meta.get("readonly"):
                self.deep_set(source, value)
        return collected

    @staticmethod
    def coerce_value(value: Any, setting_type: str) -> Any:
        if setting_type == "int":
            try:
                return int(value)
            except (TypeError, ValueError):
                return value
        if setting_type == "float":
            try:
                return float(value)
            except (TypeError, ValueError):
                return value
        if setting_type == "bool":
            if isinstance(value, bool):
                return value
            return str(value).lower() in {"true", "1", "yes", "y", "on"}
        return value

    def deep_get(self, source: str) -> Any:
        if not source:
            return None
        parts = source.split(".")
        if parts[0] == "runtime":
            current: Any = self.runtime_state
            parts = parts[1:]
        elif parts[0] == "config":
            current = self.session_config
            parts = parts[1:]
        elif parts[0] == "step_outputs":
            current = self.step_results
            parts = parts[1:]
        else:
            current = self.runtime_state
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def deep_set(self, source: str, value: Any):
        if not source:
            return
        parts = source.split(".")
        if parts[0] == "runtime":
            current: dict[str, Any] = self.runtime_state
            parts = parts[1:]
        elif parts[0] == "config":
            current = self.session_config
            parts = parts[1:]
        elif parts[0] == "step_outputs":
            current = self.step_results
            parts = parts[1:]
        else:
            current = self.runtime_state
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    # ------------------------------------------------------------------
    # Step actions
    # ------------------------------------------------------------------

    def run_active_step(self):
        step_index, step = self.get_active_step()
        if step is None:
            return
        if self.step_status.get(step["id"]) == STATUS_LOCKED:
            self.log(f"Cannot run locked step: {step['name']}")
            return

        params = self.collect_active_step_settings()
        self.set_step_status(step_index, STATUS_RUNNING)
        self.log(f"Running step: {step['name']}")

        try:
            result = self.dispatch_run_step(step, params)
        except Exception as e:
            self.set_step_status(step_index, STATUS_ERROR)
            self.record_event(step, "error", {"error": str(e), "parameters_used": params})
            self.log(f"ERROR in step {step['name']}: {e}")
            messagebox.showerror("Step failed", str(e))
            self.render_active_step()
            return

        self.complete_step(step_index, COMPLETION_RUN, result, params)

    def load_active_step_output(self):
        step_index, step = self.get_active_step()
        if step is None:
            return
        if not step.get("can_load", False):
            return

        path = filedialog.askopenfilename(
            title=step.get("load_label", "Load output"),
            filetypes=[("All files", "*.*")],
        )
        if not path:
            return

        params = self.collect_active_step_settings()
        result = {
            "loaded_file": path,
            "message": f"Loaded output for step: {step['name']}",
        }
        self.complete_step(step_index, COMPLETION_LOAD, result, params)

    def skip_active_step(self):
        step_index, step = self.get_active_step()
        if step is None or not step.get("can_skip", False):
            return
        params = self.collect_active_step_settings()
        result = {"message": f"Skipped step: {step['name']}"}
        self.complete_step(step_index, COMPLETION_SKIP, result, params, status=STATUS_SKIPPED)

    def complete_step(self, step_index: int, completion_mode: str, result: dict[str, Any], params: dict[str, Any], status: str = STATUS_DONE):
        step = self.steps[step_index]
        result_record = {
            "step_id": step["id"],
            "step_name": step["name"],
            "status": status,
            "completion_mode": completion_mode,
            "parameters_used": params,
            "result": make_json_safe(result),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        self.step_results[step["id"]] = result_record
        self.set_step_status(step_index, status)
        self.record_event(step, completion_mode, result_record)
        self.log(f"Completed step: {step['name']} ({completion_mode})")
        self.write_runtime_config_used()
        self.save_run_log(silent=True)
        self.unlock_next_step_if_needed(step_index)

    def dispatch_run_step(self, step: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        step_id = step["id"]
        if step_id == "initialize_session":
            return self.run_initialize_session(params)

        # Placeholder until the real backend functions are connected.
        return {
            "message": "Placeholder step completed. Backend function not connected yet.",
            "step_id": step_id,
        }

    def run_initialize_session(self, params: dict[str, Any]) -> dict[str, Any]:
        if not self.session_config_path:
            raise RuntimeError("No session_config.json loaded.")

        # If the operator edited the Slidebook folder before initialization,
        # write it into the in-memory config before building runtime_state.
        slidebook_dir = params.get("slidebook_data_dir")
        if slidebook_dir:
            self.session_config.setdefault("settings_used", {}).setdefault("imaging", {})["slidebook_default_dir"] = slidebook_dir

        self.runtime_state = build_main_protocol_runtime(
            self.session_config,
            self.session_config_path,
            create_save_path=True,
        )

        errors = self.runtime_state.get("errors", [])
        warnings = self.runtime_state.get("warnings", [])
        for warning in warnings:
            self.log(f"Warning: {warning}")
        if errors:
            # For now initialization should still block ROI steps if the
            # Slidebook folder/save path is not valid.
            raise RuntimeError("Initialization failed:\n" + "\n".join(errors))

        self.write_runtime_config_used()
        return {
            "message": "Session initialized.",
            "runtime_state": make_json_safe(self.runtime_state),
        }

    # ------------------------------------------------------------------
    # Logging / output files
    # ------------------------------------------------------------------

    def record_event(self, step: dict[str, Any], event_type: str, payload: dict[str, Any]):
        self.run_events.append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "step_id": step.get("id"),
                "step_name": step.get("name"),
                "event_type": event_type,
                "payload": make_json_safe(payload),
            }
        )

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def write_runtime_config_used(self):
        if not self.session_config_path:
            return
        path = self.session_config_path.parent / "runtime_config_used.json"
        data = {
            "session_config": str(self.session_config_path),
            "saved": datetime.now().isoformat(timespec="seconds"),
            "runtime_state": make_json_safe(self.runtime_state),
            "step_results": make_json_safe(self.step_results),
        }
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

    def save_run_log(self, silent: bool = False):
        if not self.session_config_path:
            if not silent:
                messagebox.showwarning("No session", "Load a session config first.")
            return

        log_path = self.session_config_path.parent / "run_log.json"
        data = {
            "session_config": str(self.session_config_path),
            "saved": datetime.now().isoformat(timespec="seconds"),
            "step_status": self.step_status,
            "step_results": make_json_safe(self.step_results),
            "run_events": make_json_safe(self.run_events),
            "run_notes": self.run_notes_text.get("1.0", "end").strip(),
            "log_text": self.log_text.get("1.0", "end").strip(),
        }

        try:
            with log_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
        except Exception as e:
            if not silent:
                messagebox.showerror("Save failed", str(e))
            return

        if not silent:
            messagebox.showinfo("Run log saved", f"Saved run log:\n{log_path}")
        self.log(f"Saved run log: {log_path}")


if __name__ == "__main__":
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    app = RunSessionGUI(config_path)
    app.mainloop()
