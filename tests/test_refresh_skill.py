"""Behavioral checks for fresh downloads and safe offline fallback."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import time
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
        self.stop_worker = mock.patch.object(refresh_skill, "stop_download")
        self.stopped = self.stop_worker.start()
        self.addCleanup(self.stop_worker.stop)
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
        self.assertEqual(args[4], "https://codeload.github.com/{}/zip/refs/heads/main".format(self.config["repository"]))
        return self.validated_worker(args, self.archive)

    def validated_worker(self, command, contents):
        archive = Path(command[5])
        archive.write_bytes(contents)
        bundle = Path(command[6])
        bundle.mkdir()
        try:
            refresh_skill.unpack(archive, bundle, command[7], command[8])
        except (OSError, ValueError, zipfile.BadZipFile) as error:
            return self.completed_worker(1, refresh_skill.failure_reason(error))
        return self.completed_worker()

    def completed_worker(self, status=0, output=""):
        worker = mock.Mock()
        worker.returncode = status
        worker.poll.return_value = status
        worker.communicate.return_value = (output, None)
        return worker

    def assert_current_unchanged(self):
        self.assertEqual((self.skill / "SKILL.md").read_text(), self.original)

    def test_downloads_again_on_repeated_invocations(self):
        with mock.patch.object(refresh_skill, "start_download", side_effect=self.download_fixture) as network:
            first = refresh_skill.refresh(self.skill)
            second = refresh_skill.refresh(self.skill)
        self.assertEqual(network.call_count, 2)
        self.assertEqual(first, second)
        self.assertEqual((first.parent / "references/guide.md").read_text(), "Latest")
        self.assertEqual((first.parent / "assets/example.txt").read_text(), "asset")
        self.assert_current_unchanged()

    def test_new_upstream_version_replaces_runtime_reading(self):
        with mock.patch.object(refresh_skill, "start_download", side_effect=self.download_fixture):
            first = refresh_skill.refresh(self.skill)
            self.archive = self.make_archive(body="New upstream version")
            second = refresh_skill.refresh(self.skill)
        self.assertNotEqual(first, second)
        self.assertIn("New upstream version", second.read_text())
        self.assert_current_unchanged()

    def test_modified_cached_copy_is_not_reused(self):
        with mock.patch.object(refresh_skill, "start_download", side_effect=self.download_fixture):
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
        with mock.patch.object(refresh_skill, "start_download", side_effect=self.download_fixture):
            result = refresh_skill.refresh(self.skill)
        self.assertNotEqual(result.parent, self.skill)
        self.assertEqual(sentinel.read_text(), "unpublished branch")
        self.assert_current_unchanged()

    def test_definite_connection_failure_does_not_wait_out_timeout(self):
        with mock.patch.object(refresh_skill, "fetch_bundle", side_effect=subprocess.CalledProcessError(1, "download")), \
                mock.patch.object(refresh_skill.time, "monotonic", side_effect=[100, 100]), \
                mock.patch.object(refresh_skill.time, "sleep") as sleep:
            result = refresh_skill.refresh(self.skill)
        sleep.assert_not_called()
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assert_current_unchanged()

    def test_timeout_does_not_add_another_wait(self):
        with mock.patch.object(refresh_skill, "fetch_bundle", side_effect=subprocess.TimeoutExpired("download", 5)), \
                mock.patch.object(refresh_skill.time, "monotonic", side_effect=[100, 105.1]), \
                mock.patch.object(refresh_skill.time, "sleep") as sleep:
            result = refresh_skill.refresh(self.skill)
        sleep.assert_not_called()
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assert_current_unchanged()

    def test_configured_timeout_reaches_download_worker(self):
        with mock.patch.dict(os.environ, {"LLM_SKILL_REFRESH_TIMEOUT_SECONDS": "120"}), \
                mock.patch.object(refresh_skill.time, "monotonic", return_value=100), \
                mock.patch.object(refresh_skill, "start_download", side_effect=self.download_fixture) as worker:
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(float(worker.call_args[0][0][9]), 120)
        self.assertIn("Latest", result.read_text())
        self.assert_current_unchanged()

    def test_invalid_timeout_falls_back_without_network_or_exposing_value(self):
        for value in ("0", "-1", "nan", "inf", "invalid-fixture-value"):
            with self.subTest(value=value):
                output = io.StringIO()
                with mock.patch.dict(os.environ, {"LLM_SKILL_REFRESH_TIMEOUT_SECONDS": value}), \
                        mock.patch.object(refresh_skill, "start_download") as network, \
                        mock.patch.object(refresh_skill.time, "sleep") as sleep, \
                        contextlib.redirect_stdout(output):
                    result = refresh_skill.refresh(self.skill)
                self.assertEqual(result, self.skill / "SKILL.md")
                self.assertIn("must be a positive finite number", output.getvalue())
                self.assertNotIn("invalid-fixture-value", output.getvalue())
                network.assert_not_called()
                sleep.assert_not_called()

    def test_corrupt_download_preserves_current_bundle(self):
        self.archive = b"not a ZIP archive"
        with mock.patch.object(refresh_skill, "start_download", side_effect=self.download_fixture), \
                mock.patch.object(refresh_skill.time, "sleep"):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assert_current_unchanged()

    def test_wrong_skill_identity_preserves_current_bundle(self):
        self.archive = self.make_archive(skill_name="other-skill")
        with mock.patch.object(refresh_skill, "start_download", side_effect=self.download_fixture), \
                mock.patch.object(refresh_skill.time, "sleep"):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assert_current_unchanged()

    def test_path_traversal_is_rejected(self):
        prefix = self.config["repository"].split("/")[1] + "-main/"
        self.archive = self.make_archive(extra=(prefix + "../escape.txt", "unsafe"))
        with mock.patch.object(refresh_skill, "start_download", side_effect=self.download_fixture), \
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
        with mock.patch.object(refresh_skill, "start_download", side_effect=self.download_fixture), \
                mock.patch.object(refresh_skill.time, "sleep"):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assert_current_unchanged()


    def test_ssh_download_uses_existing_git_credentials(self):
        url = "https://codeload.github.com/{}/zip/refs/heads/main".format(self.config["repository"])
        destination = self.root / "private.zip"
        def git_command(command, **kwargs):
            self.assertEqual(kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")
            self.assertLessEqual(kwargs["timeout"], 120)
            self.assertGreater(kwargs["timeout"], 100)
            if command[1] == "clone":
                self.assertIn("git@github.com:" + self.config["repository"] + ".git", command)
            else:
                self.assertIn("archive", command)
                destination.write_bytes(self.archive)
            return subprocess.CompletedProcess(command, 0)
        with mock.patch.object(refresh_skill.subprocess, "run", side_effect=git_command) as git:
            refresh_skill.download(url, destination, transport="ssh", timeout=120)
        self.assertEqual(git.call_count, 2)
        self.assertEqual(destination.read_bytes(), self.archive)

    def test_https_git_uses_configured_credentials_without_prompting(self):
        url = "https://codeload.github.com/{}/zip/refs/heads/main".format(self.config["repository"])
        destination = self.root / "private.zip"
        def git_command(command, **kwargs):
            self.assertEqual(kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")
            self.assertEqual(kwargs["env"]["GCM_INTERACTIVE"], "never")
            if command[1] == "clone":
                self.assertIn("https://github.com/" + self.config["repository"] + ".git", command)
                self.assertNotIn("-c", command)
            else:
                destination.write_bytes(self.archive)
            return subprocess.CompletedProcess(command, 0)
        with mock.patch.object(refresh_skill.subprocess, "run", side_effect=git_command):
            refresh_skill.download(url, destination, transport="https-git")
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
            transport = command[3]
            attempts.append(transport)
            if transport == "ssh":
                return self.completed_worker(1, "credentials unavailable or rejected")
            return self.validated_worker(command, self.archive)
        with mock.patch.object(refresh_skill, "start_download", side_effect=worker):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(attempts, ["ssh", "https-git"])
        self.assertIn("Latest", result.read_text())
        self.assert_current_unchanged()

    def fetch_with_scheduled_workers(self, durations, contents=None):
        staging = self.root / "staging"
        staging.mkdir()
        time_now = [100.0]
        attempts = []
        def worker(command):
            transport = command[3]
            started = time_now[0]
            attempts.append((transport, started, command[5]))
            process = self.validated_worker(command, (contents or {}).get(transport, self.archive))
            duration = durations[transport]
            process.poll.side_effect = lambda: (process.returncode if duration is not None and
                                               time_now[0] >= started + duration else None)
            return process
        def advance(seconds):
            time_now[0] += seconds
        with mock.patch.object(refresh_skill.time, "monotonic", side_effect=lambda: time_now[0]), \
                mock.patch.object(refresh_skill.time, "sleep", side_effect=advance), \
                mock.patch.object(refresh_skill, "start_download", side_effect=worker):
            try:
                result = refresh_skill.fetch_bundle(
                    self.config["repository"], self.config["skill_name"], staging, 105.0)
            except refresh_skill.RefreshError:
                result = None
        return result, attempts, time_now[0]

    def test_slow_valid_ssh_can_use_the_shared_budget(self):
        result, attempts, finished = self.fetch_with_scheduled_workers(
            {"ssh": 2.7, "https-git": None, "https": None})
        self.assertEqual(result[2], "ssh")
        self.assertIn("Latest", (result[1] / "SKILL.md").read_text())
        self.assertEqual([attempt[0] for attempt in attempts], ["ssh", "https-git", "https"])
        self.assertEqual(len({attempt[2] for attempt in attempts}), 3)
        self.assertGreaterEqual(finished, 102.7)
        self.assertLess(finished, 102.75)
        self.assertEqual(self.stopped.call_count, 3)

    def test_stalled_git_workers_allow_public_https_to_finish(self):
        result, attempts, finished = self.fetch_with_scheduled_workers(
            {"ssh": None, "https-git": None, "https": 0.2})
        self.assertEqual(result[2], "https")
        self.assertLess(finished, 101.3)
        self.assertEqual(len(attempts), 3)
        self.assertEqual(self.stopped.call_count, 3)

    def test_all_stalled_workers_share_five_second_deadline(self):
        result, attempts, finished = self.fetch_with_scheduled_workers(
            {"ssh": None, "https-git": None, "https": None})
        self.assertIsNone(result)
        self.assertEqual([attempt[0] for attempt in attempts], ["ssh", "https-git", "https"])
        self.assertEqual(finished, 105.0)
        self.assertEqual(self.stopped.call_count, 3)

    def test_failure_diagnostics_identify_attempts_without_raw_credentials(self):
        def worker(command):
            reason = ("HTTP 404 (repository missing or access denied)" if command[3] == "https"
                      else "credentials unavailable or rejected")
            return self.completed_worker(1, reason)
        output = io.StringIO()
        with mock.patch.object(refresh_skill, "start_download", side_effect=worker), \
                mock.patch.object(refresh_skill.time, "sleep"), contextlib.redirect_stdout(output):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(result, self.skill / "SKILL.md")
        self.assertIn("SSH credentials unavailable or rejected", output.getvalue())
        self.assertIn("HTTPS Git credentials unavailable or rejected", output.getvalue())
        self.assertIn("HTTPS archive HTTP 404", output.getvalue())

    def test_worker_reports_categorized_git_failure(self):
        executable = self.root / "bin" / "git"
        executable.parent.mkdir()
        executable.write_text("#!/bin/sh\nprintf '%s\\n' 'fatal: Authentication failed for https://user:fixture-token@github.com/' >&2\nexit 128\n")
        executable.chmod(0o755)
        url = "https://codeload.github.com/{}/zip/refs/heads/main".format(self.config["repository"])
        environment = dict(os.environ, PATH=str(executable.parent) + os.pathsep + os.environ.get("PATH", ""))
        result = subprocess.run(
            [refresh_skill.sys.executable, str(ROOT / "scripts/refresh_skill.py"), "--download",
             "https-git", url, str(self.root / "archive.zip"), str(self.root / "bundle"),
             self.config["repository"], self.config["skill_name"], "60"],
            env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=5)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.strip(), "credentials unavailable or rejected")
        self.assertEqual(result.stderr, "")
        self.assertNotIn("fixture-token", result.stdout)

    def test_invalid_ssh_archive_can_fall_back_to_valid_https_bundle(self):
        attempts = []
        def worker(command):
            transport = command[3]
            attempts.append(transport)
            return self.validated_worker(command, b"invalid archive" if transport == "ssh" else self.archive)
        with mock.patch.object(refresh_skill, "start_download", side_effect=worker):
            result = refresh_skill.refresh(self.skill)
        self.assertEqual(attempts, ["ssh", "https-git"])
        self.assertIn("Latest", result.read_text())
        self.assertEqual(self.stopped.call_count, 2)
        self.assert_current_unchanged()

    def test_slow_validation_is_cancelled_at_the_shared_deadline(self):
        fixture = self.root / "fixture.zip"
        fixture.write_bytes(self.archive)
        wrapper = self.root / "slow_validation.py"
        wrapper.write_text(
            "import sys, shutil, time\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, {!r})\n"
            "import refresh_skill\n"
            "def download(url, destination, transport, timeout):\n"
            "    shutil.copyfile({!r}, str(destination))\n"
            "def unpack(archive, destination, repository, skill_name):\n"
            "    destination.with_suffix('.validating').write_text('started')\n"
            "    time.sleep(60)\n"
            "refresh_skill.download = download\n"
            "refresh_skill.unpack = unpack\n"
            "refresh_skill.main()\n".format(str(ROOT / "scripts"), str(fixture)))
        staging = self.root / "staging"
        staging.mkdir()
        spawn = refresh_skill.start_download
        processes = []
        def start_worker(command):
            process = spawn([command[0], str(wrapper)] + command[2:])
            processes.append(process)
            return process
        started = time.monotonic()
        with mock.patch.object(refresh_skill, "start_download", side_effect=start_worker), \
                mock.patch.object(refresh_skill, "stop_download", side_effect=self.stop_worker.temp_original):
            with self.assertRaises(refresh_skill.RefreshError):
                refresh_skill.fetch_bundle(self.config["repository"], self.config["skill_name"],
                                           staging, started + 0.6)
        self.assertTrue(list(staging.glob("*.validating")))
        self.assertLess(time.monotonic() - started, 1.5)
        self.assertTrue(all(process.poll() is not None for process in processes))

    @unittest.skipUnless(os.name == "posix", "process groups require POSIX")
    def test_stopping_worker_terminates_its_descendant(self):
        stop_worker = self.stop_worker.temp_original
        child_script = "import time; time.sleep(60)"
        script = ("import subprocess, sys, time; "
                  "child = subprocess.Popen([sys.executable, '-c', {!r}]); "
                  "print(child.pid); sys.stdout.flush(); time.sleep(60)").format(child_script)
        worker = refresh_skill.start_download([refresh_skill.sys.executable, "-u", "-c", script])
        self.addCleanup(stop_worker, worker)
        descendant = int(worker.stdout.readline())
        stop_worker(worker)
        self.assertIsNotNone(worker.poll())
        state = Path("/proc") / str(descendant) / "stat"
        try:
            status = state.read_text().split()[2]
        except (FileNotFoundError, ProcessLookupError):
            return
        self.assertEqual(status, "Z")


if __name__ == "__main__":
    unittest.main()
