#!/bin/bash
# Backup all git repositories before rewriting history

set -e

# Configuration
BASE_DIR="${1:-$HOME/git}"
BACKUP_DIR="${2:-$HOME/git_backups_$(date +%Y%m%d_%H%M%S)}"

echo "🔒 Creating backups of all repositories..."
echo "Source: $BASE_DIR"
echo "Backup: $BACKUP_DIR"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Find and backup all git repos
for repo in "$BASE_DIR"/*; do
    if [ -d "$repo/.git" ]; then
        repo_name=$(basename "$repo")
        echo "📦 Backing up: $repo_name"
        
        # Create bundle (includes all branches, tags, etc.)
        cd "$repo"
        git bundle create "$BACKUP_DIR/${repo_name}.bundle" --all
        
        # Also create a tar backup
        cd "$BASE_DIR"
        tar -czf "$BACKUP_DIR/${repo_name}.tar.gz" "$repo_name"
        
        echo "  ✓ Saved to $BACKUP_DIR/${repo_name}.*"
    fi
done

echo ""
echo "✅ Backup complete!"
echo "Backup location: $BACKUP_DIR"
echo ""
echo "To restore a repository:"
echo "  git clone /path/to/backup/repo.bundle restored-repo"
