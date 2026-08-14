# Vizard API Skills 🎬

**Vizard.ai API Skills** provides a comprehensive set of tools and specifications to automate the transformation of long-form video content into viral short-form clips for platforms like TikTok, YouTube Shorts, and Instagram Reels.

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
- `skills/ui-ux-pro-max/`: Bundled UI/UX design intelligence skill (see below).

## 🎨 Bundled Skill: UI/UX Pro Max

`skills/ui-ux-pro-max/` adds an offline design-intelligence skill that pairs well with the video workflow above — use it to design the landing pages, dashboards, and player UIs that surround your generated clips.

It ships a fully local, searchable catalog (no network calls, no API key):

- 79 searchable UI styles (50 active), 192 product palettes with reasoning profiles
- 74 Google Fonts pairings, 119 UX guidelines, 105 curated icons
- 17 GSAP motion presets, 25 chart types, and 22 technology stacks (React, Vue, Svelte, Astro, Laravel, SwiftUI, Jetpack Compose, Flutter, React Native, WPF, JavaFX, and more)

### Install

Copy the skill folder into your agent's skills directory:

```bash
# Claude Code — project-local
mkdir -p .claude/skills
cp -R skills/ui-ux-pro-max .claude/skills/

# Claude Code — global
cp -R skills/ui-ux-pro-max ~/.claude/skills/
```

Cursor, Windsurf, and other agents use the same layout under their own root (`.cursor/`, `.windsurf/`, …).

### Use

Once installed the skill activates on its own for UI work. You can also drive the search engine directly:

```bash
# Generate a full design system for a product
python3 skills/ui-ux-pro-max/scripts/search.py "beauty spa" --design-system -p "Serenity Spa"

# Plain catalog search
python3 skills/ui-ux-pro-max/scripts/search.py "dashboard"
```

**Requires Python 3.x** (standard library only). Verify the bundled data with `python3 skills/ui-ux-pro-max/scripts/validate_data.py`.

### Attribution

UI/UX Pro Max is vendored from [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) and is licensed MIT (© Next Level Builder). The upstream license is preserved at `skills/ui-ux-pro-max/LICENSE`. For updates, the marketplace or CLI install is the canonical path:

```
/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
/plugin install ui-ux-pro-max@ui-ux-pro-max-skill
```

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
