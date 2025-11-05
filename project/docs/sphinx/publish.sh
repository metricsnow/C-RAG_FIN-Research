#!/bin/bash
# Script to publish Sphinx documentation to GitHub Pages

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
BRANCH="gh-pages"

echo "Building Sphinx documentation..."
cd "$SCRIPT_DIR"
source "$PROJECT_ROOT/venv/bin/activate" || {
    echo "Warning: Virtual environment not found. Continuing without activation."
}
sphinx-build -b html source build

# Create .nojekyll file if it doesn't exist
touch "$BUILD_DIR/.nojekyll"

# Check if we're in a git repository
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "Error: Not in a git repository. Cannot publish to GitHub Pages."
    exit 1
fi

cd "$PROJECT_ROOT"

# Check if gh-pages branch exists
if git show-ref --verify --quiet refs/heads/$BRANCH; then
    echo "gh-pages branch exists. Updating..."
    git checkout $BRANCH
    git pull origin $BRANCH || true
else
    echo "Creating gh-pages branch..."
    git checkout --orphan $BRANCH
    git rm -rf . || true
fi

# Copy build files to root (for gh-pages branch)
echo "Copying documentation files..."
cp -r "$BUILD_DIR"/* .

# Stage and commit
git add -A
if git diff --staged --quiet; then
    echo "No changes to commit."
else
    git commit -m "Update documentation [auto-generated]"
    echo "Documentation committed to gh-pages branch."
    echo ""
    echo "To publish:"
    echo "  git push origin gh-pages"
    echo ""
    echo "Then enable GitHub Pages in repository settings:"
    echo "  Settings > Pages > Source: gh-pages branch"
fi

# Switch back to original branch
git checkout main || git checkout master || echo "Note: Return to your working branch manually"

echo ""
echo "Documentation is ready to publish!"
echo "Next steps:"
echo "1. Review changes: git diff gh-pages"
echo "2. Push to GitHub: git push origin gh-pages"
echo "3. Enable GitHub Pages in repository settings"

