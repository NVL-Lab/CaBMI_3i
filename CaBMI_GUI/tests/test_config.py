from pathlib import Path
from CaBMI_GUI.config_manager import ConfigManager

cm = ConfigManager(Path("C:/Users/Nuria/Documents/Data/gui_tests/CaBMI_GUI_Config_Test"))

CONFIG_ROOT = Path(r"C:/Users/Nuria/Documents/Data/gui_tests/config")
DATA_ROOT = Path(r"C:/Users/Nuria/Documents/Data/gui_tests/config_data")

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
