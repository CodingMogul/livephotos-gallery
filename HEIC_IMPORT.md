# HEIC Live Photo Gallery Importer

A robust and quick solution for streamlining the import of HEIC Live Photos into your gallery configuration.

## Overview

This tool automates the process of:
1. Extracting MOV videos from HEIC Live Photos
2. Copying HEIC files to the images folder
3. Automatically updating `gallery-config.json` with new entries
4. Supporting tag-based categorization and filtering

## Quick Start

### Simple Usage (Recommended)

```bash
# Import HEIC files with tags
./import-heic.sh path/to/photos/*.HEIC --labubu --custom

# Import single file as premium content
./import-heic.sh photo.HEIC --nature --premium

# Import all HEIC files in current directory
./import-heic.sh *.HEIC --scenic
```

### Advanced Usage (Direct Python Script)

```bash
# Use the Python script directly for more control
python3 scripts/batch_heic_importer.py *.HEIC --labubu --custom --premium
```

## How It Works

### File Processing
- **HEIC Files**: Automatically copied to `images/` folder
- **Live Photo Videos**: Extracted using `exiftool` and saved to `videos/` folder
- **Static HEIC Images**: Processed without video extraction
- **Filename Sanitization**: Converts filenames to safe IDs (lowercase, underscores)

### Gallery Integration
- **Auto-categorization**: First tag becomes the category name
- **Smart Metadata**: Automatically generates file sizes, durations, timestamps
- **Duplicate Handling**: Updates existing entries instead of creating duplicates
- **Tag Support**: All command-line flags become tags in the gallery config

### Generated Gallery Items

Each processed HEIC file becomes a gallery item with:
- **ID**: Sanitized filename (e.g., `my_photo_heic` from `My Photo.HEIC`)
- **Title**: Cleaned filename (e.g., `My Photo` from `My Photo.HEIC`)
- **Description**: Generic "Custom Live Photo from HEIC"
- **Tags**: All command-line flags (e.g., `--labubu --custom` → `["labubu", "custom"]`)
- **Premium Status**: Automatically set if `--premium` tag is used
- **File Metadata**: Size, duration, creation timestamp

## Installation

### Prerequisites

Install required tools using Homebrew:

```bash
brew install exiftool ffmpeg
```

### Setup

1. Make the import script executable:
```bash
chmod +x import-heic.sh
```

2. Verify dependencies:
```bash
./import-heic.sh
```

## Examples

### Basic Import with Tags
```bash
# Import labubu photos with custom tag
./import-heic.sh ~/Downloads/labubu*.HEIC --labubu --custom
```

### Premium Content Import
```bash
# Import as premium content
./import-heic.sh premium_photo.HEIC --nature --scenic --premium
```

### Batch Import with Multiple Tags
```bash
# Import multiple files with various tags
./import-heic.sh /path/to/photos/*.HEIC --collection2024 --featured --custom
```

### Category Creation
```bash
# Create new category "wildlife"
./import-heic.sh animal_photos/*.HEIC --wildlife --nature
```

## File Structure After Import

```
livephotos-gallery/
├── images/
│   ├── photo1.HEIC          # Original HEIC files
│   ├── photo2.HEIC
│   └── ...
├── videos/
│   ├── photo1.mov           # Extracted Live Photo videos
│   ├── photo2.mov           # (only if HEIC contains video)
│   └── ...
├── gallery-config.json      # Updated with new entries
└── import-heic.sh          # Import tool
```

## Generated Gallery Config Format

```json
{
  "categories": [
    {
      "id": "labubu",
      "name": "Labubu",
      "description": "Beautiful labubu scenes",
      "items": [
        {
          "id": "my_photo",
          "title": "My Photo",
          "description": "Custom Live Photo from HEIC",
          "imageURL": "images/my_photo.HEIC",
          "videoURL": "videos/my_photo.mov",
          "thumbnailURL": "images/my_photo.HEIC",
          "isPremium": false,
          "tags": ["labubu", "custom"],
          "duration": 2.5,
          "size": {
            "bytes": 1234567,
            "formatted": "1.2 MB"
          },
          "createdAt": "2025-07-15T04:38:02.720502+00:00"
        }
      ]
    }
  ]
}
```

## Tag Usage Guide

### Common Tags
- `--labubu` - Labubu character content
- `--custom` - Custom/user-generated content
- `--nature` - Nature scenes
- `--scenic` - Scenic landscapes
- `--premium` - Premium content (requires subscription)
- `--featured` - Featured/highlighted content

### Tag Behavior
- **First tag** becomes the category name
- **All tags** are added to the item's tags array
- **Premium tag** automatically sets `isPremium: true`
- **Custom tags** can be any name you want

## Troubleshooting

### Common Issues

1. **No video extracted**: The HEIC file is a static image, not a Live Photo
2. **Missing dependencies**: Install `exiftool` and `ffmpeg` using Homebrew
3. **Permission errors**: Ensure the script is executable (`chmod +x import-heic.sh`)
4. **File not found**: Check file paths and use absolute paths if needed

### Debug Information

The script provides detailed output including:
- File processing status
- Video extraction results
- Gallery config updates
- Error messages with troubleshooting tips

### Getting Help

Run the script without arguments to see usage information:
```bash
./import-heic.sh
```

## Integration with Gallery App

After importing HEIC files:

1. **Review** the updated `gallery-config.json`
2. **Test** the gallery in your iOS app
3. **Commit** changes to your gallery repository
4. **Push** to make content available in the app

The app will automatically download and cache the new content when users access the gallery.

## Performance Notes

- **Batch processing**: Processes multiple files efficiently
- **Duplicate detection**: Avoids re-processing existing items
- **Metadata caching**: Stores file information to avoid re-computation
- **Error handling**: Continues processing even if individual files fail

## Advanced Configuration

### Custom Gallery Root
```bash
python3 scripts/batch_heic_importer.py *.HEIC --custom --gallery-root /path/to/gallery
```

### Scripting Integration
The tool can be integrated into automated workflows:

```bash
#!/bin/bash
# Automated HEIC processing pipeline
./import-heic.sh /incoming/heic/*.HEIC --automated --batch-$(date +%Y%m%d)
git add .
git commit -m "Auto-import HEIC batch $(date)"
git push
```