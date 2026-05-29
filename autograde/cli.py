import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


@dataclass
class RepositoryCheckResult:
    is_git: bool = False
    has_main: bool = False
    has_feature: bool = False
    has_file1: bool = False

    @property
    def passed(self) -> bool:
        return self.is_git and self.has_main and self.has_feature and self.has_file1


class GitCommandError(RuntimeError):
    pass


def _run_git_command(args, cwd=None):
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise GitCommandError("git executable not found on PATH") from exc
    return result


def is_git_repository(repo_url: str) -> bool:
    result = _run_git_command(["ls-remote", "--heads", repo_url])
    return result.returncode == 0


def remote_branch_exists(repo_url: str, branch: str) -> bool:
    result = _run_git_command(["ls-remote", "--heads", repo_url, f"refs/heads/{branch}"])
    return result.returncode == 0 and bool(result.stdout.strip())


def file_exists_in_branch(repo_url: str, branch: str, path: str) -> bool:
    with TemporaryDirectory() as clone_dir:
        result = _run_git_command(
            ["clone", "--depth", "1", "--branch", branch, repo_url, clone_dir],
        )
        if result.returncode != 0:
            return False
        return (Path(clone_dir) / path).exists()


def check_repository(repo_url: str) -> RepositoryCheckResult:
    result = RepositoryCheckResult()
    result.is_git = is_git_repository(repo_url)
    if not result.is_git:
        return result

    result.has_main = remote_branch_exists(repo_url, "main")
    result.has_feature = remote_branch_exists(repo_url, "feature")
    if result.has_main:
        result.has_file1 = file_exists_in_branch(repo_url, "main", "file1.txt")
    return result


def format_result(result: RepositoryCheckResult) -> str:
    lines = []
    lines.append(f"Repository: {result._url if hasattr(result, '_url') else ''}")
    lines.append(f"- Is git repository: {'PASS' if result.is_git else 'FAIL'}")
    lines.append(f"- Has main branch: {'PASS' if result.has_main else 'FAIL'}")
    lines.append(f"- Has feature branch: {'PASS' if result.has_feature else 'FAIL'}")
    lines.append(f"- main contains file1.txt: {'PASS' if result.has_file1 else 'FAIL'}")
    lines.append(f"Overall: {'PASS' if result.passed else 'FAIL'}")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a repository against AUTOGRADE git conditions."
    )
    parser.add_argument("repo_url", help="Git repository URL to validate.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON result object instead of a plain boolean.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed check output.",
    )
    args = parser.parse_args(argv)

    try:
        result = check_repository(args.repo_url)
    except GitCommandError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "passed": result.passed,
                    "is_git": result.is_git,
                    "has_main": result.has_main,
                    "has_feature": result.has_feature,
                    "has_file1": result.has_file1,
                },
                indent=2,
            )
        )
    else:
        result._url = args.repo_url
        print(format_result(result))

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
