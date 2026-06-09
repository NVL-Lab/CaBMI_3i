
"""
config_manager.py

Local configuration manager for the CaBMI GUI.

This module does not depend on Tkinter or PyNWB.
It only manages the local folder hierarchy and JSON files used by the GUI.

Current hierarchy:

CaBMI_GUI_Config/
├── shared_templates/
│   └── default_cabmi.json
└── users/
    └── <user_name>/
        ├── user_settings.json
        └── projects/
            └── <project_name>/
                ├── project_info.json
                ├── animals.json
                ├── experiments.json
                ├── sessions.json
                └── templates/
                    └── <template_name>.json

Concepts:

User:
    Person using the GUI.

Project:
    A broader research project. Animals belong to projects.

Experiment:
    A type of session/task within a project.
    Example: "CaBMI", "baseline_only", "photopharm_d1r".

Animal:
    Animal record inside a project.

Template:
    Reusable parameter set. Shared templates are lab defaults.
    Project templates are editable copies inside a project.

Session:
    Exact run on one date/day using one animal, experiment, and template.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


DEFAULT_TEMPLATE: dict[str, Any] = {
    "template_name": "default_cabmi",
    "description": "Default CaBMI session settings.",
    "task": {
        "frame_rate_hz": 30,
        "baseline_len_sec": 300,
        "bmi_len_sec": 1800,
        "ensemble_count": 2,
        "neurons_per_ensemble": 3,
        "sec_per_reward_range": [20, 60],
    },
    "feedback": {
        "enabled": True,
        "arduino_com": "COM3",
        "arduino_baudrate": 9600,
    },
    "advanced": {
        "save": True,
        "load_calibration": False,
        "f0_win": 30,
        "random_stim_ihsi_mean": 10,
        "random_stim_ihsi_range": 3,
    },
    "paths": {
        "default_save_base_dir": "",
        "default_slidebook_dir": "",
    },
}


DEFAULT_USER_SETTINGS: dict[str, Any] = {
    "display_name": "",
    "notes": "",
}


VALID_SEX_VALUES = {"M", "F", "U"}


def _slug(name: str) -> str:
    """
    Convert a display name into a safe folder/file name.

    Examples:
        "Motor Learning Project" -> "motor_learning_project"
        "Nuria V-L" -> "nuria_v_l"
    """
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        raise ValueError("Name cannot be empty.")
    return name


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return copy.deepcopy(default)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _json_path_from_name(folder: Path, name: str) -> Path:
    return folder / f"{_slug(name)}.json"


@dataclass
class ConfigManager:
    """
    Manager for local CaBMI GUI configuration files.

    Parameters
    ----------
    root:
        Base folder where all GUI config files will live.
        Example: Path.home() / "CaBMI_GUI_Config"
    """

    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root).expanduser().resolve()
        self.shared_templates_dir.mkdir(parents=True, exist_ok=True)
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self.ensure_default_shared_template()

    # ------------------------------------------------------------------
    # Root folders
    # ------------------------------------------------------------------

    @property
    def shared_templates_dir(self) -> Path:
        return self.root / "shared_templates"

    @property
    def users_dir(self) -> Path:
        return self.root / "users"

    def ensure_default_shared_template(self) -> Path:
        """Create the shared default CaBMI template if it does not exist."""
        path = self.shared_templates_dir / "default_cabmi.json"
        if not path.exists():
            _write_json(path, DEFAULT_TEMPLATE)
        return path

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def list_users(self) -> list[str]:
        return sorted([p.name for p in self.users_dir.iterdir() if p.is_dir()])

    def user_dir(self, user_name: str) -> Path:
        return self.users_dir / _slug(user_name)

    def create_user(self, user_name: str) -> Path:
        """
        Create a new user folder.

        Project-specific templates will be copied from shared templates when
        a new project is created.
        """
        user_slug = _slug(user_name)
        udir = self.users_dir / user_slug
        udir.mkdir(parents=True, exist_ok=True)

        settings_path = udir / "user_settings.json"
        if not settings_path.exists():
            settings = copy.deepcopy(DEFAULT_USER_SETTINGS)
            settings["display_name"] = user_name
            _write_json(settings_path, settings)

        (udir / "projects").mkdir(exist_ok=True)
        return udir

    def delete_user(self, user_name: str) -> None:
        shutil.rmtree(self.user_dir(user_name))

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def projects_dir(self, user_name: str) -> Path:
        return self.user_dir(user_name) / "projects"

    def project_dir(self, user_name: str, project_name: str) -> Path:
        return self.projects_dir(user_name) / _slug(project_name)

    def list_projects(self, user_name: str) -> list[str]:
        pdir = self.projects_dir(user_name)
        if not pdir.exists():
            return []
        return sorted([p.name for p in pdir.iterdir() if p.is_dir()])

    def create_project(
        self,
        user_name: str,
        project_name: str,
        description: str = "",
        notes: str = "",
        copy_default_template: bool = True,
    ) -> Path:
        """
        Create a project under a user.

        Animals, experiments, templates, and sessions are project-specific.
        """
        if not self.user_dir(user_name).exists():
            self.create_user(user_name)

        project_slug = _slug(project_name)
        pdir = self.project_dir(user_name, project_name)
        pdir.mkdir(parents=True, exist_ok=True)

        project_info_path = pdir / "project_info.json"
        if not project_info_path.exists():
            project_info = {
                "project_name": project_slug,
                "display_name": project_name,
                "description": description,
                "notes": notes,
                "created": datetime.now().isoformat(timespec="seconds"),
            }
            _write_json(project_info_path, project_info)

        if not (pdir / "animals.json").exists():
            _write_json(pdir / "animals.json", [])
        if not (pdir / "experiments.json").exists():
            _write_json(pdir / "experiments.json", [])
        if not (pdir / "sessions.json").exists():
            _write_json(pdir / "sessions.json", [])

        templates_dir = pdir / "templates"
        templates_dir.mkdir(exist_ok=True)

        if copy_default_template:
            src = self.shared_templates_dir / "default_cabmi.json"
            dst = templates_dir / "default_cabmi.json"
            if not dst.exists():
                shutil.copy2(src, dst)

        return pdir

    # Backward-compatible aliases for earlier draft code.
    # These can be removed later.
    def experiments_dir(self, user_name: str) -> Path:
        return self.projects_dir(user_name)

    def experiment_dir(self, user_name: str, experiment_name: str) -> Path:
        return self.project_dir(user_name, experiment_name)

    def list_experiments_old_projects(self, user_name: str) -> list[str]:
        return self.list_projects(user_name)

    def create_experiment_old_project(
        self,
        user_name: str,
        experiment_name: str,
        description: str = "",
        notes: str = "",
    ) -> Path:
        return self.create_project(user_name, experiment_name, description, notes)

    # ------------------------------------------------------------------
    # Experiment records inside a project
    # ------------------------------------------------------------------

    def experiments_path(self, user_name: str, project_name: str) -> Path:
        return self.project_dir(user_name, project_name) / "experiments.json"

    def list_experiments(self, user_name: str, project_name: str) -> list[dict[str, Any]]:
        """
        List experiment types inside a project.

        Example experiment records:
            {"experiment_name": "cabmi", "display_name": "CaBMI", "notes": ""}
        """
        return _read_json(self.experiments_path(user_name, project_name), [])

    def get_experiment(
        self, user_name: str, project_name: str, experiment_name: str
    ) -> dict[str, Any] | None:
        exp_slug = _slug(experiment_name)
        for experiment in self.list_experiments(user_name, project_name):
            if experiment.get("experiment_name") == exp_slug:
                return experiment
        return None

    def save_experiment(
        self,
        user_name: str,
        project_name: str,
        experiment_name: str,
        notes: str = "",
        description: str = "",
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """
        Create or update an experiment type inside a project.
        """
        exp_slug = _slug(experiment_name)
        path = self.experiments_path(user_name, project_name)
        experiments = _read_json(path, [])

        new_record = {
            "experiment_name": exp_slug,
            "display_name": experiment_name,
            "description": description,
            "notes": notes,
        }

        for i, experiment in enumerate(experiments):
            if experiment.get("experiment_name") == exp_slug:
                if not overwrite:
                    raise ValueError(
                        f"Experiment '{experiment_name}' already exists. "
                        "Use overwrite=True to edit it."
                    )
                experiments[i] = new_record
                _write_json(path, experiments)
                return new_record

        experiments.append(new_record)
        experiments = sorted(experiments, key=lambda x: x.get("experiment_name", ""))
        _write_json(path, experiments)
        return new_record

    def clone_experiment(
        self,
        user_name: str,
        project_name: str,
        source_experiment_name: str,
        new_experiment_name: str,
        notes: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Clone an experiment record.

        In the GUI this should be used to pre-fill editable boxes.
        """
        source = self.get_experiment(user_name, project_name, source_experiment_name)
        if source is None:
            raise ValueError(f"Source experiment '{source_experiment_name}' not found.")

        clone = copy.deepcopy(source)
        clone["experiment_name"] = _slug(new_experiment_name)
        clone["display_name"] = new_experiment_name
        if notes is not None:
            clone["notes"] = notes
        if description is not None:
            clone["description"] = description

        return self.save_experiment(
            user_name=user_name,
            project_name=project_name,
            experiment_name=clone["display_name"],
            notes=clone.get("notes", ""),
            description=clone.get("description", ""),
            overwrite=False,
        )

    # ------------------------------------------------------------------
    # Animals inside a project
    # ------------------------------------------------------------------

    def animals_path(self, user_name: str, project_name: str) -> Path:
        return self.project_dir(user_name, project_name) / "animals.json"

    def list_animals(self, user_name: str, project_name: str) -> list[dict[str, Any]]:
        return _read_json(self.animals_path(user_name, project_name), [])

    def get_animal(
        self, user_name: str, project_name: str, animal_id: str
    ) -> dict[str, Any] | None:
        for animal in self.list_animals(user_name, project_name):
            if animal.get("animal_id") == animal_id:
                return animal
        return None

    def save_animal(
        self,
        user_name: str,
        project_name: str,
        animal_id: str,
        sex: str = "U",
        genotype: str = "",
        notes: str = "",
        extra: dict[str, Any] | None = None,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """
        Create or update an animal inside a project.

        Animal fields are intentionally simple for the first GUI version:
        animal_id, sex, genotype, notes.

        extra can store additional future fields without changing the schema.
        """
        animal_id = animal_id.strip()
        if not animal_id:
            raise ValueError("animal_id cannot be empty.")

        sex = sex.strip().upper() if sex else "U"
        if sex not in VALID_SEX_VALUES:
            raise ValueError(f"sex must be one of {sorted(VALID_SEX_VALUES)}.")

        path = self.animals_path(user_name, project_name)
        animals = _read_json(path, [])

        new_record = {
            "animal_id": animal_id,
            "sex": sex,
            "genotype": genotype,
            "notes": notes,
        }

        if extra:
            new_record.update(extra)

        for i, animal in enumerate(animals):
            if animal.get("animal_id") == animal_id:
                if not overwrite:
                    raise ValueError(
                        f"Animal '{animal_id}' already exists. Use overwrite=True to edit it."
                    )
                animals[i] = new_record
                _write_json(path, animals)
                return new_record

        animals.append(new_record)
        animals = sorted(animals, key=lambda x: x.get("animal_id", ""))
        _write_json(path, animals)
        return new_record

    def clone_animal(
        self,
        user_name: str,
        project_name: str,
        source_animal_id: str,
        new_animal_id: str,
        sex: str | None = None,
        genotype: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """
        Clone an animal.

        In the GUI this should usually only pre-fill editable boxes.
        This function also saves the clone for command-line testing.
        """
        source = self.get_animal(user_name, project_name, source_animal_id)
        if source is None:
            raise ValueError(f"Source animal '{source_animal_id}' not found.")

        clone = copy.deepcopy(source)
        clone["animal_id"] = new_animal_id
        if sex is not None:
            clone["sex"] = sex
        if genotype is not None:
            clone["genotype"] = genotype
        if notes is not None:
            clone["notes"] = notes

        return self.save_animal(
            user_name=user_name,
            project_name=project_name,
            animal_id=clone["animal_id"],
            sex=clone.get("sex", "U"),
            genotype=clone.get("genotype", ""),
            notes=clone.get("notes", ""),
            extra={k: v for k, v in clone.items() if k not in {"animal_id", "sex", "genotype", "notes"}},
            overwrite=False,
        )

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    def project_templates_dir(self, user_name: str, project_name: str) -> Path:
        return self.project_dir(user_name, project_name) / "templates"

    # Older name kept as alias for now.
    def user_templates_dir(self, user_name: str) -> Path:
        return self.user_dir(user_name) / "templates"

    def list_shared_templates(self) -> list[str]:
        return sorted([p.stem for p in self.shared_templates_dir.glob("*.json")])

    def list_project_templates(self, user_name: str, project_name: str) -> list[str]:
        tdir = self.project_templates_dir(user_name, project_name)
        if not tdir.exists():
            return []
        return sorted([p.stem for p in tdir.glob("*.json")])

    def list_all_templates(self, user_name: str, project_name: str) -> list[dict[str, str]]:
        """
        Return shared + project templates for a GUI dropdown.

        Example:
            [{"scope": "shared", "name": "default_cabmi"},
             {"scope": "project", "name": "photopharm_test"}]
        """
        rows: list[dict[str, str]] = []
        for name in self.list_shared_templates():
            rows.append({"scope": "shared", "name": name})
        for name in self.list_project_templates(user_name, project_name):
            rows.append({"scope": "project", "name": name})
        return rows

    def template_path(
        self,
        user_name: str,
        project_name: str,
        template_name: str,
        scope: str = "project",
    ) -> Path:
        if scope == "shared":
            return _json_path_from_name(self.shared_templates_dir, template_name)
        if scope == "project":
            return _json_path_from_name(self.project_templates_dir(user_name, project_name), template_name)
        raise ValueError("scope must be 'shared' or 'project'.")

    def load_template(
        self,
        user_name: str,
        project_name: str,
        template_name: str,
        scope: str = "project",
    ) -> dict[str, Any]:
        path = self.template_path(user_name, project_name, template_name, scope)
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")
        return _read_json(path, {})

    def save_project_template(
        self,
        user_name: str,
        project_name: str,
        template_name: str,
        data: dict[str, Any],
        overwrite: bool = False,
    ) -> Path:
        """
        Save a project's editable template.

        Shared templates are intentionally not modified here.
        """
        path = self.template_path(user_name, project_name, template_name, scope="project")
        if path.exists() and not overwrite:
            raise ValueError(
                f"Template '{template_name}' already exists in project '{project_name}'. "
                "Use overwrite=True to edit it."
            )

        data = copy.deepcopy(data)
        data["template_name"] = _slug(template_name)
        _write_json(path, data)
        return path

    def clone_template_to_project(
        self,
        user_name: str,
        project_name: str,
        source_template_name: str,
        new_template_name: str,
        source_scope: str = "shared",
    ) -> Path:
        """
        Clone a shared or project template into the project template folder.
        """
        data = self.load_template(
            user_name=user_name,
            project_name=project_name,
            template_name=source_template_name,
            scope=source_scope,
        )
        data = copy.deepcopy(data)
        data["cloned_from"] = {
            "scope": source_scope,
            "template_name": source_template_name,
        }
        return self.save_project_template(
            user_name=user_name,
            project_name=project_name,
            template_name=new_template_name,
            data=data,
            overwrite=False,
        )

    def import_template_file(
        self,
        user_name: str,
        project_name: str,
        source_json_path: Path,
        new_template_name: str | None = None,
        overwrite: bool = False,
    ) -> Path:
        """
        Import a template JSON file into a project's template folder.

        This supports simple sharing:
        one person can copy a .json file, and another can import it.
        """
        source_json_path = Path(source_json_path)
        data = _read_json(source_json_path, {})
        name = new_template_name or source_json_path.stem
        return self.save_project_template(
            user_name=user_name,
            project_name=project_name,
            template_name=name,
            data=data,
            overwrite=overwrite,
        )

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def sessions_path(self, user_name: str, project_name: str) -> Path:
        return self.project_dir(user_name, project_name) / "sessions.json"

    def list_sessions(self, user_name: str, project_name: str) -> list[dict[str, Any]]:
        return _read_json(self.sessions_path(user_name, project_name), [])

    def suggest_next_day(
        self,
        user_name: str,
        project_name: str,
        animal_id: str,
        experiment_name: str | None = None,
    ) -> str:
        """
        Suggest the next day label for an animal within one project.

        If experiment_name is provided, only previous sessions for that
        experiment type are counted.

        It looks at previous session records like "day_1", "day_2", ...
        and returns the next number.

        If previous labels are nonstandard, they are ignored.
        """
        sessions = self.list_sessions(user_name, project_name)
        max_day = 0
        exp_slug = _slug(experiment_name) if experiment_name else None

        for session in sessions:
            if session.get("animal_id") != animal_id:
                continue
            if exp_slug and session.get("experiment") != exp_slug:
                continue

            day_label = str(session.get("day", ""))
            match = re.fullmatch(r"day_(\d+)", day_label)
            if match:
                max_day = max(max_day, int(match.group(1)))

        return f"day_{max_day + 1}"

    def build_session_config(
        self,
        user_name: str,
        project_name: str,
        experiment_name: str,
        animal_id: str,
        settings: dict[str, Any],
        settings_template: str = "",
        settings_scope: str = "",
        session_date: str | None = None,
        day: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build the exact session config that should be saved next to the data.

        This does not modify templates.
        """
        animal = self.get_animal(user_name, project_name, animal_id)
        if animal is None:
            raise ValueError(f"Animal '{animal_id}' not found.")

        experiment = self.get_experiment(user_name, project_name, experiment_name)
        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found.")

        session_date = session_date or date.today().strftime("%Y_%m_%d")
        day = day or self.suggest_next_day(
            user_name=user_name,
            project_name=project_name,
            animal_id=animal_id,
            experiment_name=experiment_name,
        )

        experiment_slug = _slug(experiment_name)
        project_slug = _slug(project_name)
        user_slug = _slug(user_name)

        session_id = f"{animal_id}_{experiment_slug}_{session_date}_{day}"

        config = {
            "session_id": session_id,
            "created": datetime.now().isoformat(timespec="seconds"),
            "user": user_slug,
            "project": project_slug,
            "experiment": experiment_slug,
            "experiment_info": copy.deepcopy(experiment),
            "animal": copy.deepcopy(animal),
            "animal_id": animal_id,
            "date": session_date,
            "day": day,
            "settings_template": settings_template,
            "settings_scope": settings_scope,
            "settings_used": copy.deepcopy(settings),
        }

        if extra:
            config["extra"] = extra

        return config

    def session_exists(
        self,
        user_name: str,
        project_name: str,
        session_id: str,
    ) -> bool:
        """
        Return True if a session_id already exists in sessions.json.
        """
        sessions = self.list_sessions(user_name, project_name)
        return any(session.get("session_id") == session_id for session in sessions)

    def register_session(
        self,
        user_name: str,
        project_name: str,
        session_config: dict[str, Any],
        overwrite: bool = False,
    ) -> None:
        """
        Add a session to sessions.json.

        This is the lightweight record used for automatic day suggestion.
        """
        path = self.sessions_path(user_name, project_name)
        sessions = _read_json(path, [])

        session_id = session_config["session_id"]

        for i, session in enumerate(sessions):
            if session.get("session_id") == session_id:
                if not overwrite:
                    raise ValueError(
                        f"Session '{session_id}' already exists. Use overwrite=True."
                    )
                sessions[i] = self._session_log_entry(session_config)
                _write_json(path, sessions)
                return

        sessions.append(self._session_log_entry(session_config))
        _write_json(path, sessions)

    def save_session_config(
        self,
        user_name: str,
        project_name: str,
        session_config: dict[str, Any],
        save_base_dir: Path,
        register: bool = True,
        overwrite: bool = False,
    ) -> Path:
        """
        Save the exact session config next to the future data.

        Path:
            save_base_dir / project / animal_id / experiment / date / day / session_config.json
        """
        save_base_dir = Path(save_base_dir).expanduser().resolve()

        project = session_config["project"]
        animal_id = session_config["animal_id"]
        experiment = session_config["experiment"]
        session_date = session_config["date"]
        day = session_config["day"]

        session_id = session_config["session_id"]
        session_dir = save_base_dir / project / animal_id / experiment / session_date / day
        path = session_dir / "session_config.json"

        if register and self.session_exists(user_name, project_name, session_id) and not overwrite:
            raise ValueError(
                f"Session '{session_id}' already exists. Use overwrite=True to overwrite it."
            )

        if path.exists() and not overwrite:
            raise FileExistsError(
                f"Session config file already exists: {path}. Use overwrite=True to overwrite it."
            )

        session_dir.mkdir(parents=True, exist_ok=True)
        _write_json(path, session_config)

        if register:
            self.register_session(user_name, project_name, session_config, overwrite=overwrite)

        return path

    @staticmethod
    def _session_log_entry(session_config: dict[str, Any]) -> dict[str, Any]:
        return {
            "session_id": session_config["session_id"],
            "created": session_config.get("created", ""),
            "project": session_config["project"],
            "experiment": session_config["experiment"],
            "animal_id": session_config["animal_id"],
            "date": session_config["date"],
            "day": session_config["day"],
            "settings_template": session_config.get("settings_template", ""),
            "settings_scope": session_config.get("settings_scope", ""),
        }


if __name__ == "__main__":
    # Minimal smoke test.
    cm = ConfigManager(Path.home() / "CaBMI_GUI_Config_Test")

    cm.create_user("Nuria")
    cm.create_project("Nuria", "Motor Learning Project", description="Closed-loop learning project")

    cm.save_experiment(
        "Nuria",
        "Motor Learning Project",
        experiment_name="CaBMI",
        description="Closed-loop CaBMI task",
        overwrite=True,
    )

    cm.save_animal(
        "Nuria",
        "Motor Learning Project",
        animal_id="NVL001",
        sex="F",
        genotype="GCaMP6s",
        notes="Left M1 window",
        overwrite=True,
    )

    settings = cm.load_template(
        user_name="Nuria",
        project_name="Motor Learning Project",
        template_name="default_cabmi",
        scope="project",
    )

    print("Users:", cm.list_users())
    print("Projects:", cm.list_projects("Nuria"))
    print("Experiments:", cm.list_experiments("Nuria", "Motor Learning Project"))
    print("Animals:", cm.list_animals("Nuria", "Motor Learning Project"))
    print("Templates:", cm.list_all_templates("Nuria", "Motor Learning Project"))
    print(
        "Next suggested day:",
        cm.suggest_next_day("Nuria", "Motor Learning Project", "NVL001", "CaBMI"),
    )

    session_config = cm.build_session_config(
        user_name="Nuria",
        project_name="Motor Learning Project",
        experiment_name="CaBMI",
        animal_id="NVL001",
        settings=settings,
        settings_template="default_cabmi",
        settings_scope="project",
    )

    path = cm.save_session_config(
        "Nuria",
        "Motor Learning Project",
        session_config,
        save_base_dir=Path.home() / "CaBMI_GUI_Data_Test",
    )

    print(f"Saved session config to: {path}")
    print(
        "Next suggested day after saving:",
        cm.suggest_next_day("Nuria", "Motor Learning Project", "NVL001", "CaBMI"),
    )
