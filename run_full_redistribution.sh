#!/bin/bash
set -e
set -o pipefail

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    GitHub Contribution Redistributor - Full Run           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

BASE_DIR="${1:-$HOME/git}"
BACKUP_DIR="$HOME/git_backups_$(date +%Y%m%d_%H%M%S)"

echo "📂 Base directory: $BASE_DIR"
echo "💾 Backup directory: $BACKUP_DIR"
echo ""

read -p "Continue with backup and analysis? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted."
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "STEP 1: Creating backups"
echo "═══════════════════════════════════════════════════════════"
./backup_repos.sh "$BASE_DIR" "$BACKUP_DIR"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "STEP 2: Analyzing contributions and creating plan"
echo "═══════════════════════════════════════════════════════════"
python3 contribution_redistributor.py "$BASE_DIR"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "STEP 3: Review the plan"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "⚠️  IMPORTANT: Review the redistribution plan above!"
echo ""
echo "The script 'rewrite_history.sh' has been generated."
echo ""
read -p "Do you want to execute the rewrite? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted. No changes made."
    echo ""
    echo "Your backups are still at: $BACKUP_DIR"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "STEP 4: Rewriting git history"
echo "═══════════════════════════════════════════════════════════"
./rewrite_history.sh

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "STEP 5: Verify changes (sample repos)"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Checking first modified repository..."
FIRST_REPO=$(grep "cd \"" rewrite_history.sh | head -n 1 | sed 's/cd "\(.*\)"/\1/')
if [ -n "$FIRST_REPO" ]; then
    (
        cd "$FIRST_REPO"
        echo "Repository: $(basename "$FIRST_REPO")"
        echo "Recent commits:"
        git log --oneline --date=short --pretty=format:"%h %ad %s" -10
        echo ""
    )
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "STEP 6: Push to GitHub"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "⚠️  This will FORCE PUSH to GitHub and rewrite remote history!"
echo ""
read -p "Push all changes to GitHub? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Skipping push."
    echo ""
    echo "Changes are local only. To push later, run:"
    echo "  cd <repo> && git push --force --all"
    echo ""
    echo "To restore from backup:"
    echo "  ./restore_from_backup.sh $BACKUP_DIR <repo-name>"
    exit 0
fi

echo ""
echo "Pushing all modified repositories..."
grep "cd \"" rewrite_history.sh | sed 's/cd "\(.*\)"/\1/' | sort -u | while IFS= read -r repo; do
    if [ -d "$repo/.git" ]; then
        echo ""
        echo "📤 Pushing: $(basename "$repo")"
        PUSH_OUT=$(cd "$repo" && git push --force --all 2>&1)
        printf '%s\n' "$PUSH_OUT" | head -n 5
    fi
done

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    ✅ COMPLETE!                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Summary:"
echo "  - Backups saved at: $BACKUP_DIR"
echo "  - History rewritten and pushed to GitHub"
echo "  - Contribution graph will update in 5-10 minutes"
echo ""
echo "🔄 To restore if needed:"
echo "  ./restore_from_backup.sh $BACKUP_DIR <repo-name>"
echo ""
echo "🎉 Your contribution graph should now be beautiful!"
