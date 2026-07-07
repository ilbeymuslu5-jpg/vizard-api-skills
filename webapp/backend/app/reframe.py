"""Face-based dynamic reframing.

Vizard's "auto reframe" keeps the speaker in view when cropping a landscape
source down to a vertical/square clip instead of using a fixed center crop.
This is a local approximation of that: sample frames across the clip, run a
Haar-cascade face detector (bundled with opencv, no network/model download
needed), track the largest face's horizontal position over time, smooth it,
and turn that into an ffmpeg crop `x` expression that pans the frame instead
of a static crop.
"""
from __future__ import annotations

import math
from pathlib import Path

import cv2

from .ffmpeg_utils import RATIO_TARGETS, cover_scale_dims, get_video_dimensions

_FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

MAX_KEYFRAMES = 60
MIN_SEGMENT_SECONDS = 0.75
SMOOTHING_ALPHA = 0.5  # lower = smoother/slower to react, higher = snappier


def _largest_face_center_frac(frame) -> float | None:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(40, 40))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return (x + w / 2) / frame.shape[1]


def compute_pan_expr(source: Path, clip_start: float, clip_end: float, ratio: int) -> str | None:
    """Return an ffmpeg `x` expression (scaled-pixel space, referencing `t`)
    that pans the crop window to follow the largest detected face, or None if
    there's no room to pan or no face was found anywhere in the clip (in
    which case the caller should fall back to a static center crop).
    """
    target_w, target_h = RATIO_TARGETS.get(ratio, RATIO_TARGETS[1])
    src_w, src_h = get_video_dimensions(source)
    scaled_w, scaled_h = cover_scale_dims(src_w, src_h, target_w, target_h)
    pan_range = scaled_w - target_w
    if pan_range < 10:
        return None  # square-ish source already fills the target width, nothing to pan

    duration = clip_end - clip_start
    if duration <= 0:
        return None

    segment_duration = max(MIN_SEGMENT_SECONDS, duration / MAX_KEYFRAMES)
    n_segments = max(1, math.ceil(duration / segment_duration))

    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        return None

    raw: list[float] = []
    try:
        for i in range(n_segments):
            t_mid = min(clip_start + (i + 0.5) * segment_duration, clip_end - 0.01)
            cap.set(cv2.CAP_PROP_POS_MSEC, t_mid * 1000)
            ok, frame = cap.read()
            frac = _largest_face_center_frac(frame) if ok and frame is not None else None
            if frac is None:
                frac = raw[-1] if raw else 0.5
            raw.append(frac)
    finally:
        cap.release()

    if all(abs(f - 0.5) < 0.03 for f in raw):
        return None  # no meaningfully off-center subject detected; static crop is fine

    smoothed: list[float] = []
    for f in raw:
        smoothed.append(f if not smoothed else SMOOTHING_ALPHA * f + (1 - SMOOTHING_ALPHA) * smoothed[-1])

    keyframes = [((i + 0.5) * segment_duration, smoothed[i]) for i in range(n_segments)]
    return _piecewise_pixel_expr(keyframes, scaled_w, target_w, pan_range)


def _piecewise_pixel_expr(
    keyframes: list[tuple[float, float]], scaled_w: int, target_w: int, pan_range: int
) -> str:
    def to_pixels(frac_expr: str) -> str:
        return f"clip(({frac_expr})*{scaled_w}-{target_w}/2,0,{pan_range})"

    if len(keyframes) == 1:
        return to_pixels(f"{keyframes[0][1]:.4f}")

    expr = f"{keyframes[-1][1]:.4f}"
    for i in range(len(keyframes) - 2, -1, -1):
        t0, f0 = keyframes[i]
        t1, f1 = keyframes[i + 1]
        segment = f"({f0:.4f}+({f1:.4f}-{f0:.4f})*(t-{t0:.3f})/{(t1 - t0):.3f})"
        expr = f"if(lt(t,{t1:.3f}),{segment},{expr})"
    expr = f"if(lt(t,{keyframes[0][0]:.3f}),{keyframes[0][1]:.4f},{expr})"
    return to_pixels(expr)
