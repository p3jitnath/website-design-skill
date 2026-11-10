#!/usr/bin/env python3
"""Fetch a fresh GitHub skill bundle within a configurable shared deadline."""

import hashlib
import json
import math
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
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid
import zipfile

DEFAULT_TIMEOUT_SECONDS = 120.0


class RefreshError(RuntimeError):
    """A diagnostic safe to display without raw credential-bearing output."""


def failure_reason(error):
    """Describe failures without echoing URLs, credentials or Git output."""
    if isinstance(error, RefreshError):
        return str(error)
    if isinstance(error, subprocess.TimeoutExpired):
        return "timed out"
    if isinstance(error, HTTPError):
        if error.code == 404:
            return "HTTP 404 (repository missing or access denied)"
        return "HTTP {}".format(error.code)
    if isinstance(error, FileNotFoundError):
        return "required executable or file unavailable"
    detail = str(error.stderr or "") if isinstance(error, subprocess.CalledProcessError) else str(error)
    detail = detail.lower()
    if "repository not found" in detail:
        return "repository missing or credentials lack access"
    if any(message in detail for message in ("permission denied (publickey)", "authentication failed",
                                             "could not read username", "terminal prompts disabled")):
        return "credentials unavailable or rejected"
    if any(message in detail for message in ("could not resolve", "name or service not known",
                                             "nodename nor servname")):
        return "DNS lookup failed"
    if "certificate" in detail or "ssl" in detail:
        return "TLS certificate verification failed"
    if "host key verification failed" in detail:
        return "SSH host key verification failed"
    if "timed out" in detail:
        return "connection timed out"
    if isinstance(error, (OSError, URLError)):
        return "connection or filesystem unavailable"
    return type(error).__name__


def refresh_timeout():
    value = os.environ.get("LLM_SKILL_REFRESH_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        timeout = float(value)
    except ValueError:
        raise RefreshError("LLM_SKILL_REFRESH_TIMEOUT_SECONDS must be a positive finite number")
    if not math.isfinite(timeout) or timeout <= 0:
        raise RefreshError("LLM_SKILL_REFRESH_TIMEOUT_SECONDS must be a positive finite number")
    return timeout


def download(url, destination, transport="https", timeout=DEFAULT_TIMEOUT_SECONDS):
    """Download through one transport inside the bounded worker process."""
    started = time.monotonic()
    if transport == "https":
        request = Request(url, headers={"User-Agent": "llm-skills-refresh"})
        with urlopen(request, timeout=timeout) as response:
            with destination.open("wb") as output:
                shutil.copyfileobj(response, output)
        return
    if transport not in ("ssh", "https-git"):
        raise ValueError("Unknown GitHub transport")
    match = re.fullmatch(
        r"https://codeload\.github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/zip/refs/heads/main",
        url)
    if not match:
        raise ValueError("Unexpected GitHub source URL")
    repository = match.group(1)
    # Let Git use configured SSH identities and HTTPS credential helpers.
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    environment.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes -o ConnectTimeout=2")
    remote = ("git@github.com:" + repository + ".git" if transport == "ssh"
              else "https://github.com/" + repository + ".git")
    with tempfile.TemporaryDirectory(prefix=".git-download-", dir=str(destination.parent)) as temporary:
        checkout = Path(temporary) / "checkout"
        commands = [
            ["git", "clone", "--quiet", "--no-checkout", "--depth", "1", "--single-branch",
             "--branch", "main", remote, str(checkout)],
            ["git", "-C", str(checkout), "archive", "--format=zip",
             "--prefix=" + repository.split("/")[1] + "-main/",
             "--output=" + str(destination), "HEAD"],
        ]
        for command in commands:
            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, timeout)
            subprocess.run(command, check=True, env=environment, timeout=remaining,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, universal_newlines=True)


def start_download(command):
    return subprocess.Popen(command, start_new_session=(os.name == "posix"),
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)


def stop_download(worker):
    """Reap the worker and terminate any Git or SSH descendants as well."""
    try:
        if os.name == "posix":
            os.killpg(worker.pid, signal.SIGKILL)
        elif worker.poll() is None:
            worker.kill()
    except ProcessLookupError:
        pass
    worker.wait()
    if worker.stdout is not None:
        worker.stdout.close()


def fetch_bundle(repository, skill_name, staging, deadline):
    """Bound both downloading and validation with one shared worker deadline."""
    url = "https://codeload.github.com/{}/zip/refs/heads/main".format(repository)
    transports = ("ssh", "https-git", "https")
    labels = ("SSH", "HTTPS Git", "HTTPS archive")
    failures = {}
    pending = {}
    workers = []
    index = 0
    next_start = time.monotonic()
    try:
        while pending or index < len(transports):
            now = time.monotonic()
            if now >= deadline:
                for transport in pending:
                    failures[transport] = "timed out"
                break
            if index < len(transports) and (not pending or now >= next_start):
                transport = transports[index]
                archive = staging / (transport + ".zip")
                bundle = staging / transport
                try:
                    worker = start_download([sys.executable, str(Path(__file__).resolve()),
                                             "--download", transport, url, str(archive),
                                             str(bundle), repository, skill_name,
                                             str(deadline - time.monotonic())])
                    workers.append(worker)
                    pending[transport] = (worker, archive, bundle)
                except OSError as error:
                    failures[transport] = failure_reason(error)
                index += 1
                # Start fallbacks even when SSH is still transferring a valid bundle.
                next_start = now + 0.5
            for transport, (worker, archive, bundle) in list(pending.items()):
                if worker.poll() is None:
                    continue
                del pending[transport]
                try:
                    output, _ = worker.communicate()
                    if worker.returncode:
                        raise RefreshError(output.strip() or "download worker failed")
                    return archive, bundle, transport
                except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile,
                        subprocess.SubprocessError, RuntimeError) as error:
                    failures[transport] = failure_reason(error)
            if pending:
                remaining = deadline - time.monotonic()
                delay = min(0.02, remaining)
                if index < len(transports):
                    delay = min(delay, next_start - time.monotonic())
                if delay > 0:
                    time.sleep(delay)
    finally:
        for worker in workers:
            stop_download(worker)
    if failures:
        raise RefreshError(". ".join("{} {}".format(label, failures[transport])
                                     for transport, label in zip(transports, labels)
                                     if transport in failures))
    raise RefreshError("download budget exhausted")


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
    """Leave the installed/source bundle intact and return a verified runtime copy."""
    skill_dir = skill_dir.resolve()
    started = time.monotonic()
    try:
        timeout = refresh_timeout()
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
        with tempfile.TemporaryDirectory(prefix="llm-skill-download-") as staging:
            staging = Path(staging)
            archive, bundle, transport = fetch_bundle(
                repository, skill_name, staging, started + timeout)
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            target = cache / digest
            if not same_bundle(bundle, target):
                if target.exists():
                    target = cache / (digest + "-" + uuid.uuid4().hex)
                shutil.move(str(bundle), str(target))
        print("Downloaded latest main bundle from {} using {}.".format(repository, transport.upper()))
        entrypoint = target / "SKILL.md"
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile,
            subprocess.SubprocessError, RuntimeError) as error:
        print("GitHub refresh unavailable ({}). Using the current bundle.".format(failure_reason(error)))
        entrypoint = skill_dir / "SKILL.md"
    print("Use skill from {}".format(entrypoint))
    return entrypoint


def main():
    if len(sys.argv) == 9 and sys.argv[1] == "--download":
        try:
            download(sys.argv[3], Path(sys.argv[4]), transport=sys.argv[2], timeout=float(sys.argv[8]))
            bundle = Path(sys.argv[5])
            bundle.mkdir()
            unpack(Path(sys.argv[4]), bundle, sys.argv[6], sys.argv[7])
        except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile,
                subprocess.SubprocessError, RuntimeError) as error:
            print(failure_reason(error))
            raise SystemExit(1)
    elif len(sys.argv) == 1:
        refresh(Path(__file__).resolve().parent.parent)
    else:
        raise SystemExit("Usage python3 <skill-dir>/scripts/refresh_skill.py")


if __name__ == "__main__":
    main()
