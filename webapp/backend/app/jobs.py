from __future__ import annotations

import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import ffmpeg_utils, subtitles
from .downloader import DownloadError, fetch_source_video
from .scoring import ScoredClip, select_top_clips
from .schemas import ProjectCreateRequest
from .transcription import transcribe

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROJECTS_DIR = DATA_DIR / "projects"

_executor = ThreadPoolExecutor(max_workers=2)
_lock = threading.Lock()
_jobs: dict[str, dict] = {}


def _project_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id


def _save_state(project_id: str) -> None:
    d = _project_dir(project_id)
    d.mkdir(parents=True, exist_ok=True)
    with _lock:
        state = dict(_jobs[project_id])
    (d / "meta.json").write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def _update(project_id: str, **kwargs) -> None:
    with _lock:
        _jobs[project_id].update(kwargs)
    _save_state(project_id)


def find_clip(video_id: str) -> dict | None:
    project_id = video_id.rsplit("_", 1)[0]
    project = get_project(project_id)
    if not project:
        return None
    for video in project.get("videos", []):
        if video["videoId"] == video_id:
            return video
    return None


def get_project(project_id: str) -> dict | None:
    with _lock:
        if project_id in _jobs:
            return dict(_jobs[project_id])
    meta = _project_dir(project_id) / "meta.json"
    if meta.exists():
        return json.loads(meta.read_text(encoding="utf-8"))
    return None


def create_project(req: ProjectCreateRequest, uploaded_file: Path | None) -> str:
    project_id = uuid.uuid4().hex[:12]
    name = req.projectName or (uploaded_file.name if uploaded_file else req.videoUrl or "Untitled Project")
    with _lock:
        _jobs[project_id] = {
            "projectId": project_id,
            "projectName": name,
            "status": "queued",
            "progress": 0,
            "code": 1000,
            "message": "Queued",
            "videos": [],
        }
    _save_state(project_id)
    _executor.submit(_run_pipeline, project_id, req, uploaded_file)
    return project_id


def _run_pipeline(project_id: str, req: ProjectCreateRequest, uploaded_file: Path | None) -> None:
    pdir = _project_dir(project_id)
    try:
        _update(project_id, status="downloading", progress=5, code=1000, message="Fetching source video")
        source = fetch_source_video(pdir, req.videoUrl, req.videoType, uploaded_file)

        _update(project_id, status="extracting_audio", progress=15, message="Extracting audio")
        audio_path = pdir / "audio.wav"
        ffmpeg_utils.extract_audio(source, audio_path)

        _update(project_id, status="transcribing", progress=25, message="Transcribing speech (local, on-device)")
        lang = None if req.lang == "auto" else req.lang
        sentences, detected_lang = transcribe(audio_path, language=lang)

        if not sentences:
            _update(project_id, status="failed", progress=100, code=4002,
                     message="No speech detected in the video")
            return

        _update(project_id, status="analyzing", progress=45, message="Scoring candidate clips")
        prefer_lengths = req.preferLength or [0]
        clips = select_top_clips(sentences, prefer_lengths, max_clips=max(1, req.maxClipCount))

        if not clips:
            _update(project_id, status="failed", progress=100, code=4002,
                     message="Could not find any clip-worthy segments")
            return

        videos = []
        total = len(clips)
        for idx, clip in enumerate(clips):
            progress = 50 + int(45 * (idx / total))
            _update(project_id, status="rendering", progress=progress,
                     message=f"Rendering clip {idx + 1}/{total}")
            video_id = f"{project_id}_{idx}"
            video = _render_clip(pdir, video_id, source, clip, req)
            videos.append(video)
            with _lock:
                _jobs[project_id]["videos"] = videos
            _save_state(project_id)

        _update(project_id, status="completed", progress=100, code=2000,
                 message=f"Done ({detected_lang} detected)", videos=videos)

    except DownloadError as exc:
        _update(project_id, status="failed", progress=100, code=4008, message=str(exc))
    except Exception as exc:  # pragma: no cover - safety net for background thread
        _update(project_id, status="failed", progress=100, code=4002, message=f"Processing error: {exc}")


def _render_clip(pdir: Path, video_id: str, source: Path, clip: ScoredClip, req: ProjectCreateRequest) -> dict:
    clips_dir = pdir / "clips"
    subs_dir = pdir / "subs"
    thumbs_dir = pdir / "thumbs"
    for d in (clips_dir, subs_dir, thumbs_dir):
        d.mkdir(parents=True, exist_ok=True)

    title = _make_title(clip.text)
    ass_path = subs_dir / f"{video_id}.ass"
    subtitles.build_ass(
        clip.sentences, clip.start, clip.end, ass_path,
        show_subtitles=bool(req.subtitleSwitch),
        headline=title if req.headlineSwitch else None,
        highlight_words=bool(req.highlightSwitch),
    )

    out_path = clips_dir / f"{video_id}.mp4"
    ffmpeg_utils.cut_clip(
        source, out_path, clip.start, clip.end,
        ratio=req.ratioOfClip,
        subtitle_ass=ass_path,
        remove_silence=bool(req.removeSilenceSwitch),
    )

    thumb_path = thumbs_dir / f"{video_id}.jpg"
    ffmpeg_utils.make_thumbnail(out_path, thumb_path, at_seconds=min(0.5, clip.duration / 2))

    return {
        "videoId": video_id,
        "title": title,
        "transcript": clip.text,
        "viralScore": f"{clip.score:.1f}",
        "viralReason": "; ".join(clip.reasons),
        "videoMsDuration": int(clip.duration * 1000),
        "startMs": int(clip.start * 1000),
        "endMs": int(clip.end * 1000),
        "videoUrl": f"/api/v1/project/files/{pdir.name}/clips/{video_id}.mp4",
        "thumbnailUrl": f"/api/v1/project/files/{pdir.name}/thumbs/{video_id}.jpg",
    }


def _make_title(text: str, max_words: int = 10) -> str:
    words = text.strip().split()
    title = " ".join(words[:max_words])
    if len(words) > max_words:
        title += "..."
    return title[:1].upper() + title[1:] if title else "Untitled clip"
