# Story 3.7: Implement /list_videos, /delete_video, and player playlist rescan

Status: done

## Story

As Dilnoza,
I want to see and remove videos from the playlist, and see new videos appear in the loop without restart,
so that video management is as fluid as people management.

## Acceptance Criteria

1. **Given** I am an allowlisted admin, **when** I send `/list_videos`, **then** the bot replies with a single message containing newline-separated filenames of all videos in `videos/`. _[FR22, NFR26]_
2. **And** when `videos/` is empty, the bot replies `No videos in playlist yet. Use /add_video to add one.`
3. **And** when I send `/delete_video <filename>`, the file is removed from `videos/` and the bot replies `<filename> removed. Playlist now has N videos`. _[FR23]_
4. **And** when I send `/delete_video <unknown>`, the bot replies `Video not found. Use /list_videos to see what is in the playlist.` and makes no filesystem change.
5. **And** when I send `/delete_video` with no argument, the bot replies `Usage: /delete_video <filename>` and makes no change.
6. **And** the player rescans the `videos/` folder at the end of each video iteration, picking up new files added via Story 3.6 within one playlist iteration (≤ 60 s for typical promo length). _[FR11, NFR5]_
7. **And** the player ignores the `videos/.tmp/` subdirectory entirely (defensive backstop — `scan_playlist` only walks top-level files, which already satisfies this).
8. **And** when a currently-playing video is deleted, playback continues to its end without error and the file is excluded from the next iteration.
9. **And** when the rescan yields an empty playlist, the player does NOT crash — it replays the last-loaded source as a degraded fallback until something is added back.
10. **And** both `/list_videos` and `/delete_video` are admin-only (FR27).

## Tasks / Subtasks

- [x] **Task 1** — `remove_video(filename, video_folder) -> bool` in `player/video_writer.py`. Basename-only, case-sensitive, returns False on missing or on directory match.
- [x] **Task 2** — `list_videos_command` in `bot.py` using `scan_playlist`. Empty → hint copy; non-empty → `"\n".join(names)`. Log `LIST_VIDEOS chat_id=… count=…`.
- [x] **Task 3** — `delete_video_command` parses everything after `/delete_video ` (multi-word filename preserved), calls `remove_video`, replies usage/not-found/count.
- [x] **Task 4** — Both handlers registered before `unknown_command` catch-all.
- [x] **Task 5** — `next_after_rescan` pure helper in `player/playlist.py`. `Player.__init__` accepts `video_folder`; `_on_media_status_changed` rescans + swaps playlist on EOM. `run_player` threads `video_folder` through.
- [x] **Task 6** — `RemoveVideoTests` (5 tests in `test_video_writer.py`): happy, missing, path-traversal sanitization, empty filename, directory not removed.
- [x] **Task 7** — `tests/test_playlist.py` (new) — 9 tests: empty fallback, current-present advance, wrap at end, current-deleted last-index clamp, last-index out-of-range, single-video wrap, `.tmp/` subdir ignored, `advance` wrap, `advance` zero-length raise.
- [x] **Task 8** — `ListVideosFlowTests` (3) + `DeleteVideoFlowTests` (5): empty/non-empty/unauthorized for list; known/multi-word/unknown/missing-arg/unauthorized for delete.
- [x] **Task 9** — Regression: 148/148 tests pass (was 126 after Story 3.6; +22 across the new test files).

## Dev Notes

### Why a pure rescan helper

The Qt-driven Player class is not test-friendly without a display. Pulling the rescan/advance decision into a pure function in `player/playlist.py` makes the contract testable in seconds and keeps `Player._on_media_status_changed` to a couple of lines.

### Why the player keeps playing on empty list

If all videos are deleted while running, crashing would defeat the kiosk promise (the screen MUST keep something on it). QMediaPlayer is already on the deleted file's content (it's a frame buffer in memory once loading completed); we just keep replaying the same source. When the admin re-adds a video, the next EOM rescan finds it and we resume rotation normally.

### Why `scan_playlist` doesn't need a `.tmp` filter change

`scan_playlist` already filters to `entry.is_file()` and skips subdirectories. The atomic-write target is `videos/.tmp/<name>` (a subdir), so it's invisible to the scanner. AC 7 is satisfied as a side effect — no code change needed; the test in Story 3.6 (`test_scan_playlist_picks_up_video_after_add`) already exercises this indirectly. Add an explicit test here to nail the contract.

### Delete-while-playing behavior

QMediaPlayer holds the source via `QUrl.fromLocalFile`. On Windows, deleting a file that's open for read can fail if any process holds an exclusive lock — but QMediaPlayer typically does not hold an exclusive lock for the duration of playback (it streams). If `remove_video` ever fails with `PermissionError`, surface it as a writer-level error and let the bot log + reply "Could not delete (file in use)". For this story, treat the happy path as: delete succeeds, the in-memory media keeps playing to EOM, the next rescan excludes the file. Failure mode is rare and demo-day deletion of a playing file is contrived.

### Reuse from earlier stories

- `scan_playlist` (Story 1.3) — single source of truth for what's in `videos/`.
- `admin_only` decorator (Story 3.2) — wrap both new handlers.
- `log_bot_event` (Story 3.3 pattern) — `LIST_VIDEOS`, `DELETE_VIDEO_*`.
- `Path.name` defensive sanitization — same pattern used in `add_video` (Story 3.6) and `delete_person` (Story 3.4).

### Out of scope

- File-watcher on `videos/` — not in the AC. The end-of-video rescan satisfies NFR5. A watcher would only matter if we needed sub-iteration latency for new videos, and the PRD explicitly accepts ≤ 60 s.
- 50-video stress test — Story 4.4 (stability shakedown) is the right home for that. We'll add a smoke assertion (`len(playlist) <= NFR21 ceiling`) only if it's cheap.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7

### Debug Log References

- 2026-05-16: Story file created from `epics.md` Story 3.7 after Story 3.6 (`/add_video`) shipped with 125 tests + mime-type fallback (126).
- 2026-05-16: Implemented player rescan via pure `next_after_rescan` helper so the contract is unit-testable without Qt; the Player class delegates to it on every `EndOfMedia`.

### Completion Notes List

- Rescan happens at EOM only (NFR5 accepts ≤ 60 s for typical promo length) — no extra timer, no file-watcher. The pure helper keeps the rescan/advance decision testable in isolation; the Player just plumbs `current_path`, `last_index`, and the freshly scanned list into it.
- Empty-rescan fallback returns `([current_path], 0)` so QMediaPlayer reloads the same source and the screen never goes blank. When admin re-adds a video, the next EOM picks it up and rotation resumes.
- `remove_video` is intentionally simple — direct `Path.unlink()` — and refuses to remove directories. Path-traversal payloads are reduced to basename, mirroring `add_video`'s `target_filename` defense.
- `delete_video_command` uses the same `text.split(maxsplit=1)` trick as `delete_person_command` so multi-word filenames like `my promo.mp4` survive intact.
- Test suite: 148/148 (was 126 after the 3.6 mime fallback; +5 remove_video + 9 playlist + 8 bot flow).

### File List

- `player/video_writer.py` (modified — added `remove_video`)
- `player/playlist.py` (modified — added `next_after_rescan`)
- `player/main.py` (modified — `Player` accepts `video_folder`; `_on_media_status_changed` rescans on EOM; `run_player` threads it through)
- `bot.py` (modified — `list_videos_command`, `delete_video_command`, handler registration, `remove_video` import)
- `tests/test_video_writer.py` (modified — `RemoveVideoTests`)
- `tests/test_playlist.py` (new — `NextAfterRescanTests`, `ScanPlaylistTmpFilterTests`, `AdvanceTests`)
- `tests/test_bot.py` (modified — `ListVideosFlowTests`, `DeleteVideoFlowTests`)
- `_bmad-output/implementation-artifacts/3-7-implement-list-videos-delete-video-and-player-playlist-rescan.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 3.7 created from epics.md, status set to ready-for-dev.
- 2026-05-16: Implemented `/list_videos` + `/delete_video` + player end-of-video rescan; 148/148 tests pass; status set to done. Epic 3 complete.
