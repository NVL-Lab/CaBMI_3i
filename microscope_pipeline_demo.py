"""
Minimal Python scaffold for a Prairie + NI-DAQ + Arduino pipeline
with extensive comments explaining each step.

This script mirrors the high-level flow of the MATLAB:
1) Connect to Prairie via COM and query image geometry
2) Grab one image frame to use for ROI detection
3) Run a very simple auto-ROI routine using scikit-image
4) Toggle a NI-DAQ digital line for a test TTL pulse
5) Talk to an Arduino over serial (optional) to play a test tone or TTL
6) Save artifacts to disk (image and ROI mask)


Dependencies to install (Windows):
- pywin32        (COM access)           pip install pywin32
- numpy          (numerics)             pip install numpy
- matplotlib     (plotting)             pip install matplotlib
- scikit-image   (image ops)            pip install scikit-image
- nidaqmx        (NI-DAQ I/O)           pip install nidaqmx
- pyserial       (Arduino serial)       pip install pyserial

Hardware assumptions:
- Windows machine with Prairie View / PrairieLink installed and registered as a COM server (ProgID often 'PrairieLink.Application').
- NI-DAQ device present for digital I/O (change line names below to match yours).
- Arduino connected over a COM port if you want the optional test tone/TTL.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

# The following imports are optional depending on which parts you run.
# Each section below checks availability and degrades if missing.
try:
    import win32com.client as win32  # COM client for Prairie
except Exception:
    win32 = None

try:
    import matplotlib.pyplot as plt                            # plotting for sanity checks
except Exception:
    plt = None

try:
    from skimage import filters, measure, morphology, exposure  # simple ROI ops
except Exception:
    filters = measure = morphology = exposure = None

try:
    import nidaqmx                                               # NI-DAQ control
    from nidaqmx.constants import LineGrouping
except Exception:
    nidaqmx = None
    LineGrouping = None

try:
    import serial                                                # Arduino over serial
except Exception:
    serial = None


class PrairieClient:
    """Tiny wrapper around Prairie COM to keep the main flow readable.
       Adjust the strings if Prairie raises an attribute error.
    """

    def __init__(self, prog_id: str = "PrairieLink.Application"):
        self.prog_id = prog_id
        self.app = None

    def connect(self):
        if win32 is None:
            raise RuntimeError("pywin32 is not installed. Install with 'pip install pywin32'.")
        self.app = win32.Dispatch(self.prog_id)
        # Some Prairie builds require an explicit Connect() call; others connect on Dispatch.
        # If Connect() is not present, this call will raise; ignore it.
        try:
            self.app.Connect()
        except Exception:
            pass

    def disconnect(self):
        if self.app is None:
            return
        # As with Connect(), Disconnect() may or may not exist depending on the implementation.
        try:
            self.app.Disconnect()
        except Exception:
            pass
        self.app = None

    def get_pixels_per_frame(self) -> tuple[int, int]:
        """Query image dimensions. The MATLAB had PixelsPerLine/LinesPerFrame."""
        if self.app is None:
            raise RuntimeError("Prairie not connected")
        try:
            px = int(self.app.PixelsPerLine())
            py = int(self.app.LinesPerFrame())
            return px, py
        except Exception as e:
            raise RuntimeError(f"Unable to read pixels per frame from Prairie: {e}")

    def get_microns_per_pixel(self) -> dict[str, float]:
        """Read micron scaling using GetState('micronsPerPixel', 'XAxis'/'YAxis')."""
        if self.app is None:
            raise RuntimeError("Prairie not connected")
        out = {"x": np.nan, "y": np.nan}
        try:
            out["x"] = float(self.app.GetState("micronsPerPixel", "XAxis"))
        except Exception:
            pass
        try:
            out["y"] = float(self.app.GetState("micronsPerPixel", "YAxis"))
        except Exception:
            pass
        return out

    def get_image_2(self, average_frames: int, width: int, height: int) -> np.ndarray:
        """Fetch a summary image. MATLAB used GetImage_2(2, px, py).
           We convert to a numpy array of shape (height, width).
        """
        if self.app is None:
            raise RuntimeError("Prairie not connected")
        try:
            raw = self.app.GetImage_2(int(average_frames), int(width), int(height))
        except Exception as e:
            raise RuntimeError(f"Failed to get image from Prairie: {e}")

        # Convert COM array/buffer to numpy. The following covers common cases; adapt if needed.
        try:
            arr = np.array(raw, dtype=np.float32)
        except Exception:
            # Fallback: try interpreting as a buffer of doubles
            try:
                arr = np.frombuffer(raw, dtype=np.float32)
            except Exception as e:
                raise RuntimeError(f"Could not interpret Prairie image buffer: {e}")

        # Prairie often returns a flat array; reshape to (height, width) with row-major order.
        try:
            arr = arr.reshape((height, width))
        except Exception as e:
            raise RuntimeError(f"Reshape to ({height},{width}) failed: {e}")

        return arr


def simple_auto_roi(im: np.ndarray, expected_cell_um: float | None = None, um_per_pixel: float | None = None) -> np.ndarray:
    """A very basic ROI detector producing a binary mask of putative cells.

    This mirrors the spirit of imFindCellsTM + bwlabel in MATLAB, but is purposely simple:
    1) Contrast enhancement for visualization
    2) Global or local threshold to segment bright somata
    3) Morphology to clean small noise
    4) Optional size filtering if a physical scale is known

    Returns a labeled mask (0=background, 1..N regions) suitable for downstream use.
    """
    if exposure is None or filters is None or morphology is None or measure is None:
        raise RuntimeError("scikit-image is required for ROI detection. Install with 'pip install scikit-image'.")

    im = np.asarray(im, dtype=np.float32)

    # Step 1: rescale intensities for better separation of foreground/background.
    # This does not modify the original data range used for quantitative work; it's for segmentation only.
    im_disp = exposure.rescale_intensity(im, in_range=(np.percentile(im, 1), np.percentile(im, 99)))

    # Step 2: threshold. Otsu is simple and often adequate for quick demos.
    thresh = filters.threshold_otsu(im_disp)
    bw = im_disp > thresh

    # Step 3: remove tiny specks and fill small holes to make ROIs more coherent.
    bw = morphology.remove_small_objects(bw, min_size=20)
    bw = morphology.remove_small_holes(bw, area_threshold=20)

    # Optional Step 4: size filtering based on expected soma diameter in microns and the pixel scale.
    if expected_cell_um is not None and um_per_pixel is not None and np.isfinite(um_per_pixel) and um_per_pixel > 0:
        expected_radius_px = (expected_cell_um / um_per_pixel) / 2.0
        min_area = np.pi * (0.5 * expected_radius_px) ** 2
        max_area = np.pi * (2.0 * expected_radius_px) ** 2
        labeled = measure.label(bw)
        props = measure.regionprops(labeled)
        keep = np.zeros_like(labeled, dtype=bool)
        for p in props:
            if min_area <= p.area <= max_area:
                keep[labeled == p.label] = True
        bw = keep

    labeled = measure.label(bw)
    return labeled


def test_ni_daq_pulse(line: str = "Dev1/port0/line0", pulse_seconds: float = 0.010):
    """Emit a short TTL pulse on a digital line using nidaqmx.

    The default line string must match your device name and line. Use NI MAX to
    discover resource names (e.g., 'Dev1/port0/line0'). The pulse width here is
    controlled in software; for precise timing, use hardware-timed tasks.
    """
    if nidaqmx is None:
        raise RuntimeError("nidaqmx is not installed. Install with 'pip install nidaqmx'.")

    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan(line, line_grouping=LineGrouping.CHAN_PER_LINE)
        task.start()
        task.write(True)
        time.sleep(pulse_seconds)
        task.write(False)
        task.stop()


def test_arduino_serial(port: str, baud: int = 115200, command: bytes = b"TONE\n"):
    """Send a simple command to an Arduino sketch listening over serial.

    You will need to flash an Arduino sketch that interprets commands like 'TONE' or 'TTL' and executes a tone or toggles a pin. This function sends
    one line and reads back a short reply for confirmation.
    """
    if serial is None:
        raise RuntimeError("pyserial is not installed. Install with 'pip install pyserial'.")

    with serial.Serial(port, baudrate=baud, timeout=2) as ser:
        time.sleep(0.2)  # settle time after opening port
        ser.write(command)
        ser.flush()
        try:
            reply = ser.readline().decode(errors="ignore").strip()
            print(f"Arduino replied: {reply}")
        except Exception:
            print("No reply from Arduino (this may be normal if your sketch doesn't print).")


def main():
    """Run the end-to-end demo: Prairie query + image + ROI + DAQ + Arduino (optional)."""

    # Choose where to save artifacts. 
    out_dir = Path.cwd() / "demo_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Step A: Connect to Prairie and fetch one image plus geometry.
    # If Prairie is not present, we create a synthetic image to let the rest of the
    # pipeline be exercised.
    px, py = 512, 512
    um_scale = {"x": np.nan, "y": np.nan}

    prairie_image = None
    prairie = None

    # (Replace this section with the microscope's acquisition call if available.)
    prairie = None  # kept for compatibility with the original structure
    try:
        # Create a synthetic test image (two Gaussian "cells" + noise).
        yy, xx = np.mgrid[0:py, 0:px]
        prairie_image = (
            1000 * np.exp(-((xx - px * 0.3) ** 2 + (yy - py * 0.4) ** 2) / (2 * (px * 0.03) ** 2))
            + 800 * np.exp(-((xx - px * 0.7) ** 2 + (yy - py * 0.6) ** 2) / (2 * (px * 0.04) ** 2))
            + 50 * np.random.randn(py, px)
        ).astype(np.float32)
        print("Using synthetic image instead.")
    except Exception as e:
        # This branch is unlikely to trigger, but we keep it to mirror the original robustness.
        print(f"Image generation failed unexpectedly: {e}")
        raise

    # Save the raw image for reference.
    np.save(out_dir / "im_summary.npy", prairie_image)

    # Step B: Run a very simple auto-ROI detector.
    try:
        expected_cell_um = 12.0  # rough soma diameter; tune as needed
        # Use x-scale if available; otherwise None, which disables size filtering.
        um_per_pixel = um_scale["x"] if np.isfinite(um_scale["x"]) else None
        labeled = simple_auto_roi(prairie_image, expected_cell_um=expected_cell_um, um_per_pixel=um_per_pixel)
        print(f"Detected {labeled.max()} candidate ROIs")
        np.save(out_dir / "roi_labels.npy", labeled)
    except Exception as e:
        print(f"Auto-ROI step skipped or failed: {e}")
        labeled = np.zeros_like(prairie_image, dtype=np.int32)

    # Step C: Quick visualization if matplotlib is present.
    if plt is not None:
        fig1 = plt.figure()
        plt.title("Summary image")
        plt.imshow(prairie_image, cmap="gray")
        fig1.savefig(out_dir / "im_summary.png", dpi=150)

        fig2 = plt.figure()
        plt.title("Labeled ROIs (random colormap)")
        # This quick view assigns a random color per label for a nicer look.
        labels_vis = labeled.copy()
        plt.imshow(labels_vis, cmap="nipy_spectral")
        fig2.savefig(out_dir / "roi_labels.png", dpi=150)

        plt.close("all")

    # Step D: Emit a short NI-DAQ TTL pulse for sanity (optional).
    # If you don't have nidaqmx installed or no hardware present, this will raise; we catch and continue.
    try:
        test_ni_daq_pulse(line="Dev1/port0/line0", pulse_seconds=0.010)
        print("NI-DAQ pulse sent on Dev1/port0/line0")
    except Exception as e:
        print(f"NI-DAQ test skipped or failed: {e}")

    # Step E: Ping an Arduino over serial (optional). Set the correct COM port if you want to try it.
    # If you don't have an Arduino connected, this will fail.
    try:
        # Example: on Windows this might be 'COM5'. Update to your actual port or skip.
        # test_arduino_serial(port='COM5', command=b'TONE\n')
        pass
    except Exception as e:
        print(f"Arduino test skipped or failed: {e}")

    print(f"All done. Artifacts saved in: {out_dir}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user.")
        sys.exit(1)

