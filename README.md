# GitHub Contribution Redistributor

Automatically redistribute your GitHub contributions to fill gaps and maintain consistent activity with low standard deviation.

## What This Does

This tool analyzes your git commit history from the last 365 days and redistributes commits to:
- ✅ Fill gaps larger than 7 days
- ✅ Maintain low standard deviation (5-10 commits per day)
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

## Example Output

```
📊 Statistics:
  Total commits: 487
  Days with commits: 156
  Mean commits/day: 3.12
  Standard deviation: 8.45
  Range: 1 - 43

🕳️ Gaps (>7 days):
  2024-11-06 → 2024-11-21 (15 days)
    Before: 13 commits | After: 6 commits
  
📈 New distribution:
  Days with commits: 312
  Mean commits/day: 1.56
  Standard deviation: 2.14
  Range: 5 - 10
```

## Configuration

Edit the script to adjust parameters:

```python
redistributor = ContributionRedistributor(
    target_std_dev=7,    # Target standard deviation
    max_gap_days=7       # Maximum allowed gap
)
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
