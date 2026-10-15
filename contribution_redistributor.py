#!/usr/bin/env python3
"""
GitHub Contribution Redistributor
Analyzes commit history and redistributes commits to fill gaps and maintain consistent activity.
"""

import subprocess
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
import statistics

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

class ContributionRedistributor:
    def __init__(self, target_std_dev=5, max_gap_days=7, github_email=None):
        self.target_std_dev = target_std_dev
        self.max_gap_days = max_gap_days
        self.github_email = github_email
        self.repos = []
        self.commits_by_date = defaultdict(list)
        self.redistribution_plan = {}
        
    def find_git_repos(self, base_dir):
        """Find all git repositories in the given directory (or base_dir itself if it is a git repo)."""
        base_path = Path(base_dir).expanduser().resolve()
        if not base_path.exists():
            return []
        if base_path.is_dir() and (base_path / '.git').exists():
            return [str(base_path)]

        repos = []
        if base_path.is_dir():
            for item in sorted(base_path.iterdir()):
                if item.is_dir() and (item / '.git').exists():
                    repos.append(str(item))

        return repos
    
    def get_commits_from_repo(self, repo_path, days_back=365):
        """Extract all commits from a repository for the last N days."""
        # Get date from N days ago
        since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Get commits with hash, author date, author email, and subject (%s last so '|' in messages is preserved)
        cmd = [
            'git', 'log',
            '--all',
            '--pretty=format:%H|%aI|%ae|%s',
            f'--since={since_date}'
        ]
        
        try:
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
            commits = []
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                parts = line.split('|', 3)
                if len(parts) >= 4:
                    commit_hash, date_str, author_email, message = parts
                    
                    # Filter by email if specified
                    if self.github_email and author_email.lower() != self.github_email.lower():
                        continue
                    
                    commit_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    
                    commits.append({
                        'hash': commit_hash,
                        'date': commit_date,
                        'message': message,
                        'email': author_email,
                        'repo': str(Path(repo_path).resolve()),
                        'original_date': commit_date
                    })
            
            return commits
        except (subprocess.CalledProcessError, OSError) as e:
            print(f"Error reading commits from {repo_path}: {e}")
            return []
    
    def analyze_contributions(self):
        """Analyze contribution patterns and identify gaps."""
        # Group commits by date
        date_counts = defaultdict(int)
        
        for commits in self.commits_by_date.values():
            for commit in commits:
                date_key = commit['date'].date()
                date_counts[date_key] += 1
        
        # Calculate statistics
        if not date_counts:
            print("No commits found in the last 365 days!")
            return None
        
        counts = list(date_counts.values())
        
        stats = {
            'total_commits': sum(counts),
            'days_with_commits': len(date_counts),
            'mean': statistics.mean(counts),
            'median': statistics.median(counts),
            'std_dev': statistics.stdev(counts) if len(counts) > 1 else 0,
            'min': min(counts),
            'max': max(counts)
        }
        
        # Find gaps
        all_dates = sorted(date_counts.keys())
        gaps = []
        
        for i in range(len(all_dates) - 1):
            current = all_dates[i]
            next_date = all_dates[i + 1]
            gap_days = (next_date - current).days - 1
            
            if gap_days > self.max_gap_days:
                gaps.append({
                    'start': current,
                    'end': next_date,
                    'days': gap_days,
                    'commits_before': date_counts[current],
                    'commits_after': date_counts[next_date]
                })
        
        return stats, gaps, date_counts
    
    def create_redistribution_plan(self, date_counts):
        """Create a plan to redistribute commits with weekend prioritization."""
        import random
        
        # Get all commits sorted by date
        all_commits = []
        for commits in self.commits_by_date.values():
            all_commits.extend(commits)
        
        all_commits.sort(key=lambda x: x['date'])
        
        if not all_commits:
            return {}
        
        # Get date range
        first_date = all_commits[0]['date'].date()
        last_date = all_commits[-1]['date'].date()
        
        # Create ideal distribution
        current_date = first_date
        ideal_distribution = {}
        
        while current_date <= last_date:
            ideal_distribution[current_date] = []
            current_date += timedelta(days=1)
        
        # Distribute commits with weekend prioritization while preserving chronological order
        commits_to_distribute = all_commits.copy()
        plan = {}
        sorted_dates = sorted(ideal_distribution.keys())

        day_counts = {}
        for date in sorted_dates:
            rng = random.Random(int(date.strftime('%Y%m%d')))
            is_weekend = date.weekday() >= 5  # Saturday=5, Sunday=6
            day_counts[date] = rng.randint(6, 10) if is_weekend else rng.randint(2, 6)

        total_planned = sum(day_counts.values())
        if total_planned < len(commits_to_distribute):
            deficit = len(commits_to_distribute) - total_planned
            for idx in range(deficit):
                day_counts[sorted_dates[idx % len(sorted_dates)]] += 1

        for date in sorted_dates:
            actual_count = min(day_counts[date], len(commits_to_distribute))
            if actual_count > 0:
                day_commits = commits_to_distribute[:actual_count]
                commits_to_distribute = commits_to_distribute[actual_count:]

                for commit in day_commits:
                    new_datetime = datetime.combine(
                        date,
                        commit['date'].time()
                    ).replace(tzinfo=commit['date'].tzinfo)

                    plan[commit['hash']] = {
                        'old_date': commit['date'],
                        'new_date': new_datetime,
                        'repo': commit['repo'],
                        'message': commit['message']
                    }

        return plan
    
    def print_analysis(self, stats, gaps, date_counts):
        """Print analysis results."""
        print("\n" + "="*60)
        print("CONTRIBUTION ANALYSIS")
        print("="*60)
        
        print(f"\n📊 Statistics:")
        print(f"  Total commits: {stats['total_commits']}")
        print(f"  Days with commits: {stats['days_with_commits']}")
        print(f"  Mean commits/day: {stats['mean']:.2f}")
        print(f"  Median commits/day: {stats['median']:.2f}")
        print(f"  Standard deviation: {stats['std_dev']:.2f}")
        print(f"  Range: {stats['min']} - {stats['max']}")
        
        print(f"\n🕳️  Gaps (>{self.max_gap_days} days):")
        if gaps:
            for gap in gaps:
                print(f"  {gap['start']} → {gap['end']} ({gap['days']} days)")
                print(f"    Before: {gap['commits_before']} commits | After: {gap['commits_after']} commits")
        else:
            print("  No gaps found!")
        
        print("\n" + "="*60)
    
    def print_redistribution_plan(self, plan, original_date_counts):
        """Print the redistribution plan with detailed before/after comparison."""
        print("\n" + "="*60)
        print("REDISTRIBUTION PLAN")
        print("="*60)
        
        if not plan:
            print("\nTotal commits to redistribute: 0")
            print("\n" + "="*60)
            return

        # Group by date
        by_new_date = defaultdict(list)
        for commit_hash, info in plan.items():
            by_new_date[info['new_date'].date()].append(info)
        
        print(f"\nTotal commits to redistribute: {len(plan)}")
        print(f"Date range: {min(by_new_date.keys())} → {max(by_new_date.keys())}")
        
        # Calculate new stats
        counts = [len(commits) for commits in by_new_date.values()]
        new_std = statistics.stdev(counts) if len(counts) > 1 else 0
        
        print(f"\n📈 New distribution:")
        print(f"  Days with commits: {len(by_new_date)}")
        print(f"  Mean commits/day: {statistics.mean(counts):.2f}")
        print(f"  Standard deviation: {new_std:.2f}")
        print(f"  Range: {min(counts)} - {max(counts)}")
        
        # Show newly added green days
        all_dates = sorted(by_new_date.keys())
        first_date = all_dates[0]
        last_date = all_dates[-1]
        
        blank_days_before = []
        current = first_date
        while current <= last_date:
            if current not in original_date_counts or original_date_counts[current] == 0:
                blank_days_before.append(current)
            current += timedelta(days=1)
        
        newly_green_days = [date for date in by_new_date.keys() 
                           if date not in original_date_counts or original_date_counts[date] == 0]
        
        print(f"\n🟩 NEW GREEN DAYS (was blank, now has commits):")
        print(f"  Total: {len(newly_green_days)} days")
        if newly_green_days:
            print(f"\n  Sample of newly added days:")
            for date in sorted(newly_green_days)[:15]:
                day_name = date.strftime('%a')
                weekend = "🎮 WEEKEND" if date.weekday() >= 5 else ""
                print(f"    {date} ({day_name}): {len(by_new_date[date])} commits {weekend}")
            
            if len(newly_green_days) > 15:
                print(f"    ... and {len(newly_green_days) - 15} more days")
        
        print(f"\n⬜ BLANK DAYS REMAINING:")
        remaining_blank = [date for date in blank_days_before if date not in by_new_date]
        print(f"  Total: {len(remaining_blank)} days")
        if remaining_blank and len(remaining_blank) <= 10:
            for date in remaining_blank[:10]:
                print(f"    {date}")
        
        print("\n" + "="*60)
    
    def save_detailed_log(self, plan, date_counts, output_file='redistribution_log.txt'):
        """Save detailed before/after log to file."""
        by_new_date = defaultdict(list)
        for commit_hash, info in plan.items():
            by_new_date[info['new_date'].date()].append(info)
        
        all_dates = sorted(by_new_date.keys())
        if not all_dates:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("GitHub Contribution Redistribution Log\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*70 + "\n\nNo commits in redistribution plan.\n")
            print(f"\n📝 Detailed log saved to: {output_file}")
            return
        first_date = all_dates[0]
        last_date = all_dates[-1]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("GitHub Contribution Redistribution Log\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            f.write("BEFORE REDISTRIBUTION:\n")
            f.write("-" * 70 + "\n")
            current = first_date
            while current <= last_date:
                count = date_counts.get(current, 0)
                status = "✓" if count > 0 else "✗"
                day_name = current.strftime('%a')
                f.write(f"{status} {current} ({day_name:3s}): {count:2d} commits\n")
                current += timedelta(days=1)
            
            f.write("\n" + "="*70 + "\n\n")
            f.write("AFTER REDISTRIBUTION:\n")
            f.write("-" * 70 + "\n")
            current = first_date
            while current <= last_date:
                new_count = len(by_new_date.get(current, []))
                old_count = date_counts.get(current, 0)
                day_name = current.strftime('%a')
                weekend = " [WEEKEND]" if current.weekday() >= 5 else ""
                
                if old_count == 0 and new_count > 0:
                    status = "🟩 NEW"
                elif new_count > 0:
                    status = "✓    "
                else:
                    status = "✗    "
                
                change = f"(+{new_count - old_count})" if new_count != old_count else ""
                f.write(f"{status} {current} ({day_name:3s}): {new_count:2d} commits {change}{weekend}\n")
                current += timedelta(days=1)
            
            f.write("\n" + "="*70 + "\n")
        
        print(f"\n📝 Detailed log saved to: {output_file}")
    
    def generate_rewrite_script(self, plan, output_file='rewrite_history.sh'):
        """Generate a bash script to rewrite git history."""
        script_lines = ['#!/bin/bash', '', 'set -e', '']
        
        # Group by repo
        by_repo = defaultdict(list)
        for commit_hash, info in plan.items():
            by_repo[info['repo']].append((commit_hash, info))
        
        for repo, commits in by_repo.items():
            script_lines.append(f'echo "Processing {repo}..."')
            script_lines.append(f'cd "{repo}"')
            script_lines.append('')
            
            # Create git filter-branch command
            script_lines.append('# Create commit hash to new date mapping')
            script_lines.append('export FILTER_BRANCH_SQUELCH_WARNING=1')
            script_lines.append('')
            
            # Generate the filter command
            script_lines.append('git filter-branch -f --env-filter \'')
            
            for commit_hash, info in commits:
                new_date = info['new_date'].strftime('%a %b %d %H:%M:%S %Y %z')
                script_lines.append(f'if [ "$GIT_COMMIT" = "{commit_hash}" ]; then')
                script_lines.append(f'    export GIT_AUTHOR_DATE="{new_date}"')
                script_lines.append(f'    export GIT_COMMITTER_DATE="{new_date}"')
                script_lines.append('fi')
            
            script_lines.append('\' --all')
            script_lines.append('')
            script_lines.append('echo "✓ Completed!"')
            script_lines.append('')
        
        # Write script
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_lines))
        
        os.chmod(output_file, 0o755)
        print(f"\n✅ Rewrite script generated: {output_file}")
    
    def run(self, base_dir):
        """Main execution flow."""
        print(f"🔍 Searching for repositories in: {base_dir}")
        
        # Find all git repos
        repos = self.find_git_repos(base_dir)
        
        if not repos:
            print(f"❌ No git repositories found in {base_dir}")
            return
        
        print(f"📁 Found {len(repos)} repositories:")
        for repo in repos:
            print(f"  - {os.path.basename(repo)}")
        
        # Collect all commits
        print("\n📥 Collecting commit history...")
        all_commits = []
        
        for repo in repos:
            commits = self.get_commits_from_repo(repo)
            all_commits.extend(commits)
            print(f"  {os.path.basename(repo)}: {len(commits)} commits")
        
        if not all_commits:
            print("❌ No commits found!")
            return
        
        # Store commits by repo
        self.commits_by_date.clear()
        for commit in all_commits:
            repo = commit['repo']
            if repo not in self.commits_by_date:
                self.commits_by_date[repo] = []
            self.commits_by_date[repo].append(commit)
        
        # Analyze
        result = self.analyze_contributions()
        if not result:
            return
        
        stats, gaps, date_counts = result
        self.print_analysis(stats, gaps, date_counts)
        
        # Create redistribution plan
        print("\n🔄 Creating redistribution plan...")
        plan = self.create_redistribution_plan(date_counts)
        
        if not plan:
            print("❌ Could not create redistribution plan!")
            return
        
        self.print_redistribution_plan(plan, date_counts)
        
        # Save detailed log
        self.save_detailed_log(plan, date_counts)
        
        # Generate rewrite script
        self.generate_rewrite_script(plan)
        
        print("\n⚠️  IMPORTANT NOTES:")
        print("  1. Backup your repositories before running the rewrite script!")
        print("  2. This will rewrite git history and require force push")
        print("  3. Run: ./rewrite_history.sh")
        print("  4. Then force push each repo: git push --force --all")
        print("  5. GitHub may take a few minutes to update contribution graph")


if __name__ == '__main__':
    # Get GitHub email from git config or user input
    github_email = None
    try:
        result = subprocess.run(['git', 'config', 'user.email'], 
                              capture_output=True, text=True, check=True)
        github_email = result.stdout.strip()
        print(f"Using email from git config: {github_email}")
    except:
        print("Could not detect git email. All commits will be counted.")
        print("To filter by email, run: git config --global user.email 'your@email.com'")
    
    redistributor = ContributionRedistributor(
        target_std_dev=5, 
        max_gap_days=7,
        github_email=github_email
    )
    
    # Use parent directory of current script location
    base_dir = sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / 'git')
    
    redistributor.run(base_dir)
