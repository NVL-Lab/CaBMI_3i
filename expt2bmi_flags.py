def get_flags() -> dict:
    return {
        'bmi_stim': {
            'bmi_stim': True,
            'dr_stim': True,
            'stim_random': False,
            'water': False
        },
        'Random_dr_stim': {
            'bmi_stim': True,
            'dr_stim': False,
            'stim_random': True,
            'water': False
        },
        'no_stim': {
            'bmi_stim': True,
            'dr_stim': False,
            'stim_random': False,
            'water': False
        },
        'bmi_no_stim_water': {
            'bmi_stim': True,
            'dr_stim': False,
            'stim_random': False,
            'water': True
        },
        'bmi_stim_water': {
            'bmi_stim': True,
            'dr_stim': True,
            'stim_random': False,
            'water': True
        },
        'bmi_random_stim_water': {
            'bmi_stim': True,
            'dr_stim': False,
            'stim_random': True,
            'water': True
        }
}
