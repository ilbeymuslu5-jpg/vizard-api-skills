"""Thin wrappers around the ffmpeg/ffprobe CLI used by the clipping pipeline."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


class FFmpegError(RuntimeError):
    pass


def _escape_filter_arg(path: Path) -> str:
    """Escape a filesystem path for use inside an ffmpeg filtergraph argument.

    Windows paths (C:\\foo) contain both ':' and '\\', which the filtergraph
    parser treats as special characters.
    """
    return str(path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise FFmpegError(f"Command failed ({' '.join(cmd)}):\n{proc.stderr[-4000:]}")
    return proc


def probe(path: Path) -> dict:
    proc = _run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ])
    return json.loads(proc.stdout)


def get_duration_seconds(path: Path) -> float:
    info = probe(path)
    return float(info["format"]["duration"])


def get_video_dimensions(path: Path) -> tuple[int, int]:
    info = probe(path)
    for stream in info["streams"]:
        if stream.get("codec_type") == "video":
            return int(stream["width"]), int(stream["height"])
    raise FFmpegError(f"No video stream found in {path}")


def extract_audio(src: Path, dst_wav: Path) -> None:
    dst_wav.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-y", "-i", str(src),
        "-vn", "-ac", "1", "-ar", "16000", "-f", "wav",
        str(dst_wav),
    ])


# ratio id -> (output_w, output_h) in pixels.
RATIO_TARGETS = {
    1: (1080, 1920),  # 9:16 vertical (default, TikTok/Reels/Shorts)
    2: (1080, 1080),  # square
    3: (1080, 1350),  # 4:5 portrait
    4: (1920, 1080),  # original landscape
}


def cover_scale_dims(src_w: int, src_h: int, target_w: int, target_h: int) -> tuple[int, int]:
    """Dimensions to scale (src_w, src_h) to so it fully covers (target_w, target_h),
    preserving aspect ratio (i.e. the smallest enclosing scale, like CSS `background-size:cover`).
    """
    scale = max(target_w / src_w, target_h / src_h)
    scaled_w = max(target_w, int(round(src_w * scale / 2)) * 2)
    scaled_h = max(target_h, int(round(src_h * scale / 2)) * 2)
    return scaled_w, scaled_h


def _scale_crop_filter(src_w: int, src_h: int, target_w: int, target_h: int, pan_x_expr: str | None) -> str:
    scaled_w, scaled_h = cover_scale_dims(src_w, src_h, target_w, target_h)
    x_expr = pan_x_expr if pan_x_expr else str((scaled_w - target_w) // 2)
    y_expr = str((scaled_h - target_h) // 2)
    return f"scale={scaled_w}:{scaled_h},crop={target_w}:{target_h}:x='{x_expr}':y='{y_expr}'"


def cut_clip(
    src: Path,
    dst: Path,
    start: float,
    end: float,
    ratio: int = 1,
    subtitle_ass: Path | None = None,
    remove_silence: bool = False,
    pan_x_expr: str | None = None,
) -> None:
    """Cut [start, end] from src, optionally reframe to a target ratio and burn subtitles.

    `pan_x_expr`, if given, is an ffmpeg time expression (referencing `t`) for the
    crop window's x offset in the *scaled* coordinate space, used to pan the frame
    to follow a detected subject instead of a fixed center crop.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.1, end - start)

    target_w, target_h = RATIO_TARGETS.get(ratio, RATIO_TARGETS[1])
    src_w, src_h = get_video_dimensions(src)
    vf_parts = [_scale_crop_filter(src_w, src_h, target_w, target_h, pan_x_expr)]
    if subtitle_ass is not None:
        filename = _escape_filter_arg(subtitle_ass)
        fontsdir = _escape_filter_arg(FONTS_DIR)
        vf_parts.append(f"ass='{filename}':fontsdir='{fontsdir}'")
    vf = ",".join(vf_parts)

    af_parts = []
    if remove_silence:
        af_parts.append(
            "silenceremove=start_periods=1:start_threshold=-35dB:start_silence=0.3:"
            "stop_periods=-1:stop_threshold=-35dB:stop_silence=0.3:stop_duration=0.5"
        )
    af = ",".join(af_parts) if af_parts else None

    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{duration:.3f}",
        "-vf", vf,
    ]
    if af:
        cmd += ["-af", af]
    cmd += [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(dst),
    ]
    _run(cmd)


def make_thumbnail(src: Path, dst_jpg: Path, at_seconds: float = 0.0) -> None:
    dst_jpg.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-y", "-ss", f"{at_seconds:.3f}", "-i", str(src),
        "-frames:v", "1", "-q:v", "3", str(dst_jpg),
    ])
