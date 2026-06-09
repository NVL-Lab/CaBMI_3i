
"""
cabmi_config_gui_v5.py

Redesigned CaBMI configuration GUI.

Main design:
    LEFT PANEL:
        Session selection only:
        user, project, animal, date/day, save path, session notes.

    RIGHT TOP:
        Experiment configuration template:
        experiment/template name, description, notes, capabilities,
        load/save/save-as template.

    RIGHT BOTTOM:
        Settings tabs generated from selected capabilities.

Animal creation/cloning happens through pop-up windows.
Template = experiment configuration preset.
"""

from __future__ import annotations

import copy
import json
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from config_manager import ConfigManager, DEFAULT_TEMPLATE


# For testing:
CONFIG_ROOT = Path(r"C:/Users/Nuria/Documents/Data/gui_tests/config")
DATA_ROOT = Path(r"C:/Users/Nuria/Documents/Data/gui_tests/config_data")


DEFAULT_EXPERIMENT_TEMPLATE = {
    "template_name": "default_cabmi",
    "display_name": "Default CaBMI",
    "description": "Default CaBMI experiment configuration.",
    "notes": "",
    "capabilities": {
        "cabmi": True,
        "imaging": True,
        "feedback": True,
        "random_stimulation": True,
        "holography": False,
        "photopharm": False,
        "behavior_camera": False,
        "external_trigger": False,
    },
    "cabmi": {
        "baseline_len_sec": 300,
        "bmi_len_sec": 1800,
        "ensemble_count": 2,
        "neurons_per_ensemble": 3,
        "sec_per_reward_range": [20, 60],
        "f0_win": 30,
        "load_calibration": False,
    },
    "imaging": {
        "frame_rate_hz": 30,
        "slidebook_default_dir": "",
    },
    "feedback": {
        "enabled": True,
        "arduino_com": "COM3",
        "arduino_baudrate": 9600,
    },
    "random_stimulation": {
        "enabled": True,
        "ihsi_mean": 10,
        "ihsi_range": 3,
    },
    "holography": {
        "enabled": False,
        "laser_power_mw": 0,
        "stim_duration_ms": 0,
        "target_cells": "",
    },
    "photopharm": {
        "enabled": False,
        "activation_wavelength_nm": 450,
        "reset_wavelength_nm": 375,
        "activation_duration_ms": 300,
        "reset_duration_ms": 1000,
    },
    "behavior_camera": {
        "enabled": False,
        "camera_name": "",
        "frame_rate_hz": 0,
    },
    "external_trigger": {
        "enabled": False,
        "device": "",
        "channel": "",
    },
    "custom": {},
}


CAPABILITY_LABELS = {
    "cabmi": "CaBMI",
    "imaging": "Imaging / Frequency",
    "feedback": "Feedback",
    "random_stimulation": "Random stimulation",
    "holography": "Holography",
    "photopharm": "Photopharm",
    "behavior_camera": "Behavior camera",
    "external_trigger": "External trigger",
}


class CaBMIConfigGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("CaBMI Config GUI v5")
        self.geometry("1200x850")

        self.cm = ConfigManager(CONFIG_ROOT)
        self.current_template = copy.deepcopy(DEFAULT_EXPERIMENT_TEMPLATE)
        self.current_template_name = "default_cabmi"
        self.current_template_scope = "project"

        self.capability_vars: dict[str, tk.BooleanVar] = {}
        self.setting_vars: dict[str, dict[str, tk.Variable]] = {}
        self.settings_notebook: ttk.Notebook | None = None

        self._build_variables()
        self._build_layout()
        self.refresh_users()

    # ------------------------------------------------------------------
    # Variables
    # ------------------------------------------------------------------

    def _build_variables(self):
        self.user_var = tk.StringVar()
        self.project_var = tk.StringVar()
        self.animal_var = tk.StringVar()

        self.date_var = tk.StringVar(value=date.today().strftime("%Y_%m_%d"))
        self.day_var = tk.StringVar()
        self.save_base_dir_var = tk.StringVar(value=str(DATA_ROOT))

        self.template_var = tk.StringVar()
        self.template_name_var = tk.StringVar()
        self.template_description_var = tk.StringVar()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self):
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(outer, text="CaBMI Session Configuration", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", pady=(0, 10))

        main = ttk.PanedWindow(outer, orient="horizontal")
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, padding=6)
        right = ttk.Frame(main, padding=6)

        main.add(left, weight=1)
        main.add(right, weight=3)

        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, parent):
        select_box = ttk.LabelFrame(parent, text="Session setup")
        select_box.pack(fill="x", pady=5)

        self.user_combo = self._combo_row(select_box, "User", self.user_var, self.on_user_changed, 0)
        ttk.Button(select_box, text="New", command=self.new_user).grid(row=0, column=2, padx=4)

        self.project_combo = self._combo_row(select_box, "Project", self.project_var, self.on_project_changed, 1)
        ttk.Button(select_box, text="New", command=self.new_project).grid(row=1, column=2, padx=4)

        self.animal_combo = self._combo_row(select_box, "Animal", self.animal_var, self.on_animal_changed, 2)
        ttk.Button(select_box, text="New", command=self.new_animal_popup).grid(row=2, column=2, padx=4)
        ttk.Button(select_box, text="Clone", command=self.clone_animal_popup).grid(row=2, column=3, padx=4)
        ttk.Button(select_box, text="Edit", command=self.edit_animal_popup).grid(row=2, column=4, padx=4)

        self._entry_row(select_box, "Date", self.date_var, 3)
        self._entry_row(select_box, "Day", self.day_var, 4)

        ttk.Label(select_box, text="Save path").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Entry(select_box, textvariable=self.save_base_dir_var).grid(row=5, column=1, sticky="ew", pady=4)
        ttk.Button(select_box, text="Browse", command=self.browse_save_base_dir).grid(row=5, column=2, padx=4)

        ttk.Button(select_box, text="Refresh day", command=self.refresh_suggested_day).grid(
            row=6, column=1, sticky="e", pady=4
        )

        ttk.Label(select_box, text="Session notes / log").grid(row=7, column=0, sticky="nw", pady=4)
        self.session_notes_text = tk.Text(select_box, height=6, wrap="word")
        self.session_notes_text.grid(row=7, column=1, columnspan=4, sticky="ew", pady=4)

        action_frame = ttk.Frame(select_box)
        action_frame.grid(row=8, column=0, columnspan=5, sticky="e", pady=(8, 0))
        ttk.Button(action_frame, text="Preview Session Config", command=self.preview_session_config).pack(side="left", padx=4)
        ttk.Button(action_frame, text="Save Session Config", command=self.save_session_config).pack(side="left", padx=4)
        ttk.Button(action_frame, text="Launch CaBMI (not active yet)", state="disabled").pack(side="left", padx=4)

        for i in range(5):
            select_box.columnconfigure(i, weight=1)

        status_box = ttk.LabelFrame(parent, text="Status")
        status_box.pack(fill="both", expand=True, pady=8)
        self.status_text = tk.Text(status_box, height=10, wrap="word")
        self.status_text.pack(fill="both", expand=True)
        self.log("Select or create a user to begin.")

    def _build_right_panel(self, parent):
        parent.rowconfigure(0, weight=0)
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        experiment_box = ttk.LabelFrame(parent, text="Experiment configuration template")
        experiment_box.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._build_experiment_template_panel(experiment_box)

        settings_box = ttk.LabelFrame(parent, text="Settings for selected capabilities")
        settings_box.grid(row=1, column=0, sticky="nsew")
        settings_box.rowconfigure(0, weight=1)
        settings_box.columnconfigure(0, weight=1)

        self.settings_notebook = ttk.Notebook(settings_box)
        self.settings_notebook.grid(row=0, column=0, sticky="nsew")

    def _build_experiment_template_panel(self, parent):
        # Template selection
        ttk.Label(parent, text="Template").grid(row=0, column=0, sticky="w", pady=3)
        self.template_combo = ttk.Combobox(parent, textvariable=self.template_var, state="readonly")
        self.template_combo.grid(row=0, column=1, sticky="ew", pady=3)
        self.template_combo.bind("<<ComboboxSelected>>", self.on_template_changed)

        ttk.Button(parent, text="Load", command=self.load_selected_template).grid(row=0, column=2, padx=4)
        ttk.Button(parent, text="Save", command=self.save_template_overwrite).grid(row=0, column=3, padx=4)
        ttk.Button(parent, text="Save As", command=self.save_template_as_new).grid(row=0, column=4, padx=4)

        self._entry_row(parent, "Experiment/template name", self.template_name_var, 1)
        self._entry_row(parent, "Description", self.template_description_var, 2)

        ttk.Label(parent, text="Notes").grid(row=3, column=0, sticky="nw", pady=3)
        self.template_notes_text = tk.Text(parent, height=3, wrap="word")
        self.template_notes_text.grid(row=3, column=1, columnspan=4, sticky="ew", pady=3)

        # Capabilities
        cap_frame = ttk.LabelFrame(parent, text="Capabilities")
        cap_frame.grid(row=4, column=0, columnspan=5, sticky="ew", pady=(8, 3))

        for idx, (key, label) in enumerate(CAPABILITY_LABELS.items()):
            var = tk.BooleanVar(value=False)
            self.capability_vars[key] = var
            cb = ttk.Checkbutton(
                cap_frame,
                text=label,
                variable=var,
                command=self.on_capabilities_changed,
            )
            cb.grid(row=idx // 4, column=idx % 4, sticky="w", padx=8, pady=3)

        parent.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    # Refresh dropdowns
    # ------------------------------------------------------------------

    def refresh_users(self):
        users = self.cm.list_users()
        self.user_combo["values"] = users
        if users and not self.user_var.get():
            self.user_var.set(users[0])
            self.on_user_changed()

    def refresh_projects(self):
        user = self.user_var.get()
        projects = self.cm.list_projects(user) if user else []
        self.project_combo["values"] = projects
        if projects:
            if self.project_var.get() not in projects:
                self.project_var.set(projects[0])
            self.on_project_changed()
        else:
            self.project_var.set("")
            self.refresh_animals()
            self.refresh_templates()

    def refresh_animals(self):
        user, project = self.user_var.get(), self.project_var.get()
        animals = []
        if user and project:
            animals = [a["animal_id"] for a in self.cm.list_animals(user, project)]
        self.animal_combo["values"] = animals
        if animals:
            if self.animal_var.get() not in animals:
                self.animal_var.set(animals[0])
            self.on_animal_changed()
        else:
            self.animal_var.set("")

    def refresh_templates(self):
        user, project = self.user_var.get(), self.project_var.get()
        labels = []
        if user and project:
            # Make sure a default project template exists in new v5 format.
            self.ensure_v5_default_template(user, project)
            rows = self.cm.list_all_templates(user, project)
            labels = [f"{r['scope']}:{r['name']}" for r in rows]
        self.template_combo["values"] = labels
        if labels:
            preferred = "project:default_cabmi"
            if preferred in labels:
                self.template_var.set(preferred)
            elif self.template_var.get() not in labels:
                self.template_var.set(labels[0])
            self.load_selected_template()
        else:
            self.template_var.set("")
            self.load_template_into_gui(copy.deepcopy(DEFAULT_EXPERIMENT_TEMPLATE))

    def ensure_v5_default_template(self, user, project):
        try:
            current = self.cm.load_template(user, project, "default_cabmi", scope="project")
        except Exception:
            current = {}

        if "capabilities" not in current:
            try:
                self.cm.save_project_template(
                    user, project, "default_cabmi", copy.deepcopy(DEFAULT_EXPERIMENT_TEMPLATE), overwrite=True
                )
            except Exception as e:
                self.log(f"Could not update default template: {e}")

    def refresh_suggested_day(self):
        user, project, animal = self.user_var.get(), self.project_var.get(), self.animal_var.get()
        experiment_name = self.template_name_var.get() or self.current_template_name or "experiment"
        if user and project and animal:
            self.day_var.set(self.cm.suggest_next_day(user, project, animal, experiment_name))
            self.log(f"Suggested day: {self.day_var.get()}")

    # ------------------------------------------------------------------
    # Change handlers
    # ------------------------------------------------------------------

    def on_user_changed(self, event=None):
        self.log(f"Selected user: {self.user_var.get()}")
        self.refresh_projects()

    def on_project_changed(self, event=None):
        self.log(f"Selected project: {self.project_var.get()}")
        self.refresh_animals()
        self.refresh_templates()
        self.refresh_suggested_day()

    def on_animal_changed(self, event=None):
        self.refresh_suggested_day()

    def on_template_changed(self, event=None):
        self.load_selected_template()

    def on_capabilities_changed(self):
        self.collect_template_from_gui(update_current=True)
        self.rebuild_settings_tabs()
        self.refresh_suggested_day()

    # ------------------------------------------------------------------
    # User/project creation
    # ------------------------------------------------------------------

    def new_user(self):
        name = simpledialog.askstring("New User", "User name:")
        if not name:
            return
        self.cm.create_user(name)
        self.user_var.set(self.slug_for_display(name))
        self.refresh_users()
        self.log(f"Created user: {name}")

    def new_project(self):
        user = self.require_user()
        if not user:
            return
        name = simpledialog.askstring("New Project", "Project name:")
        if not name:
            return
        self.cm.create_project(user, name)
        self.project_var.set(self.slug_for_display(name))
        self.refresh_projects()
        self.log(f"Created project: {name}")

    # ------------------------------------------------------------------
    # Animal popups
    # ------------------------------------------------------------------

    def new_animal_popup(self):
        user, project = self.require_user_project()
        if not project:
            return
        self.open_animal_popup(title="New Animal", mode="new")

    def clone_animal_popup(self):
        user, project = self.require_user_project()
        animal_id = self.animal_var.get()
        if not (user and project and animal_id):
            messagebox.showwarning("Missing animal", "Select an animal to clone.")
            return

        animal = self.cm.get_animal(user, project, animal_id)
        if not animal:
            return

        clone = copy.deepcopy(animal)
        clone["animal_id"] = animal_id + "_copy"
        self.open_animal_popup(title="Clone Animal", mode="new", animal=clone)

    def edit_animal_popup(self):
        user, project = self.require_user_project()
        animal_id = self.animal_var.get()
        if not (user and project and animal_id):
            messagebox.showwarning("Missing animal", "Select an animal to edit.")
            return

        animal = self.cm.get_animal(user, project, animal_id)
        if not animal:
            return
        self.open_animal_popup(title="Edit Animal", mode="edit", animal=animal)

    def open_animal_popup(self, title, mode, animal=None):
        animal = animal or {"animal_id": "", "sex": "U", "genotype": "", "notes": ""}

        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("450x330")
        win.transient(self)
        win.grab_set()

        animal_id_var = tk.StringVar(value=animal.get("animal_id", ""))
        sex_var = tk.StringVar(value=animal.get("sex", "U"))
        genotype_var = tk.StringVar(value=animal.get("genotype", ""))

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Animal ID").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=animal_id_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Sex").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(frame, textvariable=sex_var, values=["M", "F", "U"], state="readonly").grid(
            row=1, column=1, sticky="w", pady=4
        )

        ttk.Label(frame, text="Genotype").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=genotype_var).grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Notes").grid(row=3, column=0, sticky="nw", pady=4)
        notes_text = tk.Text(frame, height=4, wrap="word")
        notes_text.grid(row=3, column=1, sticky="ew", pady=4)
        notes_text.insert("1.0", animal.get("notes", ""))

        def save():
            user, project = self.require_user_project()
            new_id = animal_id_var.get().strip()
            if not new_id:
                messagebox.showerror("Missing animal ID", "Animal ID cannot be empty.")
                return

            existing = self.cm.get_animal(user, project, new_id)
            overwrite = mode == "edit" and existing is not None

            if mode == "new" and existing is not None:
                messagebox.showerror("Animal exists", f"Animal '{new_id}' already exists.")
                return

            self.cm.save_animal(
                user,
                project,
                animal_id=new_id,
                sex=sex_var.get(),
                genotype=genotype_var.get(),
                notes=notes_text.get("1.0", "end").strip(),
                overwrite=overwrite,
            )
            self.refresh_animals()
            self.animal_var.set(new_id)
            self.refresh_animals()
            self.log(f"Saved animal: {new_id}")
            win.destroy()

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(button_frame, text="Save", command=save).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Cancel", command=win.destroy).pack(side="left", padx=4)

        frame.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    # Template loading/saving
    # ------------------------------------------------------------------

    def load_selected_template(self):
        label = self.template_var.get()
        if not label or ":" not in label:
            return

        user, project = self.user_var.get(), self.project_var.get()
        scope, name = label.split(":", 1)

        try:
            template = self.cm.load_template(user, project, name, scope=scope)
        except Exception as e:
            messagebox.showerror("Template error", str(e))
            return

        template = self.normalize_template(template)
        self.current_template = template
        self.current_template_scope = scope
        self.current_template_name = name

        self.load_template_into_gui(template)
        self.log(f"Loaded experiment template: {label}")

    def normalize_template(self, template):
        normalized = copy.deepcopy(DEFAULT_EXPERIMENT_TEMPLATE)
        template = template or {}

        # Convert old template structure if needed.
        if "task" in template:
            task = template.get("task", {})
            normalized["cabmi"]["baseline_len_sec"] = task.get("baseline_len_sec", normalized["cabmi"]["baseline_len_sec"])
            normalized["cabmi"]["bmi_len_sec"] = task.get("bmi_len_sec", normalized["cabmi"]["bmi_len_sec"])
            normalized["cabmi"]["ensemble_count"] = task.get("ensemble_count", normalized["cabmi"]["ensemble_count"])
            normalized["cabmi"]["neurons_per_ensemble"] = task.get("neurons_per_ensemble", normalized["cabmi"]["neurons_per_ensemble"])
            normalized["cabmi"]["sec_per_reward_range"] = task.get("sec_per_reward_range", normalized["cabmi"]["sec_per_reward_range"])

        if "feedback" in template:
            normalized["feedback"].update(template.get("feedback", {}))

        if "advanced" in template:
            adv = template.get("advanced", {})
            normalized["cabmi"]["f0_win"] = adv.get("f0_win", normalized["cabmi"]["f0_win"])
            normalized["cabmi"]["load_calibration"] = adv.get("load_calibration", normalized["cabmi"]["load_calibration"])
            normalized["random_stimulation"]["ihsi_mean"] = adv.get("random_stim_ihsi_mean", normalized["random_stimulation"]["ihsi_mean"])
            normalized["random_stimulation"]["ihsi_range"] = adv.get("random_stim_ihsi_range", normalized["random_stimulation"]["ihsi_range"])

        # Overlay new format sections.
        for key, value in template.items():
            if isinstance(value, dict) and key in normalized and isinstance(normalized[key], dict):
                normalized[key].update(value)
            else:
                normalized[key] = value

        normalized.setdefault("capabilities", copy.deepcopy(DEFAULT_EXPERIMENT_TEMPLATE["capabilities"]))
        return normalized

    def load_template_into_gui(self, template):
        self.current_template = copy.deepcopy(template)

        self.template_name_var.set(template.get("display_name", template.get("template_name", "")))
        self.template_description_var.set(template.get("description", ""))

        self.template_notes_text.delete("1.0", "end")
        self.template_notes_text.insert("1.0", template.get("notes", ""))

        caps = template.get("capabilities", {})
        for key, var in self.capability_vars.items():
            var.set(bool(caps.get(key, False)))

        self.rebuild_settings_tabs()
        self.refresh_suggested_day()

    def collect_template_from_gui(self, update_current=False):
        template = copy.deepcopy(self.current_template)

        template["display_name"] = self.template_name_var.get().strip()
        template["description"] = self.template_description_var.get().strip()
        template["notes"] = self.template_notes_text.get("1.0", "end").strip()
        template["capabilities"] = {key: bool(var.get()) for key, var in self.capability_vars.items()}

        for section, fields in self.setting_vars.items():
            template.setdefault(section, {})
            for key, var in fields.items():
                template[section][key] = self.variable_value(var)

        if update_current:
            self.current_template = copy.deepcopy(template)

        return template

    def save_template_overwrite(self):
        user, project = self.require_user_project()
        if not project:
            return

        if self.current_template_scope == "shared":
            messagebox.showinfo(
                "Shared template",
                "Shared templates are read-only. Use Save As to create a project copy.",
            )
            return

        template = self.collect_template_from_gui(update_current=True)
        name = self.current_template_name or self.slug_for_display(template.get("display_name", "template"))

        try:
            self.cm.save_project_template(user, project, name, template, overwrite=True)
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return

        self.refresh_templates()
        self.template_var.set(f"project:{name}")
        self.log(f"Saved experiment template: {name}")

    def save_template_as_new(self):
        user, project = self.require_user_project()
        if not project:
            return

        suggested = self.slug_for_display(self.template_name_var.get() or "new_template")
        name = simpledialog.askstring("Save Template As", "New template name:", initialvalue=suggested)
        if not name:
            return

        template = self.collect_template_from_gui(update_current=True)

        try:
            self.cm.save_project_template(user, project, name, template, overwrite=False)
        except ValueError:
            overwrite = messagebox.askyesno("Template exists", f"Template '{name}' already exists. Overwrite?")
            if not overwrite:
                return
            self.cm.save_project_template(user, project, name, template, overwrite=True)
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return

        self.current_template_name = self.slug_for_display(name)
        self.current_template_scope = "project"
        self.refresh_templates()
        self.template_var.set(f"project:{self.current_template_name}")
        self.log(f"Saved new experiment template: {name}")

    # ------------------------------------------------------------------
    # Settings tabs
    # ------------------------------------------------------------------

    def rebuild_settings_tabs(self):
        if self.settings_notebook is None:
            return

        for tab in self.settings_notebook.tabs():
            self.settings_notebook.forget(tab)

        self.setting_vars = {}

        template = self.collect_template_from_gui(update_current=True) if hasattr(self, "template_notes_text") else self.current_template
        capabilities = template.get("capabilities", {})

        for key, active in capabilities.items():
            if not active:
                continue
            if key not in CAPABILITY_LABELS:
                continue
            section_data = template.get(key, {})
            self.add_settings_tab(key, CAPABILITY_LABELS[key], section_data)

        # Always show custom tab, but keep it simple.
        self.add_custom_tab(template.get("custom", {}))

    def add_settings_tab(self, section_key, title, data):
        frame = ttk.Frame(self.settings_notebook, padding=10)
        self.settings_notebook.add(frame, text=title)

        self.setting_vars[section_key] = {}

        row = 0
        for key, value in data.items():
            ttk.Label(frame, text=key).grid(row=row, column=0, sticky="w", pady=3)

            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                widget = ttk.Checkbutton(frame, variable=var)
                widget.grid(row=row, column=1, sticky="w", pady=3)
            else:
                var = tk.StringVar(value=self.value_to_string(value))
                widget = ttk.Entry(frame, textvariable=var)
                widget.grid(row=row, column=1, sticky="ew", pady=3)

            self.setting_vars[section_key][key] = var
            row += 1

        frame.columnconfigure(1, weight=1)

    def add_custom_tab(self, custom_data):
        frame = ttk.Frame(self.settings_notebook, padding=10)
        self.settings_notebook.add(frame, text="Custom")

        ttk.Label(
            frame,
            text="Custom parameters as JSON. Use this for temporary or new parameters not yet in the GUI.",
        ).pack(anchor="w", pady=(0, 5))

        self.custom_json_text = tk.Text(frame, height=12, wrap="none")
        self.custom_json_text.pack(fill="both", expand=True)
        self.custom_json_text.insert("1.0", json.dumps(custom_data or {}, indent=2))

    # ------------------------------------------------------------------
    # Session config
    # ------------------------------------------------------------------

    def build_current_session_config(self):
        user = self.user_var.get()
        project = self.project_var.get()
        animal = self.animal_var.get()

        if not user:
            raise ValueError("Select a user.")
        if not project:
            raise ValueError("Select a project.")
        if not animal:
            raise ValueError("Select an animal.")

        template = self.collect_template_from_gui(update_current=True)

        # Parse custom JSON.
        if hasattr(self, "custom_json_text"):
            try:
                template["custom"] = json.loads(self.custom_json_text.get("1.0", "end").strip() or "{}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Custom JSON is invalid: {e}")

        experiment_name = self.slug_for_display(template.get("display_name") or template.get("template_name") or "experiment")

        # Ensure experiment record exists because ConfigManager requires it.
        if not self.cm.get_experiment(user, project, experiment_name):
            self.cm.save_experiment(
                user,
                project,
                experiment_name=experiment_name,
                description=template.get("description", ""),
                notes=template.get("notes", ""),
                overwrite=False,
            )

        return self.cm.build_session_config(
            user_name=user,
            project_name=project,
            experiment_name=experiment_name,
            animal_id=animal,
            settings=template,
            settings_template=self.current_template_name,
            settings_scope=self.current_template_scope,
            session_date=self.date_var.get(),
            day=self.day_var.get() or None,
            extra={
                "session_notes": self.session_notes_text.get("1.0", "end").strip()
            },
        )

    def preview_session_config(self):
        try:
            config = self.build_current_session_config()
        except Exception as e:
            messagebox.showerror("Cannot build session config", str(e))
            return

        top = tk.Toplevel(self)
        top.title("Session Config Preview")
        top.geometry("850x650")

        text = tk.Text(top, wrap="none")
        text.pack(fill="both", expand=True)
        text.insert("1.0", json.dumps(config, indent=2))
        text.config(state="disabled")

    def save_session_config(self):
        try:
            config = self.build_current_session_config()
        except Exception as e:
            messagebox.showerror("Cannot build session config", str(e))
            return

        overwrite = False
        session_id = config["session_id"]

        if self.cm.session_exists(self.user_var.get(), self.project_var.get(), session_id):
            overwrite = messagebox.askyesno(
                "Session already exists",
                f"This session already exists:\n\n{session_id}\n\nOverwrite it?",
            )
            if not overwrite:
                self.log(f"Save cancelled because session already exists: {session_id}")
                return

        try:
            path = self.cm.save_session_config(
                user_name=self.user_var.get(),
                project_name=self.project_var.get(),
                session_config=config,
                save_base_dir=Path(self.save_base_dir_var.get()),
                register=True,
                overwrite=overwrite,
            )
        except FileExistsError as e:
            overwrite_file = messagebox.askyesno(
                "File already exists",
                f"{e}\n\nOverwrite the existing file?",
            )
            if not overwrite_file:
                return
            path = self.cm.save_session_config(
                user_name=self.user_var.get(),
                project_name=self.project_var.get(),
                session_config=config,
                save_base_dir=Path(self.save_base_dir_var.get()),
                register=True,
                overwrite=True,
            )
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return

        messagebox.showinfo("Session saved", f"Saved session config:\n{path}")
        self.log(f"Saved session config: {path}")
        self.refresh_suggested_day()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _combo_row(self, parent, label, var, callback, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        combo = ttk.Combobox(parent, textvariable=var, state="readonly")
        combo.grid(row=row, column=1, sticky="ew", pady=4)
        combo.bind("<<ComboboxSelected>>", callback)
        return combo

    def _entry_row(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", pady=3)
        parent.columnconfigure(1, weight=1)
        return entry

    def browse_save_base_dir(self):
        path = filedialog.askdirectory(title="Select save base directory")
        if path:
            self.save_base_dir_var.set(path)

    def require_user(self):
        user = self.user_var.get()
        if not user:
            messagebox.showwarning("Missing user", "Select or create a user first.")
            return None
        return user

    def require_user_project(self):
        user = self.require_user()
        project = self.project_var.get()
        if user and not project:
            messagebox.showwarning("Missing project", "Select or create a project first.")
            return None, None
        return user, project

    def log(self, msg):
        if hasattr(self, "status_text"):
            self.status_text.insert("end", f"{msg}\n")
            self.status_text.see("end")

    @staticmethod
    def slug_for_display(name):
        name = str(name).strip().lower()
        out = []
        prev_underscore = False
        for ch in name:
            if ch.isalnum():
                out.append(ch)
                prev_underscore = False
            else:
                if not prev_underscore:
                    out.append("_")
                    prev_underscore = True
        return "".join(out).strip("_") or "unnamed"

    @staticmethod
    def value_to_string(value):
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return str(value)

    @staticmethod
    def variable_value(var):
        value = var.get()
        if isinstance(var, tk.BooleanVar):
            return bool(value)

        s = str(value).strip()
        if s == "":
            return ""

        # Try JSON first for lists/dicts.
        if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")):
            try:
                return json.loads(s)
            except Exception:
                return s

        # Try number conversion.
        try:
            x = float(s)
            if x.is_integer():
                return int(x)
            return x
        except ValueError:
            return s


if __name__ == "__main__":
    app = CaBMIConfigGUI()
    app.mainloop()
