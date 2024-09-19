def get_flags() -> dict:
    return {
        'BMI_stim': {
            'flagBMI': True,
            'flagDRstim': True,
            'flagStimRandom': False,
            'flagWater': False
        },
        'RandomDRstim': {
            'flagBMI': True,
            'flagDRstim': False,
            'flagStimRandom': True,
            'flagWater': False
        },
        'no_stim': {
            'flagBMI': True,
            'flagDRstim': False,
            'flagStimRandom': False,
            'flagWater': False
        },
        'BMI_no_stim_water': {
            'flagBMI': True,
            'flagDRstim': False,
            'flagStimRandom': False,
            'flagWater': True
        },
        'BMI_stim_water': {
            'flagBMI': True,
            'flagDRstim': True,
            'flagStimRandom': False,
            'flagWater': True
        },
        'BMI_random_stim_water': {
            'flagBMI': True,
            'flagDRstim': False,
            'flagStimRandom': True,
            'flagWater': True
        }
}
