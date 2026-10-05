"""Behavioral checks for fresh downloads and safe offline fallback."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("refresh_skill", str(ROOT / "scripts" / "refresh_skill.py"))
refresh_skill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh_skill)


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.skill = self.root / "installed"
        (self.skill / "scripts").mkdir(parents=True)
        self.config = json.loads((ROOT / "scripts" / "refresh-source.json").read_text())
        (self.skill / "scripts" / "refresh-source.json").write_text(json.dumps(self.config))
        self.original = "---\nname: {}\ndescription: Installed fallback\n---\nCurrent\n".format(self.config["skill_name"])
        (self.skill / "SKILL.md").write_text(self.original)
        self.archive = self.make_archive()
        environment = mock.patch.dict(os.environ, {"XDG_CACHE_HOME": str(self.root / "cache")})
        environment.start()
        self.addCleanup(environment.stop)
        quiet = contextlib.redirect_stdout(io.StringIO())
        quiet.__enter__()
        self.addCleanup(quiet.__exit__, None, None, None)

    def make_archive(self, body="Latest", extra=None, skill_name=None):
        output = io.BytesIO()
        prefix = self.config["repository"].split("/")[1] + "-main/"
        name = self.config["skill_name"] if skill_name is None else skill_name
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr(prefix + "SKILL.md", "---\nname: {}\ndescription: Fresh version\n---\n{}\n".format(name, body))
            archive.writestr(prefix + "references/guide.md", body)
            archive.writestr(prefix + "assets/example.txt", "asset")
            archive.writestr(prefix + "scripts/refresh-source.json", json.dumps(self.config))
            if extra is not None:
                archive.writestr(extra[0], extra[1])
        return output.getvalue()

    def download_fixture(self, args, **kwargs):
        self.assertGreater(kwargs["timeout"], 0)
        self.assertLessEqual(kwargs["timeout"], refresh_skill.WAIT_SECONDS)
        self.assertEqual(args[-2], "https://codeload.github.com/{}/zip/refs/heads/main".format(self.config["repository"]))
        Path(args[-1]).write_bytes(self.archive)
        return subprocess.CompletedProcess(args, 0)

    def assert_current_unchanged(self):
        self.assertEqual((self.skill / "SKILL.md").read_text(), self.original)

    def test_downloads_again_on_repeated_invocations(self):
        with mock.patch.object(refresh_skill, "run_download", side_effect=self.download_fixture) as network:
            first = refresh_skill.refresh(self.skill)
            second = refresh_skill.refresh(self.skill)
        self.assertEqual(network.call_count, 2)
        self.assertEqual(first, second)
        self.assertEqual((first.parent / "references/guide.md").read_text(), "Latest")
        self.assertEqual((first.parent / "assets/example.txt").read_text(), "asset")
        self.assert_current_unchanged()

    def test_new_upstream_version_replaces_runtime_reading(self):
        with mock.patch.object(refresh_skill, "run_download", side_effect=self.download_fixture):
            first = refresh_skill.refresh(self.skill)
            self.archive = self.make_archive(body="New upstream version")
            second = refresh_skill.refresh(self.skill)
        self.assertNotEqual(first, second)
        self.assertIn("New upstream version", second.read_text())
        self.assert_current_unchanged()

    def test_modified_cached_copy_is_not_reused(self):
        with mock.patch.object(refresh_skill, "run_download", side_effect=self.download_fixture):
            first = refresh_skill.refresh(self.skill)
            first.write_text("Stale local edit")
            second = refresh_skill.refresh(self.skill)
        self.assertNotEqual(first, second)
        self.assertIn("Latest", second.read_text())
        self.assert_current_unchanged()

    def test_source_checkout_edits_are_preserved(self):
        (self.skill / ".git").mkdir()
        sentinel = self.skill / ".git" / "HEAD"
        sentinel.write_text("unpublished branch")
        with mock.patch.object(refresh_skill, "run_download", side_effect=self.download_fixture):
            result = refresh_skill.refresh(self.skill)
        self.assertNotEqual(result.parent, self.skill)
        self.assertEqual(sentinel.read_text(), "unpublished branch")
        self.assert_current_unchanged()

    def test_immediate_connection_failure_waits_five_seconds(self):
        with mock.patch.object(refresh_skill, "fetch_bundle", side_effect=subprocess.CalledProcessError(1, "download")), \
                mock.patch.object(refresh_skill.time, "monotonic", side_effect=[100, 100]), \
                mock.patch.object(refresh_skill.time, "sleep") as sleep:
            result = refresh_skill.refresh(self.skill)
        sleep.assert_called_once_with(5.0)
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assert_current_unchanged()

    def test_timeout_does_not_add_another_five_second_wait(self):
        with mock.patch.object(refresh_skill, "fetch_bundle", side_effect=subprocess.TimeoutExpired("download", 5)), \
                mock.patch.object(refresh_skill.time, "monotonic", side_effect=[100, 105.1]), \
                mock.patch.object(refresh_skill.time, "sleep") as sleep:
            result = refresh_skill.refresh(self.skill)
        sleep.assert_not_called()
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assert_current_unchanged()

    def test_corrupt_download_preserves_current_bundle(self):
        self.archive = b"not a ZIP archive"
        with mock.patch.object(refresh_skill, "run_download", side_effect=self.download_fixture), \
                mock.patch.object(refresh_skill.time, "sleep"):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assert_current_unchanged()

    def test_wrong_skill_identity_preserves_current_bundle(self):
        self.archive = self.make_archive(skill_name="other-skill")
        with mock.patch.object(refresh_skill, "run_download", side_effect=self.download_fixture), \
                mock.patch.object(refresh_skill.time, "sleep"):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assert_current_unchanged()

    def test_path_traversal_is_rejected(self):
        prefix = self.config["repository"].split("/")[1] + "-main/"
        self.archive = self.make_archive(extra=(prefix + "../escape.txt", "unsafe"))
        with mock.patch.object(refresh_skill, "run_download", side_effect=self.download_fixture), \
                mock.patch.object(refresh_skill.time, "sleep"):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assertFalse(list(self.root.rglob("escape.txt")))
        self.assert_current_unchanged()

    def test_archive_symlink_is_rejected(self):
        info = zipfile.ZipInfo(self.config["repository"].split("/")[1] + "-main/assets/link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr(info, "/tmp/target")
        self.archive = output.getvalue()
        with mock.patch.object(refresh_skill, "run_download", side_effect=self.download_fixture), \
                mock.patch.object(refresh_skill.time, "sleep"):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assert_current_unchanged()


    def test_ssh_download_uses_existing_git_credentials(self):
        url = "https://codeload.github.com/{}/zip/refs/heads/main".format(self.config["repository"])
        destination = self.root / "private.zip"
        def git_command(command, **kwargs):
            self.assertEqual(kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")
            self.assertLessEqual(kwargs["timeout"], 5)
            self.assertGreater(kwargs["timeout"], 0)
            if command[1] == "clone":
                self.assertIn("git@github.com:" + self.config["repository"] + ".git", command)
            else:
                self.assertIn("archive", command)
                destination.write_bytes(self.archive)
            return subprocess.CompletedProcess(command, 0)
        with mock.patch.object(refresh_skill.subprocess, "run", side_effect=git_command) as git:
            refresh_skill.download(url, destination, transport="ssh")
        self.assertEqual(git.call_count, 2)
        self.assertEqual(destination.read_bytes(), self.archive)

    def test_https_download_does_not_require_git(self):
        destination = self.root / "https.zip"
        url = "https://codeload.github.com/{}/zip/refs/heads/main".format(self.config["repository"])
        with mock.patch.object(refresh_skill, "urlopen", return_value=io.BytesIO(self.archive)) as http, \
                mock.patch.object(refresh_skill.subprocess, "run") as git:
            refresh_skill.download(url, destination, transport="https")
        self.assertEqual(destination.read_bytes(), self.archive)
        self.assertEqual(http.call_count, 1)
        git.assert_not_called()

    def test_ssh_connection_failure_uses_https_for_the_same_invocation(self):
        attempts = []
        def worker(command, **kwargs):
            transport = command[-3]
            attempts.append(transport)
            if transport == "ssh":
                raise subprocess.CalledProcessError(128, command)
            Path(command[-1]).write_bytes(self.archive)
        with mock.patch.object(refresh_skill, "run_download", side_effect=worker):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(attempts, ["ssh", "https"])
        self.assertIn("Latest", result.read_text())
        self.assert_current_unchanged()

    def test_early_ssh_failure_leaves_the_remaining_budget_for_https(self):
        staging = self.root / "staging"
        staging.mkdir()
        time_now = [100.0]
        budgets = []
        def worker(command, **kwargs):
            budgets.append(kwargs["timeout"])
            if command[-3] == "ssh":
                time_now[0] += 2.0
                raise subprocess.CalledProcessError(128, command)
            Path(command[-1]).write_bytes(self.archive)
        with mock.patch.object(refresh_skill.time, "monotonic", side_effect=lambda: time_now[0]), \
                mock.patch.object(refresh_skill, "run_download", side_effect=worker):
            archive, bundle, transport = refresh_skill.fetch_bundle(
                self.config["repository"], self.config["skill_name"], staging, 105.0)
        self.assertEqual(budgets, [5.0, 3.0])
        self.assertEqual(transport, "https")
        self.assertTrue((bundle / "assets/example.txt").is_file())

    def test_stalled_ssh_does_not_extend_the_total_download_budget(self):
        staging = self.root / "staging"
        staging.mkdir()
        time_now = [100.0]
        def worker(command, **kwargs):
            time_now[0] += kwargs["timeout"]
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        with mock.patch.object(refresh_skill.time, "monotonic", side_effect=lambda: time_now[0]), \
                mock.patch.object(refresh_skill, "run_download", side_effect=worker) as network:
            with self.assertRaises(subprocess.TimeoutExpired):
                refresh_skill.fetch_bundle(self.config["repository"], self.config["skill_name"], staging, 105.0)
        self.assertEqual(network.call_count, 1)
        self.assertEqual(time_now[0], 105.0)

    def test_invalid_ssh_archive_can_fall_back_to_valid_https_bundle(self):
        attempts = []
        def worker(command, **kwargs):
            transport = command[-3]
            attempts.append(transport)
            Path(command[-1]).write_bytes(b"invalid archive" if transport == "ssh" else self.archive)
        with mock.patch.object(refresh_skill, "run_download", side_effect=worker):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(attempts, ["ssh", "https"])
        self.assertIn("Latest", result.read_text())
        self.assert_current_unchanged()

    def test_download_timeout_terminates_worker_group(self):
        worker = mock.Mock()
        worker.pid = 12345
        worker.communicate.side_effect = [subprocess.TimeoutExpired("worker", 5), (None, None)]
        with mock.patch.object(refresh_skill.subprocess, "Popen", return_value=worker) as spawn, \
                mock.patch.object(refresh_skill.os, "killpg", create=True) as kill_group:
            with self.assertRaises(subprocess.TimeoutExpired):
                refresh_skill.run_download(["worker"], timeout=5)
        self.assertEqual(worker.communicate.call_args_list[0], mock.call(timeout=5))
        if os.name == "posix":
            self.assertTrue(spawn.call_args[1]["start_new_session"])
            kill_group.assert_called_once_with(worker.pid, refresh_skill.signal.SIGKILL)
        else:
            worker.kill.assert_called_once_with()
        self.assertEqual(worker.communicate.call_count, 2)



if __name__ == "__main__":
    unittest.main()
