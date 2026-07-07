from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import jobs, social
from .schemas import AiSocialRequest, ProjectCreateRequest

app = FastAPI(title="Vizard Local", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1/project"


def _parse_int_list(raw: str | None, default: list[int]) -> list[int]:
    if not raw:
        return default
    return [int(x) for x in raw.split(",") if x.strip() != ""]


@app.post(f"{API_PREFIX}/create")
async def create_project(
    file: Optional[UploadFile] = File(None),
    videoUrl: Optional[str] = Form(None),
    videoType: int = Form(1),
    lang: str = Form("auto"),
    projectName: Optional[str] = Form(None),
    getClips: int = Form(1),
    preferLength: Optional[str] = Form(None),
    maxClipCount: int = Form(8),
    ratioOfClip: int = Form(1),
    subtitleSwitch: int = Form(1),
    headlineSwitch: int = Form(1),
    highlightSwitch: int = Form(0),
    removeSilenceSwitch: int = Form(0),
    captionFont: str = Form("classic"),
):
    if file is None and not videoUrl:
        raise HTTPException(400, "Provide either a file upload or a videoUrl")

    req = ProjectCreateRequest(
        videoUrl=videoUrl,
        videoType=videoType,
        lang=lang,
        projectName=projectName,
        getClips=getClips,
        preferLength=_parse_int_list(preferLength, [0]),
        maxClipCount=maxClipCount,
        ratioOfClip=ratioOfClip,
        subtitleSwitch=subtitleSwitch,
        headlineSwitch=headlineSwitch,
        highlightSwitch=highlightSwitch,
        removeSilenceSwitch=removeSilenceSwitch,
        captionFont=captionFont,
    )

    uploaded_path = None
    if file is not None:
        suffix = Path(file.filename or "upload.mp4").suffix or ".mp4"
        fd, tmp_name = tempfile.mkstemp(suffix=suffix)
        os.close(fd)  # avoid holding a second open handle (locks the file on Windows)
        tmp = Path(tmp_name)
        with tmp.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        uploaded_path = tmp

    project_id = jobs.create_project(req, uploaded_path)
    return {"code": 2000, "projectId": project_id}


@app.get(f"{API_PREFIX}/query/{{project_id}}")
async def query_project(project_id: str):
    project = jobs.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@app.get(f"{API_PREFIX}/files/{{project_id}}/{{subpath:path}}")
async def get_file(project_id: str, subpath: str):
    path = (jobs.PROJECTS_DIR / project_id / subpath).resolve()
    if jobs.PROJECTS_DIR.resolve() not in path.parents or not path.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(path)


@app.get(f"{API_PREFIX}/social-accounts")
async def social_accounts():
    # Publishing to real social platforms needs per-platform OAuth apps and
    # is out of scope for a local clone; this local build focuses on the
    # clip-generation pipeline. Export clips and post them manually.
    return {"code": 2000, "accounts": [], "note": "Direct publishing isn't implemented locally; download clips and upload manually."}


@app.post(f"{API_PREFIX}/ai-social")
async def ai_social(req: AiSocialRequest):
    clip = jobs.find_clip(req.finalVideoId)
    if not clip:
        raise HTTPException(404, "Unknown videoId")
    try:
        caption, hashtags = social.generate_social_post(
            clip["transcript"], platform=req.aiSocialPlatform, tone=req.tone, voice=req.voice,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    full_text = caption + ("\n\n" + " ".join(hashtags) if hashtags else "")
    return {"code": 2000, "aiSocialContent": full_text, "aiSocialTitle": clip["title"]}


FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
