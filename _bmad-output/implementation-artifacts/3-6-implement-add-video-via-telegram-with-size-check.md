# Story 3.6: Implement /add_video via Telegram with size check

Status: done

## Story

As Dilnoza (Journey 4b),
I want to push a new promo video from my phone by sending the file to the bot,
so that the office display can update content without me touching the laptop.

## Acceptance Criteria

1. **Given** I am an allowlisted admin, **when** I send `/add_video`, **then** the bot replies `Send me the video file`. _[NFR26]_
2. **And** when I send a video file ≤ 20 MB, the bot downloads the file, atomically copies it into `videos/<filename>` (write to `videos/.tmp/<filename>`, then `os.replace`), and replies `<filename> added. Playlist now has N videos`. _[FR20, NFR17, NFR18, AR9]_
3. **And** when I send a video file > 20 MB, the bot replies `This video is over 20 MB. Please upload it via add_video.py on the laptop.` and does not download or write the file. _[FR25, NFR22, NFR27]_
4. **And** when the file is not a supported video format (`.mp4`, `.mov`, `.webm`), the bot replies `That file format is not supported. Please use .mp4, .mov, or .webm.` and does not write to `videos/`.
5. **And** the round-trip from `/add_video` to confirmation is < 60 s for a sub-20 MB video. _[NFR24]_
6. **And** both `/add_video` and the video handler are admin-only — non-allowlisted chats receive `Unauthorized` before any download or write.

## Tasks / Subtasks

- [x] **Task 1** — Added `player/video_writer.py` with `add_video`, `SUPPORTED_VIDEO_EXTENSIONS`, `UnsupportedVideoFormatError`, atomic copy via `.tmp/` + `os.replace`, auto-creates folders, optional `target_filename` override (basename-only for path-injection safety).
- [x] **Task 2** — `player/playlist.py` now imports `VIDEO_EXTENSIONS` from `player.video_writer.SUPPORTED_VIDEO_EXTENSIONS` (single source of truth: `.mp4`, `.mov`, `.webm`).
- [x] **Task 3** — `bot.py`: `add_video_command` (sets pending, replies prompt) and `handle_video_message` (admin-only; pre-download size check against `TELEGRAM_VIDEO_MAX_BYTES = 20 MB`; pre-download extension check; interim `Video received. Processing...` reply; `ADD_VIDEO_*` log events).
- [x] **Task 4** — Handler registration adds `/add_video` + `filters.VIDEO` handler; `bot_data` now seeds `pending_add_video = {}` and `video_folder`.
- [x] **Task 5** — `AddVideoFlowTests` (7 tests): command prompt, happy path with playlist count, oversized reject, unsupported extension, missing filename, pending-state required, unauthorized blocked.
- [x] **Task 6** — `tests/test_video_writer.py` (9 tests): happy path, dir auto-creation, tmp cleanup, unsupported extension, missing source, overwrite, target-filename basename safety, extension-set parity with playlist, scan-picks-it-up.
- [x] **Task 7** — Regression: 125/125 tests pass (was 109 at end of 3.5; +16 across the two new test files).

## Dev Notes

### Why a separate writer module

Story 4.2 builds `add_video.py` CLI. AR9 says the bot and CLI must use a single code path — the lesson from `recognition/writer.py` applies here too. Creating `player/video_writer.py` now means the CLI in Epic 4 is a 10-line wrapper.

### Atomic write pattern

Same shape as `recognition.writer._atomic_write_json`, adapted for binary file copy:

```python
def add_video(source_path: Path, video_folder: Path) -> Path:
    source_path = Path(source_path)
    video_folder = Path(video_folder)
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    suffix = source_path.suffix.lower()
    if suffix not in SUPPORTED_VIDEO_EXTENSIONS:
        raise UnsupportedVideoFormatError(suffix)
    tmp_dir = video_folder / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    filename = source_path.name
    tmp_path = tmp_dir / filename
    final_path = video_folder / filename
    shutil.copyfile(source_path, tmp_path)
    os.replace(tmp_path, final_path)
    return final_path
```

`os.replace` works across `videos/.tmp/` → `videos/` because they're on the same volume.

### Supported extensions — single source of truth

Add a `SUPPORTED_VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".webm"})` constant in `player/video_writer.py`. Update `player/playlist.py` `VIDEO_EXTENSIONS` to import from there (or share). Pick one home; Story 3.7 will then rely on the same set when iterating the playlist.

### Telegram size check happens BEFORE download

`update.message.video.file_size` is reported by Telegram in the message metadata — we have it without downloading. Check it first; reject loudly. Only when ≤ 20 MB do we call `context.bot.get_file(...).download_to_drive(...)`. This satisfies NFR24 (< 60 s) trivially — no wasted bandwidth on oversized files.

The 20 MB constant should be a module-level `TELEGRAM_VIDEO_MAX_BYTES = 20 * 1024 * 1024` for readability and easy testing.

### Filename hygiene

`video.file_name` from Telegram can be `None` (some clients omit it). Fall back to `<file_id>.<ext-from-mime-or-default>`. Strip any path components defensively — `Path(name).name` collapses anything sneaky. Tests should cover the `file_name=None` case.

### Filter setup for python-telegram-bot

Register the video handler with `MessageHandler(filters.VIDEO, handle_video_message)` (mirrors the existing `filters.PHOTO` handler). Register it before the catch-all `MessageHandler(filters.COMMAND, unknown_command)` and after the photo handler for ordering parity with Story 3.3.

### Out of scope

- `/list_videos`, `/delete_video`, and the player's runtime playlist rescan are Story 3.7.
- CLI fallback `add_video.py` is Story 4.2.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7

### Debug Log References

- 2026-05-16: Story file created from `epics.md` Story 3.6 after Story 3.5 (hot-reload) shipped with 109/109 tests passing.
- 2026-05-16: Implemented writer + bot flow. Made `player/playlist.VIDEO_EXTENSIONS` a re-export of `player.video_writer.SUPPORTED_VIDEO_EXTENSIONS` to keep a single source of truth (NFR consistency between what the writer accepts and what the player will play).

### Completion Notes List

- `player/video_writer.py` reuses the `os.replace` atomic pattern from `recognition.writer._atomic_write_json` but for binary file copy: `shutil.copyfile` to `<video_folder>/.tmp/<filename>`, then `os.replace` to `<video_folder>/<filename>`. Both folders are auto-created.
- `target_filename` parameter takes basename only (`Path(target_filename).name`) so even a path-traversal-shaped string like `../escape/clean.mp4` resolves to `clean.mp4` inside the configured `video_folder`. Defensive guard for the bot path even though the bot already sanitizes via `Path(file_name).name`.
- Bot rejects oversized and unsupported-extension videos BEFORE calling `get_file` so no bandwidth is wasted (NFR24).
- `Video received. Processing...` interim reply follows the Story 3.3 operator-instinct lesson — visible progress, no silent waits.
- `pending_add_video` state is per-chat (matching `pending_add_person`); cleared on success, reject, and error paths.
- Test suite: 125/125 (was 109 after Story 3.5; +9 writer + 7 bot flow tests).
- Note for live test: a Telegram client might send a video as a *document* rather than a *video* attachment (Telegram differentiates compressed vs uncompressed video uploads). This story matches AC verbatim — `filters.VIDEO` only. If live test reveals iOS users uploading as documents by default, Story 3.7 work or a follow-up can broaden the filter.

### File List

- `player/video_writer.py` (new)
- `player/playlist.py` (modified — `VIDEO_EXTENSIONS` re-exports from `video_writer`)
- `bot.py` (modified — `add_video_command`, `handle_video_message`, registration, `PENDING_ADD_VIDEO_KEY` and `TELEGRAM_VIDEO_MAX_BYTES` constants)
- `tests/test_bot.py` (modified — added `_FakeVideo`, video kwarg to `_FakeUpdate`, `AddVideoFlowTests`)
- `tests/test_video_writer.py` (new)
- `_bmad-output/implementation-artifacts/3-6-implement-add-video-via-telegram-with-size-check.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 3.6 created from epics.md, status set to ready-for-dev.
- 2026-05-16: Implemented `player/video_writer.py` + `/add_video` bot flow; 125/125 tests pass; status set to done.
