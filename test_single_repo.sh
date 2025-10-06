#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: ./test_single_repo.sh <repo-name>"
    echo "Example: ./test_single_repo.sh simplemacro"
    exit 1
fi

REPO_NAME="$1"
REPO_PATH="$HOME/git/$REPO_NAME"
BACKUP_DIR="$HOME/git_test_backup_$(date +%Y%m%d_%H%M%S)"

if [ ! -d "$REPO_PATH" ]; then
    echo "❌ Repository not found: $REPO_PATH"
    exit 1
fi

echo "🧪 Testing on: $REPO_NAME"
echo ""

echo "1️⃣ Creating backup..."
mkdir -p "$BACKUP_DIR"
cd "$REPO_PATH"
git bundle create "$BACKUP_DIR/${REPO_NAME}.bundle" --all
cp -r "$REPO_PATH" "$BACKUP_DIR/${REPO_NAME}_copy"
echo "   ✅ Backup saved to: $BACKUP_DIR"
echo ""

echo "2️⃣ Current remote URL:"
git remote -v | head -n 1
echo ""

echo "3️⃣ Current git log (last 5 commits):"
git log --oneline -5
echo ""

echo "📋 Ready to proceed!"
echo ""
echo "Next steps:"
echo "  1. Review the backup location above"
echo "  2. Run: python3 contribution_redistributor.py $REPO_PATH"
echo "  3. Review the generated rewrite_history.sh"
echo "  4. Run: ./rewrite_history.sh"
echo "  5. Check with: git log --oneline -10"
echo "  6. If happy: git push --force --all"
echo "  7. If unhappy: ./restore_from_backup.sh $BACKUP_DIR $REPO_NAME"
