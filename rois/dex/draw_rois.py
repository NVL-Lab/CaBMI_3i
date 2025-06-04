import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from catch_mouse_drag import catch_mouse_drag
from setup_patch_behavior2 import setup_patch_behavior2

"""
    This is an interpretation of drawROIs2.m
    f_refresh_roi_traces seems like an event function
"""

def draw_rois(f_refresh_roi_traces):
    ax = plt.gca()
    hIm = [obj for obj in ax.get_children() if isinstance(obj, plt.AxesImage)]

    catch_mouse_drag(hIm[0], drag_start_fun, cursor_motion_fun, drop_fun)

def drag_start_fun(hIm, hAx, current_point):
    hP = Polygon([], closed=False, edgecolor='black', facecolor='none', linewidth=2)
    hP.set_label('ROIPatch')
    hAx.add_patch(hP)
    return hP

def cursor_motion_fun(hIm, hAx, mouse_trace, hP):
    x = [pt[0] for pt in mouse_trace] + [mouse_trace[0][0]]
    y = [pt[1] for pt in mouse_trace] + [mouse_trace[0][1]]
    hP.set_xy(list(zip(x, y)))

def drop_fun(hIm, hAx, mouse_trace, hP):
    setup_patch_behavior2(hP, f_refresh_roi_traces)