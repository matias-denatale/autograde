import subprocess
from pathlib import Path

import pytest

from autograde.cli import RepositoryCheckResult, check_repository, main


def run_git(args, cwd=None):
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git command failed: {' '.join(args)}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def create_local_repository(tmp_path: Path, *, file1_on_main=True, feature_branch=True, main_branch="main") -> str:
    repo_dir = tmp_path / "source"
    repo_dir.mkdir()
    run_git(["init"], cwd=repo_dir)
    run_git(["checkout", "-b", main_branch], cwd=repo_dir)

    if file1_on_main:
        (repo_dir / "file1.txt").write_text("hello\n")
        run_git(["add", "file1.txt"], cwd=repo_dir)

    if file1_on_main:
        run_git(["commit", "-m", "initial commit"], cwd=repo_dir)
    else:
        run_git(["commit", "--allow-empty", "-m", "initial commit"], cwd=repo_dir)

    if feature_branch:
        run_git(["checkout", "-b", "feature"], cwd=repo_dir)
        run_git(["checkout", main_branch], cwd=repo_dir)

    bare_dir = tmp_path / "remote.git"
    run_git(["clone", "--bare", str(repo_dir), str(bare_dir)], cwd=tmp_path)
    return bare_dir.as_uri()


def test_check_repository_passes_with_required_branches_and_file(tmp_path):
    repo_url = create_local_repository(tmp_path)
    result = check_repository(repo_url)

    assert isinstance(result, RepositoryCheckResult)
    assert result.passed
    assert result.is_git is True
    assert result.has_main is True
    assert result.has_feature is True
    assert result.has_file1 is True


def test_check_repository_fails_without_feature_branch(tmp_path):
    repo_url = create_local_repository(tmp_path, feature_branch=False)
    result = check_repository(repo_url)

    assert result.is_git is True
    assert result.has_main is True
    assert result.has_feature is False
    assert result.has_file1 is True
    assert result.passed is False


def test_check_repository_fails_without_main_branch(tmp_path):
    repo_url = create_local_repository(tmp_path, main_branch="develop")
    result = check_repository(repo_url)

    assert result.is_git is True
    assert result.has_main is False
    assert result.has_feature is True
    assert result.has_file1 is False
    assert result.passed is False


def test_check_repository_fails_without_file1(tmp_path):
    repo_url = create_local_repository(tmp_path, file1_on_main=False)
    result = check_repository(repo_url)

    assert result.is_git is True
    assert result.has_main is True
    assert result.has_feature is True
    assert result.has_file1 is False
    assert result.passed is False


def test_main_returns_zero_for_passing_repository(tmp_path):
    repo_url = create_local_repository(tmp_path)
    exit_code = main([repo_url])

    assert exit_code == 0


def test_main_returns_nonzero_for_invalid_repository(tmp_path):
    invalid_url = (tmp_path / "not-a-repo").as_uri()
    exit_code = main([invalid_url])

    assert exit_code == 1
