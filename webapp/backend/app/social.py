"""Local, heuristic replacement for Vizard's `ai-social` caption generator.

No LLM call is made -- captions are built from simple keyword extraction and
platform/tone templates. Good enough for a first draft; users are expected to
tweak before posting.
"""
from __future__ import annotations

import re
from collections import Counter

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "to", "of",
    "in", "on", "for", "with", "that", "this", "it", "i", "you", "we", "they",
    "he", "she", "be", "have", "has", "had", "do", "does", "did", "so", "at",
    "as", "by", "from", "if", "then", "than", "just", "not", "will", "would",
    "can", "could", "there", "their", "our", "your", "my", "me", "us", "them",
}

PLATFORM_NAMES = {1: "General", 2: "TikTok", 3: "Instagram", 4: "YouTube", 5: "Facebook", 6: "LinkedIn", 7: "Twitter"}
TONE_TEMPLATES = {
    0: "{hook}. Here's what stood out: {body}",
    1: "You need to hear this: {hook}. {body}",
    2: "{hook}?! Wait for it... {body}",
    3: "{hook}. {body}",
    4: "Ever wonder {hook_lower}? {body}",
}


def _keywords(text: str, top_n: int = 6) -> list[str]:
    words = re.findall(r"[A-Za-z']{3,}", text.lower())
    words = [w for w in words if w not in STOPWORDS]
    counts = Counter(words)
    return [w for w, _ in counts.most_common(top_n)]


def generate_social_post(
    transcript: str,
    platform: int = 1,
    tone: int = 0,
    voice: int = 0,
) -> tuple[str, list[str]]:
    transcript = transcript.strip()
    if not transcript:
        raise ValueError("no speech/dialogue detected")

    sentences = re.split(r"(?<=[.!?])\s+", transcript)
    hook = sentences[0].strip().rstrip(".!?") if sentences else transcript[:60]
    body = " ".join(sentences[1:3]).strip() or hook

    if voice == 1:  # third person
        body = re.sub(r"\bI\b", "they", body)
        body = re.sub(r"\bmy\b", "their", body, flags=re.IGNORECASE)

    template = TONE_TEMPLATES.get(tone, TONE_TEMPLATES[0])
    caption = template.format(hook=hook, hook_lower=hook.lower(), body=body)

    keywords = _keywords(transcript)
    hashtags = [f"#{w}" for w in keywords]
    if PLATFORM_NAMES.get(platform) not in (None, "General"):
        hashtags.append(f"#{PLATFORM_NAMES[platform]}")

    return caption.strip(), hashtags
