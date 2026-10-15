#!/bin/bash
set -e

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./restore_from_backup.sh <backup-dir> <repo-name>"
    echo "Example: ./restore_from_backup.sh ~/git_backups_20251006 simplemacro"
    exit 1
fi

BACKUP_DIR="$(cd "$1" && pwd)"
REPO_NAME="$(basename "$2")"
if [ -z "$REPO_NAME" ] || [ "$REPO_NAME" = "." ] || [ "$REPO_NAME" = ".." ]; then
    echo "❌ Invalid repository name: $2"
    exit 1
fi
REPO_PATH="$HOME/git/$REPO_NAME"

echo "🔄 Restoring $REPO_NAME from backup..."
echo ""

if [ ! -f "$BACKUP_DIR/${REPO_NAME}.bundle" ]; then
    echo "❌ Backup not found: $BACKUP_DIR/${REPO_NAME}.bundle"
    exit 1
fi

echo "1️⃣ Removing current repository..."
rm -rf "${REPO_PATH:?}"

echo "2️⃣ Restoring from bundle..."
git clone "$BACKUP_DIR/${REPO_NAME}.bundle" "$REPO_PATH"

echo "3️⃣ Re-adding remote..."
cd "$REPO_PATH"
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE_URL" ]; then
    echo "   ⚠️  No remote found. You may need to add it manually:"
    echo "   git remote add origin <url>"
else
    echo "   ✅ Remote: $REMOTE_URL"
fi

echo ""
echo "✅ Repository restored!"
echo ""
echo "Verify with:"
echo "  cd $REPO_PATH"
echo "  git log --oneline -5"
echo ""
echo "To restore to GitHub:"
echo "  git push --force --all"
