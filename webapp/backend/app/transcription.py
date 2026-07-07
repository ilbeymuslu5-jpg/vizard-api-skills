"""Local speech-to-text using faster-whisper (CPU-friendly, no cloud calls)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from faster_whisper import WhisperModel

_MODEL_CACHE: dict[str, WhisperModel] = {}

DEFAULT_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")

SENTENCE_END_RE = re.compile(r"[.!?]\s*$")


@dataclass
class Word:
    text: str
    start: float
    end: float


@dataclass
class Sentence:
    text: str
    start: float
    end: float
    words: list[Word] = field(default_factory=list)


def _get_model(model_size: str = DEFAULT_MODEL_SIZE) -> WhisperModel:
    if model_size not in _MODEL_CACHE:
        _MODEL_CACHE[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _MODEL_CACHE[model_size]


def transcribe(
    audio_path: Path,
    language: str | None = None,
    model_size: str = DEFAULT_MODEL_SIZE,
) -> tuple[list[Sentence], str]:
    """Transcribe audio into sentence-level segments with word timestamps.

    Returns (sentences, detected_language).
    """
    model = _get_model(model_size)
    lang = None if (language is None or language == "auto") else language

    segments, info = model.transcribe(
        str(audio_path),
        language=lang,
        word_timestamps=True,
        vad_filter=True,
    )

    sentences: list[Sentence] = []
    cur_words: list[Word] = []

    def flush():
        if not cur_words:
            return
        text = re.sub(r"\s+", " ", "".join(w.text for w in cur_words)).strip()
        sentences.append(Sentence(text=text, start=cur_words[0].start, end=cur_words[-1].end, words=list(cur_words)))
        cur_words.clear()

    for seg in segments:
        if not seg.words:
            continue
        for w in seg.words:
            if not w.word.strip():
                continue
            # faster-whisper tokens carry their own leading space, e.g. " hello".
            cur_words.append(Word(text=w.word, start=w.start, end=w.end))
            if SENTENCE_END_RE.search(w.word):
                flush()
    flush()

    return sentences, info.language
