# Story 4.2: Build add_video.py CLI fallback

Status: done

## Story

As Sanji,
I want a CLI script that adds a video to the playlist without going through Telegram and without any file-size limit,
so that I can ship large promo videos (>20 MB) and operate offline (Journey 5).

## Acceptance Criteria

1. **Given** the shared atomic-video-writer pattern from Story 3.6 exists and the player rescans `videos/` at end-of-iteration (Story 3.7), **when** I run `python add_video.py path/to/promo.mp4`, **then** the script atomically copies the file to `videos/<filename>` and prints `Added: <filename>. Playlist now has N videos.` and exits 0. _[FR21, NFR18, AR9]_
2. **And** the player picks up the new video at end of the current playback iteration within ≤ 60 s for typical promo length. _[FR21, NFR5]_
3. **And** files of any size are accepted — no 20 MB limit (this is the explicit reason the CLI exists alongside the bot). _[NFR22]_
4. **And** when the file path does not exist, prints `Error: video file not found: <path>` and exits non-zero.
5. **And** when the file is not a recognised video extension (`.mp4` / `.mov` / `.webm`), prints `Error: unsupported video format: <ext>. Use .mp4, .mov, or .webm.` and exits non-zero.
6. **And** the script works completely offline with no network calls. _[FR21, FR31, NFR13]_

## Tasks / Subtasks

- [ ] **Task 1 — Create `add_video.py`** at repo root mirroring `add_person.py`'s shape: parse argv, resolve `video_folder` from config, call `player.video_writer.add_video`, translate errors to messages + exit codes.
- [ ] **Task 2 — Exit codes**:
  - `0` — success.
  - `1` — usage error.
  - `2` — operational error (missing source, unsupported extension).
- [ ] **Task 3 — Tests** in `tests/test_add_video_cli.py`:
  - Happy path: real file copied via writer, stdout has `Added: <filename>. Playlist now has N videos.`, exit 0.
  - Missing args → usage on stderr, exit 1.
  - Missing source file → "video file not found" on stderr, exit 2.
  - Unsupported extension → format error on stderr, exit 2.
- [ ] **Task 4 — Regression** — full suite green (was 154/154 after Story 4.1).

## Dev Notes

### Reuse from Stories 3.6 + 3.7

- `player.video_writer.add_video(source, video_folder)` — atomic write.
- `player.video_writer.UnsupportedVideoFormatError` — extension validation.
- `player.playlist.scan_playlist` — count after write for the reply.
- `bot.load_config` — single config-reading code path.

Same pattern as `add_person.py`; the CLI is just argv parsing + exception translation.

### No size check

Telegram-only constraint. The CLI exists explicitly to bypass it (NFR22, NFR27). Don't add a check.

### Out of scope

- Bulk add multiple videos in one command — not required.
- Conversion / re-encoding — out of scope.

## Dev Agent Record

### Agent Model Used

_TBD_

### Debug Log References

- 2026-05-16: Story file created after Story 4.1 (`add_person.py` CLI) shipped with 154/154 tests passing.

### Completion Notes List

_To be filled by dev agent._

### File List

_Expected:_

- `add_video.py` (new)
- `tests/test_add_video_cli.py` (new)
- `_bmad-output/implementation-artifacts/4-2-build-add-video-py-cli-fallback.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 4.2 created from epics.md, status set to ready-for-dev.
