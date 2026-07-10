"""Acquire the source video: a local upload, a direct file URL, or a
YouTube/Vimeo/etc. link (via yt-dlp). Everything runs on this machine --
no third-party clipping API is involved.
"""
from __future__ import annotations

import os
import shutil
import urllib.request
from pathlib import Path

# Mirrors the `videoType` values used in the Vizard API skill docs, so the
# request shape will feel familiar to anyone coming from that integration.
VIDEO_TYPE_LOCAL_UPLOAD = 1
VIDEO_TYPE_YOUTUBE = 2
VIDEO_TYPE_GDRIVE = 3
VIDEO_TYPE_VIMEO = 4

YTDLP_TYPES = {VIDEO_TYPE_YOUTUBE, VIDEO_TYPE_VIMEO, 5, 6, 7, 9, 10, 11, 12}


class DownloadError(RuntimeError):
    pass


def fetch_source_video(
    dest_dir: Path,
    video_url: str | None,
    video_type: int,
    uploaded_file: Path | None = None,
) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)

    if uploaded_file is not None:
        dst = dest_dir / f"source{uploaded_file.suffix or '.mp4'}"
        shutil.move(str(uploaded_file), dst)
        return dst

    if not video_url:
        raise DownloadError("Either an uploaded file or a videoUrl is required")

    if video_type in YTDLP_TYPES:
        return _download_with_ytdlp(video_url, dest_dir)

    return _download_direct(video_url, dest_dir)


def _download_with_ytdlp(url: str, dest_dir: Path) -> Path:
    import yt_dlp

    outtmpl = str(dest_dir / "source.%(ext)s")
    opts = {
        "outtmpl": outtmpl,
        "format": "bv*[height<=1080]+ba/b[height<=1080]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    # YouTube increasingly challenges datacenter/repeat-request IPs with a
    # "confirm you're not a bot" wall. Borrowing cookies from a real, signed-in
    # local browser session (yt-dlp's own recommended fix) works around it.
    browser = os.environ.get("YTDLP_COOKIES_FROM_BROWSER", "chrome")
    if browser:
        opts["cookiesfrombrowser"] = (browser,)

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as exc:  # yt_dlp raises its own exception types
        raise DownloadError(f"Failed to download video: {exc}") from exc

    matches = list(dest_dir.glob("source.*"))
    if not matches:
        raise DownloadError("Download finished but no output file was found")
    return matches[0]


def _download_direct(url: str, dest_dir: Path) -> Path:
    ext = Path(url.split("?")[0]).suffix or ".mp4"
    dst = dest_dir / f"source{ext}"
    try:
        with urllib.request.urlopen(url) as resp, open(dst, "wb") as f:
            shutil.copyfileobj(resp, f)
    except Exception as exc:
        raise DownloadError(f"Failed to download video from URL: {exc}") from exc
    return dst
