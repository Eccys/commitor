#!/bin/bash
set -o pipefail

echo "📤 Push All Modified Repositories to GitHub"
echo "==========================================="
echo ""

if [ ! -f "rewrite_history.sh" ]; then
    echo "❌ Error: rewrite_history.sh not found!"
    exit 1
fi

# Extract repos from rewrite script
REPOS=$(grep 'cd "' rewrite_history.sh | sed 's/cd "\(.*\)"/\1/' | sort -u)

echo "📋 Found repositories to push:"
while IFS= read -r repo; do
    if [ -n "$repo" ]; then
        echo "  - $(basename "$repo")"
    fi
done <<< "$REPOS"

echo ""
echo "⚠️  WARNING: This will FORCE PUSH and rewrite remote history!"
echo ""
read -p "Continue with force push? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted."
    exit 1
fi

echo ""
SUCCESS=0
FAILED=0

while IFS= read -r repo; do
    if [ -n "$repo" ] && [ -d "$repo/.git" ]; then
        echo ""
        echo "📤 Pushing: $(basename "$repo")"
        if (cd "$repo" && git push --force --all 2>&1 | head -n 10); then
            SUCCESS=$((SUCCESS + 1))
            echo "  ✅ Success"
        else
            FAILED=$((FAILED + 1))
            echo "  ❌ Failed"
        fi
    fi
done <<< "$REPOS"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║           PUSH COMPLETE!               ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "🎉 Your contribution graph will update in 5-10 minutes!"
echo "🌐 Check: https://github.com/Eccys"
