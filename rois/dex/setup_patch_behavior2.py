import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np
from matplotlib.widgets import PolygonSelector
from skimage.draw import polygon2mask
from get_ud import get_ud

from set_ud import set_ud
from get_current_point import get_current_point
from catch_mouse_drag import catch_mouse_drag

def setup_patch_behavior2(h_pin_list, f_refresh_roi_traces):
    for h_pin in h_pin_list:
        set_ud(h_pin, 'hPlotTrace', None)

        if len(h_pin.get_xdata()) < 5:
            h_pin.remove()
            return

        h_pin.set_picker(True)
        h_pin.set_gid("ROIPatch")
        h_pin.figure.canvas.mpl_connect('button_press_event', lambda event: patch_click(h_pin, h_pin.axes))

        current_point = get_current_point(h_pin.axes)
        catch_mouse_drag(h_pin, patch_click, patch_motion_fun, patch_drop_fun, 'extend')
        refresh_rois(h_pin)

    f_refresh_roi_traces()

def patch_motion_fun(h_patch, h_ax, mouse_trace, custom):
    initxdata = h_patch.get_xdata()
    initydata = h_patch.get_ydata()
    dist = np.subtract(mouse_trace[-1], mouse_trace[-2])
    h_patch.set_xdata(initxdata + dist[0])
    h_patch.set_ydata(initydata + dist[1])
    refresh_rois(h_patch)
    f_refresh_roi_traces() #Seems like an event function but Nuria said it should be an int

def patch_drop_fun(h_patch, h_ax, mouse_trace, custom):
    h_trace = get_ud(h_patch, 'hPlotTrace')
    if h_trace is not None and h_trace in h_ax.lines:
        h_trace.set_linewidth(0.5)

    refresh_rois(h_patch)
    f_refresh_roi_traces()

def refresh_rois(h_patch):
    h_ax = h_patch.axes
    h_im = next(obj for obj in h_ax.get_children() if isinstance(obj, plt.AxesImage))
    s = h_im.get_array().shape
    xdata = h_patch.get_xdata()
    ydata = h_patch.get_ydata()
    # binroi = poly2mask(xdata, ydata, s[0], s[1])
    binroi = polygon2mask((s[0], s[1]), np.column_stack((ydata, xdata))).astype(np.uint8)
    set_ud(h_patch, 'binroi', binroi)

def make_cm_roi(h_patch):
    # Placeholder: actual UI context menu integration differs in Python
    pass

def cm_roi_callback(h_obj, *args):
    pass  # Placeholder for actual implementation

def patch_click(h_patch, h_ax, *args):
    h_plot_trace = get_ud(h_patch, 'hPlotTrace')
    if h_plot_trace is not None:
        h_plot_trace.set_linewidth(2)

        def window_button_up(event):
            if h_plot_trace is not None:
                h_plot_trace.set_linewidth(0.5)

        h_patch.figure.canvas.mpl_connect('button_release_event', window_button_up)

    return get_current_point(h_patch.axes)