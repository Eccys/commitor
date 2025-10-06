#!/bin/bash
set -e

echo "🚀 Executing Git History Redistribution"
echo "========================================"
echo ""

# Check if rewrite script exists
if [ ! -f "rewrite_history.sh" ]; then
    echo "❌ Error: rewrite_history.sh not found!"
    echo "Run: python3 contribution_redistributor.py ~/git"
    exit 1
fi

echo "📋 This will:"
echo "  1. Rewrite git history in local repos"
echo "  2. You can verify changes before pushing"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted."
    exit 1
fi

echo ""
echo "🔄 Executing rewrite_history.sh..."
./rewrite_history.sh

echo ""
echo "✅ Local history rewritten!"
echo ""
echo "📊 Verify changes in a sample repo:"
echo "  cd ~/git/simplemacro"
echo "  git log --oneline --date=short --pretty=format:'%h %ad %s' -20"
echo ""
echo "📤 To push all changes to GitHub:"
echo "  ./push_all_repos.sh"
echo ""
echo "🔄 To restore from backup:"
echo "  ls ~/git_backups_* # find your backup"
echo "  ./restore_from_backup.sh <backup-dir> <repo-name>"
