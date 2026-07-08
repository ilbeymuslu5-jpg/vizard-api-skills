"""Local, heuristic replacement for Vizard's `ai-social` caption generator.

No LLM call is made -- captions are built from simple keyword extraction and
platform/tone templates, picked by the source video's detected language.
Good enough for a first draft; users are expected to tweak before posting.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "to", "of",
    "in", "on", "for", "with", "that", "this", "it", "i", "you", "we", "they",
    "he", "she", "be", "have", "has", "had", "do", "does", "did", "so", "at",
    "as", "by", "from", "if", "then", "than", "just", "not", "will", "would",
    "can", "could", "there", "their", "our", "your", "my", "me", "us", "them",
}

STOPWORDS_TR = {
    "bir", "bu", "şu", "o", "ve", "ile", "için", "gibi", "çok", "daha", "ama",
    "fakat", "de", "da", "ki", "mi", "mı", "mu", "mü", "ne", "nasıl", "niçin",
    "hep", "hiç", "her", "ben", "sen", "biz", "siz", "onlar", "benim", "senin",
    "onun", "bizim", "sizin", "onların", "var", "yok", "olarak", "kadar",
    "sonra", "önce", "şey", "böyle", "şöyle", "bana", "beni", "seni", "ona",
}

PLATFORM_NAMES = {1: "General", 2: "TikTok", 3: "Instagram", 4: "YouTube", 5: "Facebook", 6: "LinkedIn", 7: "Twitter"}

TONE_TEMPLATES_EN = {
    0: "{hook}. Here's what stood out: {body}",
    1: "You need to hear this: {hook}. {body}",
    2: "{hook}?! Wait for it... {body}",
    3: "{hook}. {body}",
    4: "Ever wonder {hook_lower}? {body}",
}

TONE_TEMPLATES_TR = {
    0: "{hook}. İşte öne çıkan kısım: {body}",
    1: "Bunu mutlaka duymalısın: {hook}. {body}",
    2: "{hook}?! Devamını izle... {body}",
    3: "{hook}. {body}",
    4: "Hiç {hook_lower} diye düşündün mü? {body}",
}

_LOCALES = {
    "tr": {"stopwords": STOPWORDS_TR, "templates": TONE_TEMPLATES_TR},
    "en": {"stopwords": STOPWORDS_EN, "templates": TONE_TEMPLATES_EN},
}
DEFAULT_LOCALE = "en"

WORD_RE = re.compile(r"[^\W\d_]{3,}", re.UNICODE)


def _locale(language: str | None) -> dict:
    return _LOCALES.get((language or "").lower(), _LOCALES[DEFAULT_LOCALE])


def _casefold(text: str) -> str:
    # Python's default lower() turns Turkish "İ" into "i" + a combining dot
    # above, which then gets mis-tokenized; strip stray combining marks.
    lowered = text.lower()
    return "".join(c for c in lowered if not unicodedata.combining(c))


def _keywords(text: str, stopwords: set[str], top_n: int = 6) -> list[str]:
    words = WORD_RE.findall(_casefold(text))
    words = [w for w in words if w not in stopwords]
    counts = Counter(words)
    return [w for w, _ in counts.most_common(top_n)]


def generate_social_post(
    transcript: str,
    platform: int = 1,
    tone: int = 0,
    voice: int = 0,
    language: str | None = None,
) -> tuple[str, list[str]]:
    transcript = transcript.strip()
    if not transcript:
        raise ValueError("no speech/dialogue detected")

    locale = _locale(language)

    sentences = re.split(r"(?<=[.!?])\s+", transcript)
    hook = sentences[0].strip().rstrip(".!?") if sentences else transcript[:60]
    body = " ".join(sentences[1:3]).strip() or hook

    if voice == 1:  # third person (English-only heuristic; harmless no-op for other languages)
        body = re.sub(r"\bI\b", "they", body)
        body = re.sub(r"\bmy\b", "their", body, flags=re.IGNORECASE)

    template = locale["templates"].get(tone, locale["templates"][0])
    caption = template.format(hook=hook, hook_lower=_casefold(hook), body=body)

    keywords = _keywords(transcript, locale["stopwords"])
    hashtags = [f"#{w}" for w in keywords]
    if PLATFORM_NAMES.get(platform) not in (None, "General"):
        hashtags.append(f"#{PLATFORM_NAMES[platform]}")

    return caption.strip(), hashtags
