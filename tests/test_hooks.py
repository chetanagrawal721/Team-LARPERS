import os
import shutil
import subprocess

import pytest

SH = shutil.which("sh")
pytestmark = pytest.mark.skipif(SH is None, reason="sh not available")


def run_commit_msg(tmp_path, msg):
    f = tmp_path / "msg"
    f.write_text(msg)
    return subprocess.run([SH, ".githooks/commit-msg", str(f)], capture_output=True).returncode


def test_team_commit_ok(tmp_path):
    assert run_commit_msg(tmp_path, "M0.1: x\n") == 0


def test_outside_coauthor_rejected(tmp_path):
    assert run_commit_msg(tmp_path, "x\n\nCo-authored-by: Someone <a@b.c>\n") == 1


def test_team_coauthor_accepted(tmp_path):
    assert run_commit_msg(tmp_path, "x\n\nCo-authored-by: chetanagrawal721 <c@users.noreply.github.com>\n") == 0


def run_pre_commit(name):
    env = dict(os.environ, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL="a@b.c")
    return subprocess.run([SH, ".githooks/pre-commit"], capture_output=True, env=env).returncode


def test_wrong_author_rejected():
    assert run_pre_commit("test") == 1


def test_team_author_accepted():
    assert run_pre_commit("atharvg44") == 0


def test_ignored_files(tmp_path):
    out = subprocess.run(["git", "check-ignore", ".env", "gateway/data/x.db"], capture_output=True, text=True).stdout
    assert ".env" in out and "x.db" in out
