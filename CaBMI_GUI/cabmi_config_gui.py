
"""
cabmi_config_gui.py

First single-page GUI for CaBMI session configuration.

This version does NOT launch CaBMI yet.
It only tests the workflow:

User -> Project -> Experiment -> Animal -> Template -> Session Config

Template dropdown loads templates automatically when selected.
The Load button reloads the selected template explicitly.

Requirements:
    - config_manager_project_hierarchy.py must be in the same folder,
      or rename it to config_manager.py and update the import below.
"""

from __future__ import annotations

import copy
import json
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from config_manager import ConfigManager, DEFAULT_TEMPLATE


CONFIG_ROOT = Path(r"C:/Users/Nuria/Documents/Data/gui_tests/config")
DATA_ROOT = Path(r"C:/Users/Nuria/Documents/Data/gui_tests/config_data")


class CaBMIConfigGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("CaBMI Config GUI")
        self.geometry("1100x850")

        self.cm = ConfigManager(CONFIG_ROOT)

        self.current_settings = copy.deepcopy(DEFAULT_TEMPLATE)
        self.current_template_scope = "project"
        self.current_template_name = "default_cabmi"

        self._build_variables()
        self._build_layout()
        self.refresh_users()

    # ------------------------------------------------------------------
    # Variables
    # ------------------------------------------------------------------

    def _build_variables(self):
        self.user_var = tk.StringVar()
        self.project_var = tk.StringVar()
        self.experiment_var = tk.StringVar()
        self.animal_var = tk.StringVar()
        self.template_var = tk.StringVar()

        self.date_var = tk.StringVar(value=date.today().strftime("%Y_%m_%d"))
        self.day_var = tk.StringVar()
        self.save_base_dir_var = tk.StringVar(value=str(DATA_ROOT))

        # Experiment fields
        self.exp_display_var = tk.StringVar()
        self.exp_description_var = tk.StringVar()
        self.exp_notes_var = tk.StringVar()

        # Animal fields
        self.animal_id_var = tk.StringVar()
        self.sex_var = tk.StringVar(value="U")
        self.genotype_var = tk.StringVar()
        self.animal_notes_var = tk.StringVar()

        # Settings fields
        self.frame_rate_var = tk.StringVar()
        self.baseline_len_var = tk.StringVar()
        self.bmi_len_var = tk.StringVar()
        self.ensemble_count_var = tk.StringVar()
        self.neurons_per_ensemble_var = tk.StringVar()
        self.reward_min_var = tk.StringVar()
        self.reward_max_var = tk.StringVar()

        self.feedback_enabled_var = tk.BooleanVar()
        self.arduino_com_var = tk.StringVar()
        self.arduino_baudrate_var = tk.StringVar()

        self.save_data_var = tk.BooleanVar()
        self.load_calibration_var = tk.BooleanVar()
        self.f0_win_var = tk.StringVar()
        self.ihsi_mean_var = tk.StringVar()
        self.ihsi_range_var = tk.StringVar()

        self.slidebook_dir_var = tk.StringVar()

        # Session log / notes
        self.session_notes_var = tk.StringVar()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self):
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(
            outer,
            text="CaBMI Session Configuration",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w", pady=(0, 10))

        # Scrollable-ish main area using PanedWindow
        main = ttk.PanedWindow(outer, orient="horizontal")
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, padding=6)
        right = ttk.Frame(main, padding=6)
        main.add(left, weight=1)
        main.add(right, weight=2)

        self._build_selection_panel(left)
        self._build_details_panel(right)

        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(10, 0))

        ttk.Button(bottom, text="Launch CaBMI (not active yet)", state="disabled").pack(
            side="right", padx=5
        )

    def _build_selection_panel(self, parent):
        box = ttk.LabelFrame(parent, text="Select")
        box.pack(fill="x", pady=5)

        self.user_combo = self._combo_row(
            box, "User", self.user_var, self.on_user_changed, row=0
        )
        ttk.Button(box, text="New User", command=self.new_user).grid(row=0, column=2, padx=4)

        self.project_combo = self._combo_row(
            box, "Project", self.project_var, self.on_project_changed, row=1
        )
        ttk.Button(box, text="New Project", command=self.new_project).grid(row=1, column=2, padx=4)

        self.experiment_combo = self._combo_row(
            box, "Experiment", self.experiment_var, self.on_experiment_changed, row=2
        )
        ttk.Button(box, text="New", command=self.new_experiment).grid(row=2, column=2, padx=4)
        ttk.Button(box, text="Clone", command=self.clone_experiment).grid(row=2, column=3, padx=4)

        self.animal_combo = self._combo_row(
            box, "Animal", self.animal_var, self.on_animal_changed, row=3
        )
        ttk.Button(box, text="New", command=self.new_animal).grid(row=3, column=2, padx=4)
        ttk.Button(box, text="Clone", command=self.clone_animal).grid(row=3, column=3, padx=4)

        self.template_combo = self._combo_row(
            box, "Template", self.template_var, self.on_template_changed, row=4
        )
        ttk.Button(box, text="Load", command=self.on_template_changed).grid(row=4, column=2, padx=4)
        ttk.Button(box, text="New", command=self.new_template).grid(row=4, column=3, padx=4)
        ttk.Button(box, text="Clone", command=self.clone_template).grid(row=4, column=4, padx=4)

        for i in range(5):
            box.columnconfigure(i, weight=1)

        session_box = ttk.LabelFrame(parent, text="Session")
        session_box.pack(fill="x", pady=8)

        self._entry_row(session_box, "Date", self.date_var, row=0)
        self._entry_row(session_box, "Day", self.day_var, row=1)

        ttk.Label(session_box, text="Save base dir").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(session_box, textvariable=self.save_base_dir_var).grid(
            row=2, column=1, sticky="ew", pady=3
        )
        ttk.Button(session_box, text="Browse", command=self.browse_save_base_dir).grid(
            row=2, column=2, padx=4
        )

        ttk.Button(session_box, text="Refresh suggested day", command=self.refresh_suggested_day).grid(
            row=3, column=1, sticky="e", pady=5
        )

        ttk.Label(session_box, text="Session notes / log").grid(row=4, column=0, sticky="nw", pady=3)
        self.session_notes_text = tk.Text(session_box, height=4, wrap="word")
        self.session_notes_text.grid(row=4, column=1, columnspan=2, sticky="ew", pady=3)

        action_frame = ttk.Frame(session_box)
        action_frame.grid(row=5, column=0, columnspan=3, sticky="e", pady=(8, 0))

        ttk.Button(
            action_frame,
            text="Preview Session Config",
            command=self.preview_session_config,
        ).pack(side="left", padx=4)

        ttk.Button(
            action_frame,
            text="Save Session Config",
            command=self.save_session_config,
        ).pack(side="left", padx=4)

        session_box.columnconfigure(1, weight=1)

        info_box = ttk.LabelFrame(parent, text="Status")
        info_box.pack(fill="both", expand=True, pady=8)

        self.status_text = tk.Text(info_box, height=14, wrap="word")
        self.status_text.pack(fill="both", expand=True)
        self.log("Select or create a user to begin.")

    def _build_details_panel(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)

        exp_tab = ttk.Frame(notebook, padding=10)
        animal_tab = ttk.Frame(notebook, padding=10)
        settings_tab = ttk.Frame(notebook, padding=10)
        advanced_tab = ttk.Frame(notebook, padding=10)

        notebook.add(exp_tab, text="Experiment")
        notebook.add(animal_tab, text="Animal")
        notebook.add(settings_tab, text="Settings")
        notebook.add(advanced_tab, text="Advanced")

        self._build_experiment_tab(exp_tab)
        self._build_animal_tab(animal_tab)
        self._build_settings_tab(settings_tab)
        self._build_advanced_tab(advanced_tab)

    def _build_experiment_tab(self, parent):
        self._entry_row(parent, "Experiment name", self.exp_display_var, row=0)
        self._entry_row(parent, "Description", self.exp_description_var, row=1)

        ttk.Label(parent, text="Notes").grid(row=2, column=0, sticky="nw", pady=3)
        self.exp_notes_text = tk.Text(parent, height=3, wrap="word")
        self.exp_notes_text.grid(row=2, column=1, sticky="ew", pady=3)

        ttk.Button(parent, text="Save Experiment", command=self.save_experiment).grid(
            row=3, column=1, sticky="e", pady=8
        )

        parent.columnconfigure(1, weight=1)
        # Notes should stay compact, not expand vertically.
        parent.rowconfigure(2, weight=0)

    def _build_animal_tab(self, parent):
        self._entry_row(parent, "Animal ID", self.animal_id_var, row=0)

        ttk.Label(parent, text="Sex").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Combobox(
            parent,
            textvariable=self.sex_var,
            values=["M", "F", "U"],
            state="readonly",
            width=10,
        ).grid(row=1, column=1, sticky="w", pady=3)

        self._entry_row(parent, "Genotype", self.genotype_var, row=2)

        ttk.Label(parent, text="Notes").grid(row=3, column=0, sticky="nw", pady=3)
        self.animal_notes_text = tk.Text(parent, height=3, wrap="word")
        self.animal_notes_text.grid(row=3, column=1, sticky="ew", pady=3)

        ttk.Button(parent, text="Save Animal", command=self.save_animal).grid(
            row=4, column=1, sticky="e", pady=8
        )

        parent.columnconfigure(1, weight=1)
        # Notes should stay compact, not expand vertically.
        parent.rowconfigure(3, weight=0)

    def _build_settings_tab(self, parent):
        self._entry_row(parent, "Frame rate (Hz)", self.frame_rate_var, row=0)
        self._entry_row(parent, "Baseline length (sec)", self.baseline_len_var, row=1)
        self._entry_row(parent, "BMI length (sec)", self.bmi_len_var, row=2)
        self._entry_row(parent, "Ensemble count", self.ensemble_count_var, row=3)
        self._entry_row(parent, "Neurons per ensemble", self.neurons_per_ensemble_var, row=4)

        ttk.Label(parent, text="Sec per reward range").grid(row=5, column=0, sticky="w", pady=3)
        range_frame = ttk.Frame(parent)
        range_frame.grid(row=5, column=1, sticky="w", pady=3)
        ttk.Entry(range_frame, textvariable=self.reward_min_var, width=8).pack(side="left")
        ttk.Label(range_frame, text=" to ").pack(side="left")
        ttk.Entry(range_frame, textvariable=self.reward_max_var, width=8).pack(side="left")

        ttk.Checkbutton(parent, text="Feedback enabled", variable=self.feedback_enabled_var).grid(
            row=6, column=1, sticky="w", pady=3
        )
        self._entry_row(parent, "Arduino COM", self.arduino_com_var, row=7)
        self._entry_row(parent, "Arduino baudrate", self.arduino_baudrate_var, row=8)

        ttk.Button(parent, text="Overwrite Current Template", command=self.save_template_overwrite).grid(
            row=9, column=1, sticky="e", pady=8
        )
        ttk.Button(parent, text="Save As New Named Template", command=self.save_template_as_new).grid(
            row=9, column=0, sticky="w", pady=8
        )

        parent.columnconfigure(1, weight=1)

    def _build_advanced_tab(self, parent):
        ttk.Checkbutton(parent, text="Save data", variable=self.save_data_var).grid(
            row=0, column=1, sticky="w", pady=3
        )
        ttk.Checkbutton(parent, text="Load calibration", variable=self.load_calibration_var).grid(
            row=1, column=1, sticky="w", pady=3
        )

        self._entry_row(parent, "F0 window", self.f0_win_var, row=2)
        self._entry_row(parent, "Random stim IHSI mean", self.ihsi_mean_var, row=3)
        self._entry_row(parent, "Random stim IHSI range", self.ihsi_range_var, row=4)

        ttk.Label(parent, text="Slidebook default dir").grid(row=5, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=self.slidebook_dir_var).grid(
            row=5, column=1, sticky="ew", pady=3
        )
        ttk.Button(parent, text="Browse", command=self.browse_slidebook_dir).grid(
            row=5, column=2, padx=4
        )

        parent.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    # Layout helpers
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
            self.clear_project_dependent_fields()

    def refresh_experiments(self):
        user, project = self.user_var.get(), self.project_var.get()
        experiments = []
        if user and project:
            records = self.cm.list_experiments(user, project)
            experiments = [r["experiment_name"] for r in records]
        self.experiment_combo["values"] = experiments
        if experiments:
            if self.experiment_var.get() not in experiments:
                self.experiment_var.set(experiments[0])
            self.on_experiment_changed()
        else:
            self.experiment_var.set("")
            self.clear_experiment_fields()

    def refresh_animals(self):
        user, project = self.user_var.get(), self.project_var.get()
        animals = []
        if user and project:
            records = self.cm.list_animals(user, project)
            animals = [r["animal_id"] for r in records]
        self.animal_combo["values"] = animals
        if animals:
            if self.animal_var.get() not in animals:
                self.animal_var.set(animals[0])
            self.on_animal_changed()
        else:
            self.animal_var.set("")
            self.clear_animal_fields()

    def refresh_templates(self):
        user, project = self.user_var.get(), self.project_var.get()
        labels = []
        if user and project:
            rows = self.cm.list_all_templates(user, project)
            labels = [f"{r['scope']}:{r['name']}" for r in rows]
        self.template_combo["values"] = labels
        if labels:
            if self.template_var.get() not in labels:
                self.template_var.set(labels[0])
            self.on_template_changed()
        else:
            self.template_var.set("")
            self.load_settings_into_fields(copy.deepcopy(DEFAULT_TEMPLATE))

    def refresh_suggested_day(self):
        user = self.user_var.get()
        project = self.project_var.get()
        experiment = self.experiment_var.get()
        animal = self.animal_var.get()

        if user and project and experiment and animal:
            self.day_var.set(self.cm.suggest_next_day(user, project, animal, experiment))
            self.log(f"Suggested day updated: {self.day_var.get()}")

    # ------------------------------------------------------------------
    # Change handlers
    # ------------------------------------------------------------------

    def on_user_changed(self, event=None):
        self.log(f"Selected user: {self.user_var.get()}")
        self.refresh_projects()

    def on_project_changed(self, event=None):
        self.log(f"Selected project: {self.project_var.get()}")
        self.refresh_experiments()
        self.refresh_animals()
        self.refresh_templates()
        self.refresh_suggested_day()

    def on_experiment_changed(self, event=None):
        user, project, exp = self.user_var.get(), self.project_var.get(), self.experiment_var.get()
        if user and project and exp:
            record = self.cm.get_experiment(user, project, exp)
            if record:
                self.exp_display_var.set(record.get("display_name", exp))
                self.exp_description_var.set(record.get("description", ""))
                self.exp_notes_text.delete("1.0", "end")
                self.exp_notes_text.insert("1.0", record.get("notes", ""))
        self.refresh_suggested_day()

    def on_animal_changed(self, event=None):
        user, project, animal_id = self.user_var.get(), self.project_var.get(), self.animal_var.get()
        if user and project and animal_id:
            record = self.cm.get_animal(user, project, animal_id)
            if record:
                self.animal_id_var.set(record.get("animal_id", ""))
                self.sex_var.set(record.get("sex", "U"))
                self.genotype_var.set(record.get("genotype", ""))
                self.animal_notes_text.delete("1.0", "end")
                self.animal_notes_text.insert("1.0", record.get("notes", ""))
        self.refresh_suggested_day()

    def on_template_changed(self, event=None):
        label = self.template_var.get()
        if not label or ":" not in label:
            return
        scope, name = label.split(":", 1)
        user, project = self.user_var.get(), self.project_var.get()
        try:
            settings = self.cm.load_template(user, project, name, scope=scope)
        except Exception as e:
            messagebox.showerror("Template error", str(e))
            return

        self.current_settings = settings
        self.current_template_scope = scope
        self.current_template_name = name
        self.load_settings_into_fields(settings)
        self.log(f"Loaded template: {label}")

    # ------------------------------------------------------------------
    # Create / clone actions
    # ------------------------------------------------------------------

    def new_user(self):
        name = simpledialog.askstring("New User", "User name:")
        if not name:
            return
        self.cm.create_user(name)
        self.user_var.set(name.lower().replace(" ", "_"))
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
        self.project_var.set(name.lower().replace(" ", "_"))
        self.refresh_projects()
        self.log(f"Created project: {name}")

    def new_experiment(self):
        self.clear_experiment_fields()
        self.exp_display_var.set("")
        self.log("New experiment form ready. Fill fields and click Save Experiment.")

    def clone_experiment(self):
        user, project, exp = self.require_user_project_experiment()
        if not exp:
            return
        record = self.cm.get_experiment(user, project, exp)
        if not record:
            return

        self.exp_display_var.set(record.get("display_name", exp) + "_copy")
        self.exp_description_var.set(record.get("description", ""))
        self.exp_notes_text.delete("1.0", "end")
        self.exp_notes_text.insert("1.0", record.get("notes", ""))
        self.experiment_var.set("")
        self.log("Experiment cloned into editable fields. Change name and click Save Experiment.")

    def new_animal(self):
        self.clear_animal_fields()
        self.log("New animal form ready. Fill fields and click Save Animal.")

    def clone_animal(self):
        user, project, animal_id = self.require_user_project_animal()
        if not animal_id:
            return
        record = self.cm.get_animal(user, project, animal_id)
        if not record:
            return

        self.animal_id_var.set(record.get("animal_id", "") + "_copy")
        self.sex_var.set(record.get("sex", "U"))
        self.genotype_var.set(record.get("genotype", ""))
        self.animal_notes_text.delete("1.0", "end")
        self.animal_notes_text.insert("1.0", record.get("notes", ""))
        self.animal_var.set("")
        self.log("Animal cloned into editable fields. Change ID/fields and click Save Animal.")

    def new_template(self):
        self.current_settings = copy.deepcopy(DEFAULT_TEMPLATE)
        self.current_template_scope = "project"
        self.current_template_name = ""
        self.template_var.set("")
        self.load_settings_into_fields(self.current_settings)
        self.log("New template form ready. Edit fields and click Save As New Template.")

    def clone_template(self):
        if not self.template_var.get():
            messagebox.showwarning("No template", "Select a template first.")
            return
        self.current_template_name = ""
        self.template_var.set("")
        self.log("Template cloned into editable fields. Click Save As New Template.")

    # ------------------------------------------------------------------
    # Save actions
    # ------------------------------------------------------------------

    def save_experiment(self):
        user, project = self.require_user_project()
        if not project:
            return
        name = self.exp_display_var.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Experiment name cannot be empty.")
            return

        existing = self.cm.get_experiment(user, project, name)
        overwrite = existing is not None
        if overwrite:
            ok = messagebox.askyesno("Overwrite experiment?", f"Overwrite experiment '{name}'?")
            if not ok:
                return

        self.cm.save_experiment(
            user,
            project,
            experiment_name=name,
            description=self.exp_description_var.get(),
            notes=self.exp_notes_text.get("1.0", "end").strip(),
            overwrite=overwrite,
        )
        self.refresh_experiments()
        self.experiment_var.set(name.lower().replace(" ", "_"))
        self.refresh_experiments()
        self.log(f"Saved experiment: {name}")

    def save_animal(self):
        user, project = self.require_user_project()
        if not project:
            return

        animal_id = self.animal_id_var.get().strip()
        if not animal_id:
            messagebox.showerror("Missing animal ID", "Animal ID cannot be empty.")
            return

        existing = self.cm.get_animal(user, project, animal_id)
        overwrite = existing is not None
        if overwrite:
            ok = messagebox.askyesno("Overwrite animal?", f"Overwrite animal '{animal_id}'?")
            if not ok:
                return

        self.cm.save_animal(
            user,
            project,
            animal_id=animal_id,
            sex=self.sex_var.get(),
            genotype=self.genotype_var.get(),
            notes=self.animal_notes_text.get("1.0", "end").strip(),
            overwrite=overwrite,
        )
        self.refresh_animals()
        self.animal_var.set(animal_id)
        self.refresh_animals()
        self.log(f"Saved animal: {animal_id}")

    def save_template_overwrite(self):
        user, project = self.require_user_project()
        if not project:
            return

        if self.current_template_scope == "shared":
            messagebox.showinfo(
                "Shared template",
                "Shared templates are read-only. Use 'Save As New Template' instead.",
            )
            return

        label = self.template_var.get()
        if label and ":" in label:
            scope, name = label.split(":", 1)
        else:
            name = self.current_template_name

        if not name:
            self.save_template_as_new()
            return

        settings = self.collect_settings_from_fields()
        self.cm.save_project_template(user, project, name, settings, overwrite=True)
        self.refresh_templates()
        self.template_var.set(f"project:{name}")
        self.log(f"Saved template: {name}")

    def save_template_as_new(self):
        user, project = self.require_user_project()
        if not project:
            return

        name = simpledialog.askstring("Save Template As", "New template name:")
        if not name:
            return

        settings = self.collect_settings_from_fields()

        try:
            self.cm.save_project_template(user, project, name, settings, overwrite=False)
        except ValueError:
            ok = messagebox.askyesno("Overwrite template?", f"Template '{name}' exists. Overwrite?")
            if not ok:
                return
            self.cm.save_project_template(user, project, name, settings, overwrite=True)

        self.refresh_templates()
        self.template_var.set(f"project:{name.lower().replace(' ', '_')}")
        self.refresh_templates()
        self.log(f"Saved new template: {name}")

    def preview_session_config(self):
        try:
            config = self.build_current_session_config()
        except Exception as e:
            messagebox.showerror("Cannot build session config", str(e))
            return

        top = tk.Toplevel(self)
        top.title("Session Config Preview")
        top.geometry("800x600")

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
            answer = messagebox.askyesnocancel(
                "Session already exists",
                (
                    f"This session already exists:\n\n"
                    f"{session_id}\n\n"
                    "Yes = overwrite existing session_config.json\n"
                    "No = cancel so you can change the day/session label\n"
                    "Cancel = cancel"
                ),
            )
            if answer is True:
                overwrite = True
            else:
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
            answer = messagebox.askyesno(
                "File already exists",
                f"{e}\n\nOverwrite the existing file?"
            )
            if not answer:
                self.log("Save cancelled because file already exists.")
                return

            try:
                path = self.cm.save_session_config(
                    user_name=self.user_var.get(),
                    project_name=self.project_var.get(),
                    session_config=config,
                    save_base_dir=Path(self.save_base_dir_var.get()),
                    register=True,
                    overwrite=True,
                )
            except Exception as e2:
                messagebox.showerror("Save failed", str(e2))
                return

        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return

        if overwrite:
            messagebox.showinfo("Session overwritten", f"Overwrote session config:\n{path}")
            self.log(f"Overwrote session config: {path}")
        else:
            messagebox.showinfo("Session saved", f"Saved session config:\n{path}")
            self.log(f"Saved session config: {path}")

        self.refresh_suggested_day()

    # ------------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------------

    def load_settings_into_fields(self, settings):
        self.current_settings = copy.deepcopy(settings)

        task = settings.get("task", {})
        feedback = settings.get("feedback", {})
        advanced = settings.get("advanced", {})
        paths = settings.get("paths", {})

        self.frame_rate_var.set(str(task.get("frame_rate_hz", "")))
        self.baseline_len_var.set(str(task.get("baseline_len_sec", "")))
        self.bmi_len_var.set(str(task.get("bmi_len_sec", "")))
        self.ensemble_count_var.set(str(task.get("ensemble_count", "")))
        self.neurons_per_ensemble_var.set(str(task.get("neurons_per_ensemble", "")))

        reward_range = task.get("sec_per_reward_range", ["", ""])
        self.reward_min_var.set(str(reward_range[0]) if len(reward_range) > 0 else "")
        self.reward_max_var.set(str(reward_range[1]) if len(reward_range) > 1 else "")

        self.feedback_enabled_var.set(bool(feedback.get("enabled", False)))
        self.arduino_com_var.set(str(feedback.get("arduino_com", "")))
        self.arduino_baudrate_var.set(str(feedback.get("arduino_baudrate", "")))

        self.save_data_var.set(bool(advanced.get("save", True)))
        self.load_calibration_var.set(bool(advanced.get("load_calibration", False)))
        self.f0_win_var.set(str(advanced.get("f0_win", "")))
        self.ihsi_mean_var.set(str(advanced.get("random_stim_ihsi_mean", "")))
        self.ihsi_range_var.set(str(advanced.get("random_stim_ihsi_range", "")))

        self.slidebook_dir_var.set(str(paths.get("default_slidebook_dir", "")))

    def collect_settings_from_fields(self):
        settings = copy.deepcopy(self.current_settings)

        settings.setdefault("task", {})
        settings.setdefault("feedback", {})
        settings.setdefault("advanced", {})
        settings.setdefault("paths", {})

        settings["task"]["frame_rate_hz"] = self._float_or_int(self.frame_rate_var.get())
        settings["task"]["baseline_len_sec"] = self._float_or_int(self.baseline_len_var.get())
        settings["task"]["bmi_len_sec"] = self._float_or_int(self.bmi_len_var.get())
        settings["task"]["ensemble_count"] = self._int(self.ensemble_count_var.get())
        settings["task"]["neurons_per_ensemble"] = self._int(self.neurons_per_ensemble_var.get())
        settings["task"]["sec_per_reward_range"] = [
            self._float_or_int(self.reward_min_var.get()),
            self._float_or_int(self.reward_max_var.get()),
        ]

        settings["feedback"]["enabled"] = bool(self.feedback_enabled_var.get())
        settings["feedback"]["arduino_com"] = self.arduino_com_var.get()
        settings["feedback"]["arduino_baudrate"] = self._int(self.arduino_baudrate_var.get())

        settings["advanced"]["save"] = bool(self.save_data_var.get())
        settings["advanced"]["load_calibration"] = bool(self.load_calibration_var.get())
        settings["advanced"]["f0_win"] = self._float_or_int(self.f0_win_var.get())
        settings["advanced"]["random_stim_ihsi_mean"] = self._float_or_int(self.ihsi_mean_var.get())
        settings["advanced"]["random_stim_ihsi_range"] = self._float_or_int(self.ihsi_range_var.get())

        settings["paths"]["default_save_base_dir"] = self.save_base_dir_var.get()
        settings["paths"]["default_slidebook_dir"] = self.slidebook_dir_var.get()

        return settings

    def build_current_session_config(self):
        user = self.user_var.get()
        project = self.project_var.get()
        experiment = self.experiment_var.get()
        animal = self.animal_var.get()

        if not user:
            raise ValueError("Select a user.")
        if not project:
            raise ValueError("Select a project.")
        if not experiment:
            raise ValueError("Select an experiment.")
        if not animal:
            raise ValueError("Select an animal.")

        settings = self.collect_settings_from_fields()

        label = self.template_var.get()
        if label and ":" in label:
            scope, name = label.split(":", 1)
        else:
            scope, name = self.current_template_scope, self.current_template_name

        return self.cm.build_session_config(
            user_name=user,
            project_name=project,
            experiment_name=experiment,
            animal_id=animal,
            settings=settings,
            settings_template=name,
            settings_scope=scope,
            session_date=self.date_var.get(),
            day=self.day_var.get() or None,
            extra={
                "session_notes": self.session_notes_text.get("1.0", "end").strip()
                if hasattr(self, "session_notes_text") else ""
            },
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def browse_save_base_dir(self):
        path = filedialog.askdirectory(title="Select save base directory")
        if path:
            self.save_base_dir_var.set(path)

    def browse_slidebook_dir(self):
        path = filedialog.askdirectory(title="Select Slidebook directory")
        if path:
            self.slidebook_dir_var.set(path)

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

    def require_user_project_experiment(self):
        user, project = self.require_user_project()
        exp = self.experiment_var.get()
        if user and project and not exp:
            messagebox.showwarning("Missing experiment", "Select an experiment first.")
            return user, project, None
        return user, project, exp

    def require_user_project_animal(self):
        user, project = self.require_user_project()
        animal = self.animal_var.get()
        if user and project and not animal:
            messagebox.showwarning("Missing animal", "Select an animal first.")
            return user, project, None
        return user, project, animal

    def clear_project_dependent_fields(self):
        self.clear_experiment_fields()
        self.clear_animal_fields()
        self.load_settings_into_fields(copy.deepcopy(DEFAULT_TEMPLATE))

    def clear_experiment_fields(self):
        self.exp_display_var.set("")
        self.exp_description_var.set("")
        if hasattr(self, "exp_notes_text"):
            self.exp_notes_text.delete("1.0", "end")

    def clear_animal_fields(self):
        self.animal_id_var.set("")
        self.sex_var.set("U")
        self.genotype_var.set("")
        if hasattr(self, "animal_notes_text"):
            self.animal_notes_text.delete("1.0", "end")

    def log(self, msg):
        if hasattr(self, "status_text"):
            self.status_text.insert("end", f"{msg}\n")
            self.status_text.see("end")

    @staticmethod
    def _int(value):
        value = str(value).strip()
        if value == "":
            return 0
        return int(float(value))

    @staticmethod
    def _float_or_int(value):
        value = str(value).strip()
        if value == "":
            return 0
        x = float(value)
        if x.is_integer():
            return int(x)
        return x


if __name__ == "__main__":
    app = CaBMIConfigGUI()
    app.mainloop()
