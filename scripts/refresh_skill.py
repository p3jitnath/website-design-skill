#!/usr/bin/env python3
"""Fetch a fresh GitHub skill bundle per invocation, with a five-second fallback."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid
import zipfile

WAIT_SECONDS = 5.0


def download(url, destination):
    started = time.monotonic()
    request = Request(url, headers={"User-Agent": "llm-skills-refresh"})
    try:
        with urlopen(request, timeout=WAIT_SECONDS) as response:
            with destination.open("wb") as output:
                shutil.copyfileobj(response, output)
        return
    except HTTPError as error:
        if error.code not in (401, 403, 404):
            raise
        match = re.fullmatch(
            r"https://codeload\.github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/zip/refs/heads/main",
            url)
        if not match:
            raise
        repository = match.group(1)
    # Private repositories use existing SSH credentials, without an auth prompt.
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    environment.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
    with tempfile.TemporaryDirectory(prefix=".git-download-", dir=str(destination.parent)) as temporary:
        checkout = Path(temporary) / "checkout"
        commands = [
            ["git", "clone", "--quiet", "--depth", "1", "--single-branch",
             "--branch", "main", "git@github.com:" + repository + ".git", str(checkout)],
            ["git", "-C", str(checkout), "archive", "--format=zip",
             "--prefix=" + repository.split("/")[1] + "-main/",
             "--output=" + str(destination), "HEAD"],
        ]
        for command in commands:
            remaining = WAIT_SECONDS - (time.monotonic() - started)
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, WAIT_SECONDS)
            subprocess.run(command, check=True, env=environment, timeout=remaining,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_download(command, timeout):
    # Terminate the worker and any Git/SSH descendants when its budget expires.
    worker = subprocess.Popen(command, start_new_session=(os.name == "posix"),
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        worker.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            if os.name == "posix":
                os.killpg(worker.pid, signal.SIGKILL)
            else:
                worker.kill()
        except ProcessLookupError:
            pass
        worker.communicate()
        raise
    if worker.returncode:
        raise subprocess.CalledProcessError(worker.returncode, command)


def unpack(archive, destination, repository, skill_name):
    """Extract a complete bundle, rejecting unsafe paths and unexpected identity."""
    root = repository.split("/")[1] + "-main"
    written = set()
    with zipfile.ZipFile(str(archive)) as source:
        for member in source.infolist():
            parts = PurePosixPath(member.filename).parts
            if (not parts or parts[0] != root or
                    ".." in parts or "\\" in member.filename or
                    stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError("Unsafe or unexpected archive member")
            relative = Path(*parts[1:])
            target = destination / relative
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not parts[1:] or str(relative) in written:
                raise ValueError("Duplicate or invalid archive member")
            written.add(str(relative))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read(member))
            mode = stat.S_IMODE(member.external_attr >> 16)
            target.chmod(0o755 if mode & 0o111 else 0o644)
    entrypoint = destination / "SKILL.md"
    text = entrypoint.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)
    if (len(frontmatter) != 3 or frontmatter[0].strip() or
            not re.search(r"^name:\s*" + re.escape(skill_name) + r"\s*$",
                          frontmatter[1], re.MULTILINE)):
        raise ValueError("Downloaded skill has unexpected frontmatter")


def same_bundle(first, second):
    if not second.is_dir() or second.is_symlink():
        return False
    first_files = {p.relative_to(first) for p in first.rglob("*") if p.is_file()}
    second_files = {p.relative_to(second) for p in second.rglob("*") if p.is_file()}
    if first_files != second_files:
        return False
    return all(not (second / p).is_symlink() and
               (first / p).read_bytes() == (second / p).read_bytes()
               for p in first_files)


def refresh(skill_dir):
    """Leave the installed/source bundle intact; return a verified runtime copy."""
    skill_dir = skill_dir.resolve()
    started = time.monotonic()
    try:
        config = json.loads((skill_dir / "scripts" / "refresh-source.json").read_text())
        repository = config["repository"]
        skill_name = config["skill_name"]
        if (not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or
                not re.fullmatch(r"[a-z0-9-]+", skill_name) or
                config["branch"] != "main"):
            raise ValueError("Invalid GitHub source configuration")
        cache_root = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
        cache = cache_root / "llm-skills" / skill_name
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".download-", dir=str(cache)) as staging:
            staging = Path(staging)
            archive = staging / "latest.zip"
            url = "https://codeload.github.com/{}/zip/refs/heads/main".format(repository)
            # A separate process bounds DNS, connection, and the entire transfer,
            # including a connection that stalls between individual reads.
            run_download([sys.executable, str(Path(__file__).resolve()),
                          "--download", url, str(archive)], timeout=WAIT_SECONDS)
            bundle = staging / "bundle"
            bundle.mkdir()
            unpack(archive, bundle, repository, skill_name)
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            target = cache / digest
            if not same_bundle(bundle, target):
                if target.exists():
                    target = cache / (digest + "-" + uuid.uuid4().hex)
                bundle.rename(target)
        print("Downloaded latest main bundle from {}.".format(repository))
        entrypoint = target / "SKILL.md"
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile,
            subprocess.SubprocessError, RuntimeError) as error:
        remaining = WAIT_SECONDS - (time.monotonic() - started)
        if remaining > 0:
            time.sleep(remaining)
        print("GitHub refresh unavailable ({}); using the current bundle after "
              "the five-second fallback.".format(type(error).__name__))
        entrypoint = skill_dir / "SKILL.md"
    print("Use skill: {}".format(entrypoint))
    return entrypoint


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--download":
        download(sys.argv[2], Path(sys.argv[3]))
    elif len(sys.argv) == 1:
        refresh(Path(__file__).resolve().parent.parent)
    else:
        raise SystemExit("Usage: python3 <skill-dir>/scripts/refresh_skill.py")


if __name__ == "__main__":
    main()
