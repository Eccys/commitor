#!/bin/bash

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
echo "$REPOS" | while read repo; do
    if [ -n "$repo" ]; then
        echo "  - $(basename "$repo")"
    fi
done

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

echo "$REPOS" | while read repo; do
    if [ -n "$repo" ] && [ -d "$repo/.git" ]; then
        echo ""
        echo "📤 Pushing: $(basename "$repo")"
        cd "$repo"
        
        if git push --force --all 2>&1 | head -n 10; then
            ((SUCCESS++))
            echo "  ✅ Success"
        else
            ((FAILED++))
            echo "  ❌ Failed"
        fi
    fi
done

echo ""
echo "╔════════════════════════════════════════╗"
echo "║           PUSH COMPLETE!               ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "🎉 Your contribution graph will update in 5-10 minutes!"
echo "🌐 Check: https://github.com/Eccys"
