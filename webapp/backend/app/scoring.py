"""Heuristic 'viral potential' scoring for candidate clips.

There is no cloud AI model involved here -- this is a local, transparent
substitute for Vizard's proprietary scoring model. It rewards hallmarks of
engaging short-form clips: hooks, curiosity gaps, punchy pacing, numbers, and
emotionally-charged language.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .transcription import Sentence

HOOK_WORDS = {
    "secret", "never", "always", "mistake", "amazing", "shocking", "unbelievable",
    "hack", "tip", "why", "how", "best", "worst", "truth", "warning", "stop",
    "wrong", "wait", "actually", "surprising", "crazy", "insane", "important",
    "biggest", "huge", "free", "proven", "guarantee", "fail", "win", "lesson",
    "story", "honestly", "literally", "imagine", "listen", "problem", "answer",
}

NUMBER_RE = re.compile(r"\b\d+\b")
QUESTION_RE = re.compile(r"\?")
EXCLAIM_RE = re.compile(r"!")

IDEAL_WORDS_PER_SEC = (1.8, 3.2)  # comfortable spoken pace range


@dataclass
class Candidate:
    start: float
    end: float
    text: str
    sentences: list[Sentence]

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class ScoredClip(Candidate):
    score: float = 0.0
    reasons: list[str] = None  # type: ignore[assignment]


PREFER_LENGTH_BOUNDS = {
    0: (15.0, 90.0),   # auto
    1: (5.0, 30.0),    # <30s
    2: (30.0, 60.0),   # 30-60s
    3: (60.0, 90.0),   # 60-90s
    4: (90.0, 180.0),  # >90s
    5: (28.0, 38.0),   # Shorts sweet spot (~30-35s)
}


def build_candidates(sentences: list[Sentence], prefer_lengths: list[int]) -> list[Candidate]:
    """Slide a window over consecutive sentences to build clip candidates."""
    bounds = [PREFER_LENGTH_BOUNDS.get(p, PREFER_LENGTH_BOUNDS[0]) for p in prefer_lengths] or [PREFER_LENGTH_BOUNDS[0]]
    min_len = min(b[0] for b in bounds)
    max_len = max(b[1] for b in bounds)

    candidates: list[Candidate] = []
    n = len(sentences)
    for i in range(n):
        acc_text = []
        for j in range(i, n):
            start = sentences[i].start
            end = sentences[j].end
            dur = end - start
            if dur > max_len:
                break
            acc_text.append(sentences[j].text)
            if dur >= min_len:
                candidates.append(Candidate(
                    start=start, end=end,
                    text=" ".join(acc_text),
                    sentences=sentences[i:j + 1],
                ))
    return candidates


def score_candidate(cand: Candidate, prefer_lengths: list[int]) -> ScoredClip:
    text = cand.text
    lower = text.lower()
    words = lower.split()
    word_count = max(1, len(words))

    reasons: list[str] = []
    score = 4.0  # baseline

    hook_hits = sum(1 for w in words if w.strip(".,!?'\"") in HOOK_WORDS)
    if hook_hits:
        bonus = min(2.5, hook_hits * 0.6)
        score += bonus
        reasons.append(f"{hook_hits} attention-grabbing word(s)")

    if QUESTION_RE.search(text):
        score += 0.8
        reasons.append("poses a question (curiosity hook)")

    if EXCLAIM_RE.search(text):
        score += 0.4
        reasons.append("emphatic/exclamatory tone")

    if NUMBER_RE.search(text):
        score += 0.5
        reasons.append("contains a concrete number/list")

    wps = word_count / max(0.1, cand.duration)
    lo, hi = IDEAL_WORDS_PER_SEC
    if lo <= wps <= hi:
        score += 1.0
        reasons.append("energetic, well-paced delivery")
    elif wps < lo * 0.5 or wps > hi * 1.6:
        score -= 1.0

    bounds = [PREFER_LENGTH_BOUNDS.get(p, PREFER_LENGTH_BOUNDS[0]) for p in prefer_lengths] or [PREFER_LENGTH_BOUNDS[0]]
    best_fit = min(abs(cand.duration - (b[0] + b[1]) / 2) for b in bounds)
    score += max(0.0, 1.2 - best_fit / 45.0)

    if words[:3] and any(w in HOOK_WORDS for w in words[:3]):
        score += 0.5
        reasons.append("opens with a strong hook")

    unique_ratio = len(set(words)) / word_count
    if unique_ratio < 0.45:
        score -= 0.8

    score = max(0.0, min(10.0, score))
    if not reasons:
        reasons.append("clear, self-contained thought")

    return ScoredClip(
        start=cand.start, end=cand.end, text=cand.text, sentences=cand.sentences,
        score=round(score, 1), reasons=reasons,
    )


def select_top_clips(
    sentences: list[Sentence],
    prefer_lengths: list[int],
    max_clips: int = 8,
) -> list[ScoredClip]:
    candidates = build_candidates(sentences, prefer_lengths)
    scored = [score_candidate(c, prefer_lengths) for c in candidates]
    scored.sort(key=lambda c: c.score, reverse=True)

    chosen: list[ScoredClip] = []
    for clip in scored:
        if any(not (clip.end <= c.start or clip.start >= c.end) for c in chosen):
            continue  # overlaps an already-chosen clip
        chosen.append(clip)
        if len(chosen) >= max_clips:
            break

    chosen.sort(key=lambda c: c.start)
    return chosen
