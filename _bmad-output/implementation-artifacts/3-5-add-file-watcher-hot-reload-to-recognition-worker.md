# Story 3.5: Add file-watcher hot-reload to recognition worker

Status: done

## Story

As Dilnoza,
I want a person I just added (via Telegram or CLI) to be recognized the next time they walk past the camera, and a person I just removed to stop being greeted,
so that my admin actions take effect immediately without restarting the system (Journey 4 climax).

## Acceptance Criteria

1. **Given** the recognition worker (Story 2.3) is running, **when** `people.json` is modified by any writer (bot from Story 3.3, `/delete_person` from Story 3.4, CLI from Epic 4, or manual edit), **then** the worker reloads its in-memory `Registry` within 5 seconds (FR18, NFR4).
2. **And** the next camera frame containing the newly-added person triggers a `MATCH:` line and a greeting queue event (FR18 end-to-end).
3. **And** when a person is removed, the worker drops them from its in-memory `Registry` within 5 seconds; subsequent walk-pasts produce no greeting for that person (FR19).
4. **And** partial-write states are handled: Story 2.2's writer guarantees atomic `os.replace`, so the watcher only ever observes valid post-replace states; the reloader does NOT need to retry on `JSONDecodeError` from a half-written file.
5. **And** a malformed `people.json` (e.g., manual hand-edit error) is logged to stderr (which the supervisor routes to `logs/worker.log`) and the previous valid `Registry` is retained — the worker does NOT crash.
6. **And** the worker continues to honor `stop_event` cleanly during and after a reload — the watcher thread is stopped during shutdown so no zombie threads remain.

## Tasks / Subtasks

- [x] **Task 1** — Added `recognition/hot_reload.py` with `PeopleRegistryReloader` (watches parent dir, filters by basename, `threading.Event` flag, idempotent `stop()`, auto-creates missing parent dir).
- [x] **Task 2** — Added `tests/test_hot_reload.py` with 7 tests covering modification, atomic replace, clear-pending, unrelated-file noise filter, idempotent stop, missing-parent-dir handling, and the `request_reload` test hook.
- [x] **Task 3** — `worker.run` builds + starts the reloader, checks `reload_pending` at the top of each loop iteration (clear-first, then `load_registry`), logs `REGISTRY_RELOADED count=<N>` on success and `REGISTRY_RELOAD_FAILED <type>: <msg>` to stderr on failure (keeping the old registry). Reloader is stopped in `finally` before `cap.release()`.
- [x] **Task 4** — Added 3 worker integration tests using a `_FakeReloader` (no real watchdog thread): swap-on-reload, malformed-JSON-keeps-old-registry, reloader-stopped-on-shutdown.
- [x] **Task 5** — Regression: 109/109 tests pass (was 99 after Story 3.4; added 7 hot-reload + 3 worker integration).

## Dev Notes

### Architecture compliance

- **AR7 — IPC and observability:** `watchdog.Observer` lives in the worker process, not the player or bot. Each writer (bot, CLI) just writes atomically; the worker is the only consumer of file events.
- **NFR4 — DB hot-reload propagation ≤ 5 s:** With a 0.01 s loop sleep on empty and `recognize_dual` running every frame, the reload check at loop top means propagation is effectively bounded by one camera-frame cycle (~33 ms at 30 fps) plus watchdog's event dispatch (~tens of ms). 5 s is a comfortable upper bound.
- **NFR11 — no on-screen artifact from internal events:** The reload happens in the worker; the player is unaware. Greeting events continue to flow over the existing `multiprocessing.Queue`. No new IPC.

### Why a flag, not a direct reload in the handler

watchdog dispatches events on its own thread. Calling `load_registry` from the handler thread races with the main loop's reads of `registry`. Setting a flag and reloading from the main loop is single-writer for `registry`, no locks needed.

Order of operations matters: **clear the flag BEFORE calling `load_registry`**. If we clear after, and a second write lands during the read, we lose that second write's notification. With clear-first, the worst case is one redundant reload — harmless.

### Atomic-write guarantee removes the partial-read risk

Story 2.2's writer goes `write to .tmp → fsync → os.replace`. On Windows, `os.replace` is atomic at the file-system level (same volume), and watchdog won't fire `on_modified` for the .tmp file (it's not the watched name). It fires for the target after the replace, by which point the file is fully written. So `JSONDecodeError` from `load_registry` indicates a genuine schema problem (manual edit), not a race — log loudly, do not retry.

### What `watchdog` event types to listen for

`os.replace` on Windows generates `on_moved` (with the temp as src and the target as dest). On POSIX it can generate `on_created` for the new target and `on_modified` separately depending on the FS. Hooking all three (`on_modified`, `on_created`, `on_moved`) and filtering by filename is the safe option. The filter compares against `people_db_path.name` (basename).

### Pattern reference — recognition/writer.py

```python
def _atomic_write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    ...
    os.replace(tmp, path)
```

So the path being watched is `people.json`; the temp `people.json.tmp` is the only intermediate. Filter handler events to `event.dest_path.name == "people.json"` (for moves) or `event.src_path.name == "people.json"` (for modified/created).

### Out of scope

- Hot-reload of `config.yaml` — out of scope; config is read once at worker boot.
- Hot-reload of `videos/` — Story 3.7 handles playlist rescan in the player.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7

### Debug Log References

- 2026-05-16: Story file created from `epics.md` Story 3.5 after Story 3.4 (`/list_people` + `/delete_person`) shipped with 99/99 tests passing.
- 2026-05-16: Implemented reloader + worker integration. `watchdog==6.0.0` was already pinned in `requirements.txt` but was not yet installed in the smoke venv (`.venv-smoke-dlib-corrected`); `pip install watchdog==6.0.0` brought the venv in line with the pin.

### Completion Notes List

- `PeopleRegistryReloader` watches the parent directory of `people.json` (watchdog observes dirs, not single files) and filters events by basename so writes to `people.json.tmp` or unrelated noise in the same folder do not trigger reloads — only the post-`os.replace` target does.
- The handler subscribes to `on_modified`, `on_created`, and `on_moved`. `os.replace` produces `on_moved` on Windows (src=temp, dest=target); covering all three event types is the safe cross-platform option.
- Worker loop is single-writer for `registry`: handler thread only sets the flag, main loop clears the flag *first* and then calls `load_registry`. Clear-first guarantees that a second write arriving during the read is not lost (worst case: one redundant reload).
- Malformed JSON → caught at `load_registry` (raises `ValueError`), logged as `REGISTRY_RELOAD_FAILED ValueError: <msg>` to stderr, old registry retained. Worker keeps running.
- `reloader.stop()` is called in `finally` before `cap.release()` so the watchdog observer thread is joined cleanly on supervisor shutdown — no zombie threads on Ctrl+C.
- The reloader auto-creates the parent dir on `start()` if missing — useful for clean clones where the worker spins up before any writer has touched `people.json`.
- Test suite: 109/109 (was 99 at end of 3.4).

### File List

- `recognition/hot_reload.py` (new — `PeopleRegistryReloader`)
- `recognition/worker.py` (modified — import + start/stop + reload check at top of loop)
- `tests/test_hot_reload.py` (new — 7 reloader unit tests)
- `tests/test_worker.py` (modified — `_FakeReloader`, 3 integration tests; added `json` import)
- `_bmad-output/implementation-artifacts/3-5-add-file-watcher-hot-reload-to-recognition-worker.md` (this story)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status)

## Change Log

- 2026-05-16: Story 3.5 created from epics.md, status set to ready-for-dev.
- 2026-05-16: Implemented `PeopleRegistryReloader` + worker integration; 109/109 tests pass; status set to done.
