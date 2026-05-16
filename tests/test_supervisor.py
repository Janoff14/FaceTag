"""Tests for Story 3.1 supervisor lifecycle helpers."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import supervisor


class TestBotProcess(unittest.TestCase):
    def test_bot_process_redirects_logs_and_stays_alive_until_shutdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp)
            bot_script = log_dir / "fake_bot.py"
            bot_script.write_text(
                "import time\nprint('BOT_READY test', flush=True)\ntime.sleep(30)\n",
                encoding="utf-8",
            )
            handle = supervisor.start_bot_process(
                log_dir,
                python_executable=sys.executable,
                repo_root=log_dir,
                bot_script=bot_script,
            )
            try:
                ready = supervisor.wait_for_log_text(log_dir / "bot.log", "BOT_READY test", timeout_s=5)
                self.assertTrue(ready)
                self.assertIsNone(handle.process.poll())
            finally:
                supervisor.stop_bot_process(handle)
            self.assertIsNotNone(handle.process.poll())


class _FakeWorkerHandle:
    def __init__(self, exitcode):
        self.stop_event = mock.Mock()
        self.process = mock.Mock()
        self.process.exitcode = exitcode


class _FakeBotHandle:
    def __init__(self, returncode):
        self.process = mock.Mock()
        self.process.poll.return_value = returncode
        self.log_handle = mock.Mock()


class TestComponentSupervisor(unittest.TestCase):
    def test_tick_restarts_failed_worker_without_touching_bot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp)
            sup = supervisor.ComponentSupervisor(
                config={"log_directory": str(log_dir)},
                greeting_queue=mock.Mock(),
                debug_camera_queue=None,
                start_monitor_thread=False,
            )
            failed_worker = _FakeWorkerHandle(exitcode=1)
            sup.worker = failed_worker
            sup.bot = _FakeBotHandle(returncode=None)
            replacement = _FakeWorkerHandle(exitcode=None)

            with mock.patch.object(supervisor, "stop_recognition_worker") as stop_worker, \
                 mock.patch.object(supervisor, "start_recognition_worker", return_value=replacement) as start_worker, \
                 mock.patch.object(supervisor, "stop_bot_process") as stop_bot, \
                 mock.patch.object(supervisor, "start_bot_process"):
                sup.tick()

            stop_worker.assert_called_once_with(failed_worker)
            start_worker.assert_called_once()
            stop_bot.assert_not_called()
            self.assertIs(sup.worker, replacement)
            self.assertIn("Restarting worker", (log_dir / "supervisor.log").read_text(encoding="utf-8"))

    def test_tick_restarts_failed_bot_without_touching_worker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp)
            sup = supervisor.ComponentSupervisor(
                config={"log_directory": str(log_dir)},
                greeting_queue=mock.Mock(),
                debug_camera_queue=None,
                start_monitor_thread=False,
            )
            sup.worker = _FakeWorkerHandle(exitcode=None)
            failed_bot = _FakeBotHandle(returncode=7)
            sup.bot = failed_bot
            replacement = _FakeBotHandle(returncode=None)

            with mock.patch.object(supervisor, "stop_recognition_worker") as stop_worker, \
                 mock.patch.object(supervisor, "start_recognition_worker"), \
                 mock.patch.object(supervisor, "stop_bot_process") as stop_bot, \
                 mock.patch.object(supervisor, "start_bot_process", return_value=replacement) as start_bot:
                sup.tick()

            stop_worker.assert_not_called()
            stop_bot.assert_called_once_with(failed_bot)
            start_bot.assert_called_once()
            self.assertIs(sup.bot, replacement)
            self.assertIn("Restarting bot", (log_dir / "supervisor.log").read_text(encoding="utf-8"))

    def test_stop_shuts_down_worker_and_bot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sup = supervisor.ComponentSupervisor(
                config={"log_directory": tmp},
                greeting_queue=mock.Mock(),
                debug_camera_queue=None,
                start_monitor_thread=False,
            )
            sup.worker = _FakeWorkerHandle(exitcode=None)
            sup.bot = _FakeBotHandle(returncode=None)

            with mock.patch.object(supervisor, "stop_recognition_worker") as stop_worker, \
                 mock.patch.object(supervisor, "stop_bot_process") as stop_bot:
                sup.stop()

            stop_worker.assert_called_once_with(sup.worker)
            stop_bot.assert_called_once_with(sup.bot)


class TestLogTail(unittest.TestCase):
    def test_print_log_tail_includes_component_names_and_latest_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp)
            for component in supervisor.COMPONENT_LOGS:
                (log_dir / f"{component}.log").write_text(
                    "\n".join(f"{component}-{i}" for i in range(5)),
                    encoding="utf-8",
                )

            output = supervisor.format_log_tail(log_dir, line_count=2)

        self.assertIn("== worker.log ==", output)
        self.assertIn("worker-3", output)
        self.assertIn("worker-4", output)
        self.assertNotIn("worker-0", output)


if __name__ == "__main__":
    unittest.main()
