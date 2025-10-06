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

class ContributionRedistributor:
    def __init__(self, target_std_dev=7, max_gap_days=7):
        self.target_std_dev = target_std_dev
        self.max_gap_days = max_gap_days
        self.repos = []
        self.commits_by_date = defaultdict(list)
        self.redistribution_plan = {}
        
    def find_git_repos(self, base_dir):
        """Find all git repositories in the given directory."""
        base_path = Path(base_dir)
        repos = []
        
        for item in base_path.iterdir():
            if item.is_dir() and (item / '.git').exists():
                repos.append(str(item))
        
        return repos
    
    def get_commits_from_repo(self, repo_path, days_back=365):
        """Extract all commits from a repository for the last N days."""
        os.chdir(repo_path)
        
        # Get date from N days ago
        since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Get commits with author date and hash
        cmd = [
            'git', 'log',
            '--all',
            '--pretty=format:%H|%aI|%s',
            f'--since={since_date}'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commits = []
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                parts = line.split('|', 2)
                if len(parts) >= 3:
                    commit_hash, date_str, message = parts
                    commit_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    
                    commits.append({
                        'hash': commit_hash,
                        'date': commit_date,
                        'message': message,
                        'repo': repo_path,
                        'original_date': commit_date
                    })
            
            return commits
        except subprocess.CalledProcessError as e:
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
        """Create a plan to redistribute commits for uniform distribution."""
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
        total_days = (last_date - first_date).days + 1
        total_commits = len(all_commits)
        
        # Target: spread commits evenly
        target_per_day = total_commits / total_days
        
        # Create ideal distribution
        current_date = first_date
        ideal_distribution = {}
        
        while current_date <= last_date:
            ideal_distribution[current_date] = []
            current_date += timedelta(days=1)
        
        # Distribute commits
        commits_to_distribute = all_commits.copy()
        plan = {}
        
        for date in sorted(ideal_distribution.keys()):
            # Calculate how many commits this day should have
            # Aim for target_per_day, but adjust based on what's available
            target_count = int(target_per_day)
            
            # Add some variation (5-10 range as requested)
            import random
            random.seed(int(date.strftime('%Y%m%d')))  # Consistent randomness
            target_count = random.randint(5, 10)
            
            # Don't go past our commit pool
            actual_count = min(target_count, len(commits_to_distribute))
            
            if actual_count > 0:
                # Take commits from the pool
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
    
    def print_redistribution_plan(self, plan):
        """Print the redistribution plan."""
        print("\n" + "="*60)
        print("REDISTRIBUTION PLAN")
        print("="*60)
        
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
        
        print("\n📅 Sample of new distribution (first 10 days):")
        for date in sorted(list(by_new_date.keys())[:10]):
            print(f"  {date}: {len(by_new_date[date])} commits")
        
        print("\n" + "="*60)
    
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
        with open(output_file, 'w') as f:
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
        
        self.print_redistribution_plan(plan)
        
        # Generate rewrite script
        self.generate_rewrite_script(plan)
        
        print("\n⚠️  IMPORTANT NOTES:")
        print("  1. Backup your repositories before running the rewrite script!")
        print("  2. This will rewrite git history and require force push")
        print("  3. Run: ./rewrite_history.sh")
        print("  4. Then force push each repo: git push --force --all")
        print("  5. GitHub may take a few minutes to update contribution graph")


if __name__ == '__main__':
    redistributor = ContributionRedistributor(target_std_dev=7, max_gap_days=7)
    
    # Use parent directory of current script location
    base_dir = sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / 'git')
    
    redistributor.run(base_dir)
