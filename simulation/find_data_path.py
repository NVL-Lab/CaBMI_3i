def find_data_path(folder_list, component):
    """
    Function that creates the correct folder_path after obtaining which
    location in the computer each hard-drive has (given by folder_list).
    """

    # Hardcoded structure given the location of the data in the same HD
    folder_paths = {
        'FA': ['m13', 'm15', 'm16', 'm18', 'm25'],
        'FB': ['m21', 'm22', 'm26'],
        'FC': ['m23', 'm27', 'm28', 'm29']
    }

    # Find the corresponding key in folder_list
    matching_key = ''
    for key in folder_list:
        data_list = folder_paths.get(key, [])
        if component in data_list:
            matching_key = key
            break

    # Check if a matching key was found
    if not matching_key:
        print('No matching key found in folder_list.')
        return ''

    # Return the full data path using folder_list value and matching component
    return folder_list[matching_key]