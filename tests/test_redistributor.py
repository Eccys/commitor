import os
from pathlib import Path
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contribution_redistributor import ContributionRedistributor


def _init_repo_with_commit(repo_dir, message, email="user@example.com"):
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", email], cwd=repo_dir, check=True)
    (repo_dir / "file.txt").write_text(message, encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo_dir, check=True, capture_output=True)


def test_find_git_repos_parent_and_single_repo(tmp_path):
    r = ContributionRedistributor()
    assert r.find_git_repos(tmp_path / "does_not_exist") == []

    repo_a = tmp_path / "repo_a"
    repo_b = tmp_path / "repo_b"
    _init_repo_with_commit(repo_a, "initial a")
    _init_repo_with_commit(repo_b, "initial b")

    found_multi = r.find_git_repos(tmp_path)
    assert len(found_multi) == 2

    found_single = r.find_git_repos(repo_a)
    assert found_single == [str(repo_a.resolve())]


def test_get_commits_preserves_cwd_and_pipe_messages(tmp_path):
    orig_cwd = os.getcwd()
    repo = tmp_path / "pipe_repo"
    _init_repo_with_commit(repo, "feat: part A | part B | part C", email="Dev@Example.com")

    r = ContributionRedistributor(github_email="dev@example.com")
    commits = r.get_commits_from_repo(str(repo))
    assert os.getcwd() == orig_cwd
    assert len(commits) == 1
    assert commits[0]["message"] == "feat: part A | part B | part C"
    assert commits[0]["email"] == "Dev@Example.com"

    # Filtering by a non-matching email should yield empty list
    r_other = ContributionRedistributor(github_email="other@example.com")
    assert r_other.get_commits_from_repo(str(repo)) == []

    # Missing repo path or non-git directory should return [] without raising OSError
    assert r.get_commits_from_repo(str(tmp_path / "missing_repo")) == []
    non_git = tmp_path / "plain_dir"
    non_git.mkdir()
    assert r.get_commits_from_repo(str(non_git)) == []


def test_redistribution_plan_preserves_all_commits_on_single_day(tmp_path):
    r = ContributionRedistributor()
    now = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
    r.commits_by_date["repo1"] = [
        {
            "hash": f"hash_{i}",
            "date": now,
            "message": f"commit {i}",
            "email": "user@example.com",
            "repo": str(tmp_path / "repo1"),
            "original_date": now,
        }
        for i in range(25)
    ]
    stats, gaps, date_counts = r.analyze_contributions()
    assert stats["total_commits"] == 25
    assert gaps == []

    plan = r.create_redistribution_plan(date_counts)
    assert len(plan) == 25

    log_file = tmp_path / "log.txt"
    script_file = tmp_path / "rewrite.sh"
    r.save_detailed_log(plan, date_counts, output_file=str(log_file))
    r.generate_rewrite_script(plan, output_file=str(script_file))
    assert log_file.exists()
    assert script_file.exists()
    assert "git filter-branch" in script_file.read_text(encoding="utf-8")


def test_redistribution_plan_preserves_chronological_order_across_days(tmp_path):
    r = ContributionRedistributor()
    day1 = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)
    day2 = day1 + timedelta(days=1)
    commits = []
    for i in range(30):
        dt = day1 if i < 15 else day2
        commits.append(
            {
                "hash": f"hash_{i:02d}",
                "date": dt + timedelta(minutes=i),
                "message": f"commit {i}",
                "email": "user@example.com",
                "repo": str(tmp_path / "repo1"),
                "original_date": dt + timedelta(minutes=i),
            }
        )
    r.commits_by_date["repo1"] = commits
    _, _, date_counts = r.analyze_contributions()

    # Verify global random state is not clobbered by create_redistribution_plan
    random.seed(12345)
    expected_next = random.Random(12345).random()
    plan = r.create_redistribution_plan(date_counts)
    assert random.random() == expected_next

    assert len(plan) == 30
    assigned_dates = [plan[f"hash_{i:02d}"]["new_date"].date() for i in range(30)]
    assert assigned_dates == sorted(assigned_dates), (
        f"Expected monotonic chronological dates, got {assigned_dates}"
    )


def test_empty_contributions_and_gap_detection(tmp_path):
    r = ContributionRedistributor(max_gap_days=3)
    assert r.analyze_contributions() is None
    assert r.create_redistribution_plan({}) == {}

    # Empty plan should not crash print_redistribution_plan or save_detailed_log
    r.print_redistribution_plan({}, {})
    empty_log = tmp_path / "empty_log.txt"
    r.save_detailed_log({}, {}, output_file=str(empty_log))
    assert "No commits in redistribution plan" in empty_log.read_text(encoding="utf-8")

    # Gap detection across > 3 days
    d1 = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
    d2 = datetime(2026, 10, 10, 9, 0, tzinfo=timezone.utc)
    r.commits_by_date["repo1"] = [
        {"hash": "h1", "date": d1, "message": "c1", "email": "a@b.c", "repo": "r", "original_date": d1},
        {"hash": "h2", "date": d2, "message": "c2", "email": "a@b.c", "repo": "r", "original_date": d2},
    ]
    stats, gaps, date_counts = r.analyze_contributions()
    assert stats["total_commits"] == 2
    assert len(gaps) == 1
    assert gaps[0]["days"] == 8
    r.print_analysis(stats, gaps, date_counts)
    plan = r.create_redistribution_plan(date_counts)
    r.print_redistribution_plan(plan, date_counts)


