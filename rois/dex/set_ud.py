def set_ud(handle, paramname, value):
    u = getattr(handle, 'userdata', {})
    u[paramname] = value
    setattr(handle, 'userdata', u)