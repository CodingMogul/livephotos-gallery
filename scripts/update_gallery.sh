#!/bin/bash

# Update Gallery Script
# Automates the process of committing and pushing gallery updates

echo "🎬 Live Photos Gallery Updater"
echo "==============================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "Please run this script from the root of your livephotos-gallery repository"
    exit 1
fi

# Check for changes
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes detected"
    echo "Your gallery is up to date!"
    exit 0
fi

echo "📋 Changes detected:"
git status --short

echo ""
read -p "📝 Enter commit message (or press Enter for default): " commit_message

if [ -z "$commit_message" ]; then
    # Count new files
    new_images=$(git status --porcelain | grep "^??" | grep -c "images/")
    new_videos=$(git status --porcelain | grep "^??" | grep -c "videos/")
    new_thumbnails=$(git status --porcelain | grep "^??" | grep -c "thumbnails/")
    
    if [ $new_images -gt 0 ] || [ $new_videos -gt 0 ]; then
        commit_message="Add new Live Photo content ($new_images images, $new_videos videos)"
    else
        commit_message="Update gallery configuration"
    fi
fi

echo ""
echo "🔄 Staging changes..."
git add .

echo "💾 Committing with message: '$commit_message'"
git commit -m "$commit_message"

echo "📤 Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Gallery updated successfully!"
    echo "🌐 Your changes are now live at:"
    echo "   https://raw.githubusercontent.com/$(git config remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/main/gallery-config.json"
    echo ""
    echo "📱 Users will see the new content next time they open the app!"
else
    echo "❌ Failed to push changes"
    exit 1
fi 