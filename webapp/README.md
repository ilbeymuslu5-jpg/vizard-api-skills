# Vizard Local — a self-hosted AI clipping studio

A local clone of [Vizard.ai](https://vizard.ai)'s core workflow: turn a long
video into short, ranked, subtitle-burned clips for TikTok/Shorts/Reels —
without an API key, a subscription, or sending your video to a cloud service.
Everything (speech-to-text, clip selection, scoring, subtitle rendering,
cropping) runs on your own machine.

It intentionally reuses the request/response shape documented in
[`../SKILL.md`](../SKILL.md) and [`../api-reference.md`](../api-reference.md)
(`project/create`, `project/query/{id}`, `project/ai-social`, …) so anything
written against the real Vizard API skill is easy to point at this server
instead.

## What it does

- **Upload a file or paste a URL** (YouTube/Vimeo via `yt-dlp`, or a direct
  video link).
- **Transcribes locally** with [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
  (CPU, word-level timestamps, no cloud call).
- **Finds clip-worthy moments** with a transparent heuristic scorer (hooks,
  questions, numbers, pacing, ideal length) — see `backend/app/scoring.py`.
  It's not Vizard's proprietary model, but the reasoning behind every score
  is visible and tweakable.
- **Renders clips** with `ffmpeg`: crops/pads to 9:16, 1:1, 4:5 or keeps
  16:9, burns in styled subtitles (optionally word-by-word highlighted),
  overlays a headline hook, and can trim silence.
- **Caption fonts**: pick from a few bundled styles (`classic` / DejaVu Sans,
  `beast` / Montserrat ExtraBold, `impact` / Bebas Neue, `clean` / Roboto
  Black) via `captionFont`. Fonts are bundled in `backend/assets/fonts` and
  loaded straight from disk by ffmpeg, so the look is identical on every OS
  regardless of what's installed system-wide.
- **Smart reframe** (`smartReframeSwitch`, on by default): when cropping a
  landscape source down to a vertical/square ratio, a local OpenCV
  face-detector samples the clip, tracks the largest face's horizontal
  position over time, and pans the crop to follow it instead of using a
  fixed center crop — see `backend/app/reframe.py`. Falls back to a static
  center crop if no face is found. This is a local approximation of
  Vizard's "auto reframe" — not per-word active-speaker detection, just
  face tracking.
- **Generates a social caption + hashtags** per clip, again with a local
  heuristic instead of a cloud LLM call.

### What it deliberately doesn't do

- **No AI B-roll** — inserting relevant stock footage requires a licensed
  footage library and a matching model; out of scope for a local clone.
- **No direct publishing to social platforms** — that needs a real OAuth
  app registered with each platform. `GET /api/v1/project/social-accounts`
  is a stub that always returns no accounts; download the clips and post
  them yourself.

## Requirements

- Python 3.10+
- `ffmpeg` on your `PATH` (`apt install ffmpeg` / `brew install ffmpeg`)
- ~150 MB free for the Whisper model, downloaded once on first run from
  Hugging Face (needs internet the *first* time only; fully offline after
  that). If your network blocks `huggingface.co`, transcription will fail —
  see `WHISPER_MODEL_SIZE` below to pick a smaller/cached model.

## Run it

```bash
cd webapp
./run.sh
```

Then open http://localhost:8000.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `WHISPER_MODEL_SIZE` | `base` | faster-whisper model size: `tiny`, `base`, `small`, `medium`, `large-v3`. Bigger = more accurate, slower, larger download. |

## API

Same shape as the real Vizard API (see the repo root docs), served locally:

- `POST /api/v1/project/create` — multipart form: `file` **or** `videoUrl`
  + `videoType`, plus `lang`, `preferLength`, `ratioOfClip`, `maxClipCount`,
  `subtitleSwitch`, `headlineSwitch`, `highlightSwitch`, `removeSilenceSwitch`,
  `captionFont` (`classic` | `beast` | `impact` | `clean`).
- `GET /api/v1/project/query/{projectId}` — poll status/progress; on
  completion, `videos[]` has the same fields Vizard returns
  (`videoId`, `videoUrl`, `title`, `transcript`, `viralScore`, `viralReason`, …).
- `GET /api/v1/project/files/{projectId}/{path}` — serves rendered clips/thumbnails.
- `POST /api/v1/project/ai-social` — `{finalVideoId, aiSocialPlatform, tone, voice}`
  → generated caption + hashtags.
- `GET /api/v1/project/social-accounts` — stub, always empty (see above).

## Project layout

```
webapp/
  backend/
    app/
      main.py          FastAPI routes
      jobs.py           background pipeline orchestrator + job state
      downloader.py      yt-dlp / direct URL / upload handling
      transcription.py   faster-whisper wrapper
      scoring.py          candidate clip segmentation + viral scoring
      subtitles.py        .ass subtitle/headline generation
      ffmpeg_utils.py      ffmpeg/ffprobe wrappers (cut, crop, thumbnail)
      social.py            local caption/hashtag generator
    requirements.txt
  frontend/            plain HTML/CSS/JS UI (no build step)
  run.sh
```
