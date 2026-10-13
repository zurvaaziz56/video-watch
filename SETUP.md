# Video Watch — installation (for Claude Code to follow)

Mac only. Show the user each install command and wait for their OK before running it. Read the scripts in `scripts/` before running them.

1. **Check the machine.** Confirm this is macOS (`sw_vers`). If it isn't, stop and tell the user this package is Mac-only.
2. **Homebrew.** Run `brew --version`. If Homebrew is missing, do not install it yourself — give the user the official command from https://brew.sh to run in Terminal (it asks for their password), then continue.
3. **Tools.** `brew install yt-dlp ffmpeg whisper-cpp` — then confirm `yt-dlp --version`, `ffmpeg -version` and `whisper-cli -h` work.
4. **Speech model (547 MB, one-time).**
   ```
   mkdir -p ~/.local/share/whisper
   curl -L --fail -o ~/.local/share/whisper/ggml-large-v3-turbo-q5_0.bin \
     https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin
   shasum -a 256 ~/.local/share/whisper/ggml-large-v3-turbo-q5_0.bin
   ```
   The checksum must be `394221709cd5ad1f40c46e6031ca61bce88931e6e088c188294c6d5a55ffa7e2` (size 574,041,195 bytes). If it doesn't match, delete the file and stop.
5. **Install the skill (user-level, so it works in every project).** Unzip the package so the folder ends up at `~/.claude/skills/video-watch/` (containing `SKILL.md`, `SETUP.md`, `scripts/`, `references/`). If a `video-watch` skill already exists there, ask before replacing it.
6. **Notes folder.** Ask the user where notes should go (default `~/Documents/Video Notes`). Create it, then write the path into `~/.local/share/video-watch/notes_dir.txt`.
7. **Check.** `python3 ~/.claude/skills/video-watch/scripts/watch.py --check` → must print `ready`.
8. **Test on a public reel** (a test reel used by yt-dlp's own developers):
   `python3 ~/.claude/skills/video-watch/scripts/watch.py "https://www.instagram.com/reel/CDUMkliABpa/"`
   Read one frame, then run `--cleanup` on the work dir it printed and confirm `deleted`. Expected: about 10–20 seconds, a caption, a short transcript (it's music) and ~7 frames.
9. **iPhone share button.** Run `python3 ~/.claude/skills/video-watch/scripts/inbox.py setup` (creates the Reminders list "Reels for Claude"; macOS asks once to let the app control Reminders — allow it). Then show the user the one-shot prompt and the three checks in `references/iphone-share-button.md`. When the user has saved a first link, run `inbox.py status` and confirm it arrived.
10. **Reading List lane (optional).** `inbox.py status` shows how many video links Safari's Reading List holds. If reading it fails with a permission error, either skip this lane or have the user give the Claude app Full Disk Access (System Settings → Privacy & Security → Full Disk Access).

Finish by telling the user, in plain words, how to use it: paste a link, or save reels with the button and say "go through my reels".
