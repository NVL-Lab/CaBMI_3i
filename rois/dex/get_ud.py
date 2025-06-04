def get_ud(handle, paramname=None):
    u = handle.get_user_data()
    if paramname is None:
        return u
    else:
        return u[paramname]