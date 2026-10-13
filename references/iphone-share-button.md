# "Send to Claude" share button — iPhone setup

One-time setup, about 3 minutes, free (Apple Shortcuts). Afterwards any reel or video link can be saved for Claude with two taps, and Claude goes through them when you say "go through my reels".

## Build it with one prompt (updated 2026-10-03: Reminders, not a file)

First, on the Mac, ask Claude to run `inbox.py setup` — it creates the Reminders list **Reels for Claude**, which syncs to the iPhone. The shortcut saves each link there because Reminders sync in seconds, while a text file written by a share-sheet shortcut can sit on the phone as "↑ Waiting…" for hours.

In the Shortcuts app, create a **new** shortcut with the describe-it (AI) feature and paste this exactly:

```
Create a new shortcut named "Send to Claude" that works from the Share Sheet.

1. Receive input from the Share Sheet. Accept URLs, Safari web pages and text.
2. If there is no input, get the current clipboard instead.
3. Add that input as a new reminder in the Reminders list named "Reels for Claude". The reminder's title is the input.
4. Show a notification that says "Saved for Claude ✓".

Do not open any app or website, do not ask me any questions while it runs, and do not send the input anywhere else.
```

Then open the shortcut's edit screen and check three things:
1. The top block says *Receive … from* **Share Sheet** (not "Nowhere").
2. The **Add New Reminder** step uses the input (If Result) as the reminder and the list **Reels for Claude**.
3. Run it once: the link appears in the Reminders app under Reels for Claude.

## Use it

- **Instagram:** tap the paper-plane **Share** icon → **Share to…** / **More** (opens the iPhone share menu) → scroll to **Send to Claude**.
- **YouTube, Safari, TikTok, X:** Share → **Send to Claude**.
- **Fallback:** tap **Copy link**, then run *Send to Claude* from the Shortcuts app — it reads the clipboard.

Check it worked: the **Reminders** app → **Reels for Claude** shows the link. Then, on the Mac, tell Claude **"go through my reels"**.

## Manual build (if the prompt version misbehaves)

1. Shortcuts → **+** → name it `Send to Claude`.
2. Settings (**ⓘ** or the name at the top) → turn on **Show in Share Sheet**; accept **URLs** and **Text**; if there's no input → **Get Clipboard**.
3. Add **Add New Reminder**: reminder = **Shortcut Input** (or the If Result variable), list = **Reels for Claude**.
4. Optional: **Show Notification** → `Saved for Claude ✓`.

## Lessons (from building the first one)

- Create the shortcut with ONE complete prompt. "Describe a change" on a working shortcut can rebuild it from scratch and lose what worked.
- The iPhone creates `reels.txt`; the Mac only reads it. A file made on the Mac could not be opened by the phone's shortcut ("The file reels.txt couldn't be opened"). Fix: delete that file and run the shortcut again.
- Keep the file at the top of iCloud Drive › Shortcuts (no subfolders).
- A run with nothing shared falls back to the clipboard, so stray text can land in the file — harmless, because the Mac only picks out links.
- Nothing is sent anywhere except your own iCloud Drive; Instagram is never logged into. Private-account reels can't be opened without a login, so Claude skips those and says so.
