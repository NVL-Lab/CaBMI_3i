import matplotlib.pyplot as plt

"""
    Implementation from MATLAB is different
"""

def catch_mouse_drag(h_obj, f_drag_start=None, f_drag_motion=None, f_drop=None, selection_type='normal'):
    if f_drag_start is None:
        f_drag_start = lambda *args: None
    if f_drag_motion is None:
        f_drag_motion = lambda *args: None
    if f_drop is None:
        f_drop = lambda *args: None

    init_button_down_func = h_obj.figure.canvas.mpl_connect(
        'button_press_event',
        lambda event: obj_button_down_func(event, h_obj, f_drag_start, f_drag_motion, f_drop, selection_type)
    )

    # Note: No `uiwait`/`uiresume` direct equivalent in matplotlib — interactive blocking will differ.

def obj_button_down_func(event, h_obj, f_drag_start, f_drag_motion, f_drop, selection_type):
    if event.button != 1:  # Left click
        return

    fig = event.canvas.figure
    ax = event.inaxes
    mouse_trace = [[event.xdata, event.ydata]]
    custom_data = f_drag_start(h_obj, ax, mouse_trace)

    def on_motion(event_motion):
        if event_motion.inaxes != ax:
            return
        mouse_trace.append([event_motion.xdata, event_motion.ydata])
        f_drag_motion(h_obj, ax, mouse_trace, custom_data)

    def on_release(event_release):
        fig.canvas.mpl_disconnect(cid_motion)
        fig.canvas.mpl_disconnect(cid_release)
        f_drop(h_obj, ax, mouse_trace, custom_data)

    cid_motion = fig.canvas.mpl_connect('motion_notify_event', on_motion)
    cid_release = fig.canvas.mpl_connect('button_release_event', on_release)