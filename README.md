# video-watch

A Claude Code skill that "watches" Instagram Reels, YouTube videos and other video links locally on a Mac, then explains what they teach and files a short text note.

It downloads the video to a temporary folder without logging in or using cookies. It pulls about 20 still frames and makes a timestamped transcript on-device with [whisper.cpp](https://github.com/ggml-org/whisper.cpp). Claude reads the frames and transcript, and then **all media is deleted before Claude replies**. Nothing is uploaded to any transcription service.

## The problem it solves

Saved reels pile up: tutorials, tool demos, hackathon announcements, formats worth borrowing. Watching them again to pull out the one useful thing takes longer than the reel itself. This turns "watch this" into a short explanation, an online check of the claims, and a sorted note: build idea, opportunity to apply for, content idea, something to learn, or skip.

## What's in it

| Path | What it is |
|---|---|
| `SKILL.md` | The skill definition Claude Code reads: trigger phrases, pipeline, rules |
| `SETUP.md` | Step-by-step install guide written for a Claude Code session to follow |
| `scripts/watch.py` | Download → frames → transcript → cleanup (`--check`, `--frames`, `--translate`, `--cleanup`, `--sweep`) |
| `scripts/inbox.py` | Batch inbox: collects video links shared from an iPhone (a share-sheet Shortcut, or Safari's Reading List) |
| `references/iphone-share-button.md` | How to set up the iPhone "Send to Claude" share button |
| `references/source-note-template.md` | The format of the text note written after each video |

## Stack

Python 3 (standard library) · `yt-dlp` · `ffmpeg` · `whisper-cpp` with the `ggml-large-v3-turbo-q5_0` model (checksum-verified during setup) · Claude Code.

## Setup

Open Claude Code in this folder and ask it to follow `SETUP.md`. In short:

```bash
brew install yt-dlp ffmpeg whisper-cpp
python3 scripts/watch.py --check
```

`SETUP.md` covers downloading the whisper model and verifying its SHA-256, choosing a notes folder, installing the skill at user level, testing with one public reel, and the optional iPhone button.

## Usage

Paste a video link into Claude Code ("watch this: <link>"), or say "go through my reels" to process the inbox.

## Privacy and limits

- No accounts, no cookies, and no `--cookies-from-browser`. Private or login-only videos are out of scope.
- Media lives only in a temporary folder and is removed with `--cleanup` before the reply; `--sweep` clears leftovers.
- macOS only (Homebrew tools, Apple Shortcuts / Safari Reading List inbox).
- Long videos are summarised from at most about 24 frames plus the full transcript, so purely visual detail can be missed.

Built with Claude Code.
