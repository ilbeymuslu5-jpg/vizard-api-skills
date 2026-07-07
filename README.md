# Vizard API Skills 🎬

**Vizard.ai API Skills** provides a comprehensive set of tools and specifications to automate the transformation of long-form video content into viral short-form clips for platforms like TikTok, YouTube Shorts, and Instagram Reels.

> **New:** [`webapp/`](./webapp) contains a self-hosted local clone of the
> Vizard.ai workflow — upload/URL → local Whisper transcription → heuristic
> clip scoring → subtitle-burned vertical clips — with no API key or cloud
> service required. See [`webapp/README.md`](./webapp/README.md) to run it.

This is a universal skill set compatible with all major AI agents and developer tools, including **OpenClaw**, **Claude Code**, **OpenCode**, and **Cursor**. It provides a standardized way for any AI agent to automate professional video workflows.

By leveraging AI, this skill allows developers and AI agents to identify high-engagement moments, apply professional edits automatically, and handle social media publishing—all via a streamlined REST API.

## 🚀 Core Capabilities

### 1. AI Video Clipping (Long $\rightarrow$ Short)
Turn long videos into a series of short, punchy clips optimized for engagement.
- **Multi-Source Input:** Support for YouTube, Google Drive, Vimeo, and direct file uploads.
- **Viral Scoring:** AI automatically ranks clips by their potential to go viral.
- **Length Control:** Specify preferred clip durations (e.g., <30s, 60-90s).

### 2. AI Video Enhancement (Short $\rightarrow$ Enhanced)
For videos under 3 minutes, apply a "Pro Editor" pass:
- **Auto-Subtitles & Headlines:** Automatically generate and style captions to increase retention.
- **AI B-Roll:** Seamlessly insert relevant stock footage based on the transcript.
- **Silence Removal:** Clean up audio by removing dead air and filler words.
- **Format Optimization:** Instant conversion to 9:16, 1:1, or 4:5 ratios.

### 3. Social Automation
- **AI Caption Generation:** Create platform-specific captions and hashtags (TikTok, LinkedIn, etc.) based on the video's tone and voice.
- **Direct Publishing:** Push finished clips directly to connected social media accounts.

## 🛠 Technical Workflow

The API follows an asynchronous processing pattern:

`Submit Project` $\rightarrow$ `Poll for Results` $\rightarrow$ `Download / Publish`

1.  **Submission**: Send a request to `/project/create`. You can choose between **Clipping Mode** (for long videos) or **Editing Mode** (for short enhancements).
2.  **Polling**: Since AI processing takes time, poll the `/project/query/{projectId}` endpoint every 30 seconds until you receive a success code (`2000`).
3.  **Finalization**: Once complete, use the generated `videoId` to generate social captions or publish the content.

## 📂 Repository Structure

- `SKILL.md`: High-level guide and prompt instructions for AI Agents.
- `api-reference.md`: Detailed technical documentation including all endpoints, parameters, and status codes.

## 🚀 Quick Start (Example)

**Base URL:** `https://elb-api.vizard.ai/hvizard-server-front/open-api/v1`  
**Auth Header:** `VIZARDAI_API_KEY: YOUR_API_KEY`

```python
# Submit a YouTube video for clipping
import requests

headers = {"VIZARDAI_API_KEY": "YOUR_API_KEY", "Content-Type": "application/json"}
payload = {
    "videoUrl": "https://www.youtube.com/watch?v=XXXXX",
    "videoType": 2, # YouTube
    "lang": "en"
}

response = requests.post("https://elb-api.vizard.ai/hvizard-server-front/open-api/v1/project/create", headers=headers, json=payload)
print(f"Project ID: {response.json()['projectId']}")
```

---
*For more detailed parameter tables and status codes, please refer to [api-reference.md](./api-reference.md).*
