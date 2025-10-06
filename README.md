# GitHub Contribution Redistributor

Automatically redistribute your GitHub contributions to fill gaps and maintain consistent activity with low standard deviation.

## What This Does

This tool analyzes your git commit history from the last 365 days and redistributes commits to:
- ✅ Fill gaps larger than 7 days
- ✅ Maintain low standard deviation (4-6 commits per day)
- ✅ **Prioritize weekends** (6-10 commits) over weekdays (2-6 commits)
- ✅ **Filter by your GitHub email** (only counts YOUR commits)
- ✅ Create a more uniform contribution graph
- ✅ Give you more green squares! 🟩

## How It Works

1. **Analyzes** all commits from your local repositories
2. **Identifies** gaps in your contribution history
3. **Creates a redistribution plan** to spread commits evenly
4. **Generates a script** to rewrite git history with new dates
5. **Preserves** commit messages, authors, and content

## Requirements

- Python 3.6+
- Git
- Local clones of your GitHub repositories

## Usage

### Step 1: Backup Your Repositories

**IMPORTANT:** Always backup before rewriting history!

```bash
chmod +x backup_repos.sh
./backup_repos.sh ~/git ~/git_backups
```

### Step 2: Run the Analyzer

```bash
python3 contribution_redistributor.py ~/git
```

This will:
- Scan all git repositories in `~/git`
- Analyze contribution patterns
- Display current statistics and gaps
- Generate a redistribution plan
- Create `rewrite_history.sh` script

### Step 3: Review the Plan

The tool will show you:
- Current contribution statistics
- Identified gaps
- New distribution plan
- Expected standard deviation

**Review this carefully before proceeding!**

### Step 4: Rewrite History

```bash
chmod +x rewrite_history.sh
./rewrite_history.sh
```

This will rewrite git history for all affected repositories.

### Step 5: Force Push to GitHub

For each repository that was modified:

```bash
cd ~/git/your-repo
git push --force --all
```

⚠️ **Warning:** Force pushing rewrites remote history. Only do this on repositories you own!

### Step 6: Wait for GitHub to Update

GitHub's contribution graph may take a few minutes to update after force pushing.

## Features

### 🎯 Email Filtering
Automatically detects your GitHub email from `git config user.email` and **only counts commits authored by you**. This prevents counting commits from:
- Forked repositories
- Cloned open-source projects
- Collaborator commits
- Dependencies with bundled repos

### 🎮 Weekend Prioritization
- **Weekdays (Mon-Fri):** 2-6 commits per day
- **Weekends (Sat-Sun):** 6-10 commits per day

This creates a realistic activity pattern where you appear more active on weekends!

### 📊 Detailed Before/After Logging
Generates `redistribution_log.txt` with:
- ✅ Complete before/after comparison for every day
- 🟩 **NEW GREEN DAYS** clearly marked (was blank, now has commits)
- ⬜ Remaining blank days
- 🎮 Weekend indicators
- Commit count changes (+X) for each day

Example:
```
✗ 2024-08-17 (Sat):  0 commits     BEFORE
🟩 NEW 2024-08-17 (Sat):  8 commits (+8) [WEEKEND]     AFTER
```

## Example Output

```
Using email from git config: 73040912+Eccys@users.noreply.github.com

📊 Statistics:
  Total commits: 114
  Days with commits: 32
  Mean commits/day: 3.56
  Standard deviation: 3.55
  Range: 1 - 13

🕳️ Gaps (>7 days): 11 gaps found
  
📈 New distribution:
  Days with commits: 23
  Mean commits/day: 4.96
  Standard deviation: 2.36
  Range: 2 - 10
```

## Configuration

Edit the script to adjust parameters:

```python
redistributor = ContributionRedistributor(
    target_std_dev=5,              # Target standard deviation (4-6 range)
    max_gap_days=7,                # Maximum allowed gap
    github_email="your@email.com" # Filter commits by email
)
```

### Weekend/Weekday Ratio

To adjust the weekend prioritization, edit lines 168-171 in the script:

```python
if is_weekend:
    target_count = random.randint(6, 10)  # Weekend commits
else:
    target_count = random.randint(2, 6)   # Weekday commits
```

## Safety Features

- Automatic backup script included
- Dry-run analysis before any changes
- Generated rewrite script can be reviewed
- Clear warnings about force pushing

## Restoring from Backup

If something goes wrong:

```bash
# Restore from bundle
git clone /path/to/backup/repo.bundle restored-repo

# Or extract from tar
tar -xzf /path/to/backup/repo.tar.gz
```

## Important Notes

### ⚠️ Warnings

1. **Collaboration**: Don't do this on repos with collaborators
2. **Force Push**: Required - will overwrite remote history
3. **Private Repos**: Won't show unless you enable "Private contributions" in GitHub settings
4. **Branches**: All branches will be affected
5. **CI/CD**: May trigger workflows if you have automation

### 📝 Best Practices

- Only run on repos you own
- Backup everything first
- Review the redistribution plan
- Test on one repo first
- Inform collaborators (if any)

### 🔧 Troubleshooting

**"No commits found"**
- Check that repositories exist in the specified directory
- Ensure repos have commits in the last 365 days

**"Force push rejected"**
- You may need to temporarily disable branch protection
- Ensure you have write access to the repository

**"Contribution graph not updating"**
- Wait 5-10 minutes for GitHub to refresh
- Ensure repos are public or private contributions are enabled
- Check that commit author email matches your GitHub email

## How Git History Rewriting Works

The tool uses `git filter-branch` to rewrite commit dates:

```bash
git filter-branch --env-filter '
if [ "$GIT_COMMIT" = "abc123..." ]; then
    export GIT_AUTHOR_DATE="Mon Oct 6 12:00:00 2025 +0000"
    export GIT_COMMITTER_DATE="Mon Oct 6 12:00:00 2025 +0000"
fi
' --all
```

This preserves:
- ✅ Commit content
- ✅ Commit messages
- ✅ File changes
- ✅ Commit authors

Changes:
- 📅 Author date
- 📅 Committer date

## License

MIT - Do whatever you want with it!

## Disclaimer

This tool rewrites git history. Use at your own risk. The author is not responsible for any issues arising from its use.
