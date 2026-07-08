from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    videoUrl: Optional[str] = None
    videoType: int = 1
    ext: Optional[str] = None
    lang: str = "auto"
    projectName: Optional[str] = None

    # Clipping mode
    getClips: int = 1
    preferLength: list[int] = Field(default_factory=lambda: [0])
    maxClipCount: int = 8

    # Editing/rendering options (apply to every produced clip)
    ratioOfClip: int = 1
    subtitleSwitch: int = 1
    headlineSwitch: int = 0
    highlightSwitch: int = 1
    removeSilenceSwitch: int = 0
    captionFont: str = "classic"
    smartReframeSwitch: int = 1


class ClipOut(BaseModel):
    videoId: str
    title: str
    transcript: str
    viralScore: str
    viralReason: str
    videoMsDuration: int
    startMs: int
    endMs: int
    videoUrl: str
    thumbnailUrl: str
    language: str


class ProjectStatusOut(BaseModel):
    code: int
    projectId: str
    projectName: str
    status: str
    progress: int
    message: str = ""
    videos: list[ClipOut] = Field(default_factory=list)


class AiSocialRequest(BaseModel):
    finalVideoId: str
    aiSocialPlatform: int = 1
    tone: int = 0
    voice: int = 0
