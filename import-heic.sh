#!/bin/bash

# HEIC Gallery Import Wrapper Script
# Simple wrapper around the Python batch importer for quick usage

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/scripts/batch_heic_importer.py"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: batch_heic_importer.py not found at $PYTHON_SCRIPT"
    exit 1
fi

# Show usage if no arguments
if [ $# -eq 0 ]; then
    echo "🚀 HEIC Gallery Import Tool"
    echo "=========================="
    echo ""
    echo "Usage:"
    echo "  ./import-heic.sh path/to/photos/*.HEIC --tag1 --tag2 [--premium]"
    echo "  ./import-heic.sh photo.HEIC --labubu --custom"
    echo "  ./import-heic.sh /path/to/single/file.HEIC --nature --scenic"
    echo ""
    echo "Examples:"
    echo "  # Import all HEIC files with labubu and custom tags"
    echo "  ./import-heic.sh ~/Downloads/*.HEIC --labubu --custom"
    echo ""
    echo "  # Import single file as premium content"
    echo "  ./import-heic.sh photo.HEIC --nature --premium"
    echo ""
    echo "  # Import files in current directory"
    echo "  ./import-heic.sh *.HEIC --scenic"
    echo ""
    echo "Available tags:"
    echo "  --labubu, --custom, --nature, --scenic, --premium, etc."
    echo "  (You can use any tag name you want)"
    echo ""
    echo "The script will:"
    echo "  1. Extract MOV videos from Live Photos"
    echo "  2. Copy HEIC files to images/ folder"
    echo "  3. Update gallery-config.json with new entries"
    echo "  4. Use tags for categorization and filtering"
    exit 0
fi

# Set gallery root to current directory
export GALLERY_ROOT="$SCRIPT_DIR"

echo "🚀 Running HEIC Gallery Importer..."
echo "Gallery root: $GALLERY_ROOT"
echo ""

# Run the Python script with all arguments
python3 "$PYTHON_SCRIPT" --gallery-root "$GALLERY_ROOT" "$@"

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Import completed successfully!"
else
    echo ""
    echo "❌ Import failed!"
    exit 1
fi