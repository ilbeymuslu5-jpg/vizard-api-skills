"""Generate styled .ass subtitle files (burned in via ffmpeg) for a clip."""
from __future__ import annotations

from pathlib import Path

from .transcription import Sentence

# Fonts are bundled in assets/fonts and loaded via ffmpeg's `fontsdir`, so the
# rendered look is identical regardless of what's installed on the host OS.
FONT_PRESETS: dict[str, dict] = {
    "classic": {"label": "Classic", "family": "DejaVu Sans", "caption_size": 64, "headline_size": 54},
    "beast": {"label": "MrBeast (Bold)", "family": "Montserrat ExtraBold", "caption_size": 70, "headline_size": 58},
    "impact": {"label": "Impact", "family": "Bebas Neue", "caption_size": 76, "headline_size": 64},
    "clean": {"label": "Clean", "family": "Roboto Black", "caption_size": 62, "headline_size": 52},
}
DEFAULT_FONT = "classic"

ASS_HEADER_TEMPLATE = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{family},{caption_size},&H00FFFFFF,&H000000FF,&H00101010,&H00000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,140,1
Style: Headline,{family},{headline_size},&H00FDF200,&H000000FF,&H00101010,&H00000000,-1,0,0,0,100,100,0,0,1,4,2,8,60,60,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ass_header(font: str) -> str:
    preset = FONT_PRESETS.get(font, FONT_PRESETS[DEFAULT_FONT])
    return ASS_HEADER_TEMPLATE.format(**preset)


def _ts(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def _escape(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def _wrap_words(words: list[str], max_chars: int) -> list[str]:
    """Greedily group words into lines no longer than max_chars (visible chars)."""
    lines: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for w in words:
        added = len(w) + (1 if cur else 0)
        if cur and cur_len + added > max_chars:
            lines.append(" ".join(cur))
            cur, cur_len = [w], len(w)
        else:
            cur.append(w)
            cur_len += added
    if cur:
        lines.append(" ".join(cur))
    return lines


def _wrap(text: str, max_chars: int = 22) -> str:
    lines = _wrap_words(text.split(), max_chars)
    return "\\N".join(lines[:3])


def build_ass(
    sentences: list[Sentence],
    clip_start: float,
    clip_end: float,
    dst_ass: Path,
    show_subtitles: bool = True,
    headline: str | None = None,
    highlight_words: bool = False,
    font: str = DEFAULT_FONT,
) -> None:
    """Write an .ass file with timestamps relative to the clip (clip_start = t0)."""
    dst_ass.parent.mkdir(parents=True, exist_ok=True)
    events: list[str] = []

    if headline:
        headline_end = min(clip_end, clip_start + 4.0) - clip_start
        events.append(
            f"Dialogue: 1,{_ts(0)},{_ts(headline_end)},Headline,,0,0,0,,{_wrap(_escape(headline.upper()), max_chars=18)}"
        )

    if show_subtitles:
        for sent in sentences:
            if sent.end <= clip_start or sent.start >= clip_end:
                continue
            start = max(0.0, sent.start - clip_start)
            end = min(clip_end, sent.end) - clip_start
            if end <= start:
                continue
            if highlight_words and sent.words:
                text = _build_karaoke_text(sent, clip_start, clip_end)
            else:
                text = _wrap(_escape(sent.text))
            events.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},Caption,,0,0,0,,{text}")

    dst_ass.write_text(_ass_header(font) + "\n".join(events) + "\n", encoding="utf-8")


def _build_karaoke_text(sent: Sentence, clip_start: float, clip_end: float, max_chars: int = 22) -> str:
    tagged: list[str] = []
    visible: list[str] = []
    for w in sent.words:
        if w.end <= clip_start or w.start >= clip_end:
            continue
        dur_cs = max(1, int(round((w.end - w.start) * 100)))
        word = w.text.strip()
        tagged.append(f"{{\\k{dur_cs}}}{_escape(word)}")
        visible.append(word)
    if not tagged:
        return ""

    # Wrap by visible word length, keeping each word's \k tag glued to it.
    lines: list[list[str]] = []
    cur: list[str] = []
    cur_len = 0
    for tag, word in zip(tagged, visible):
        added = len(word) + (1 if cur else 0)
        if cur and cur_len + added > max_chars:
            lines.append(cur)
            cur, cur_len = [tag], len(word)
        else:
            cur.append(tag)
            cur_len += added
    if cur:
        lines.append(cur)
    return "\\N".join(" ".join(line) for line in lines[:3])
