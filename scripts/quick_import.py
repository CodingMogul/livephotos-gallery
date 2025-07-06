#!/usr/bin/env python3
"""
Quick Import Script for Live Photos Gallery
Quickly adds existing MOV, image, and thumbnail files to the gallery.

Usage:
    python3 quick_import.py <name> <title> [--category nature|abstract] [--premium]
    
Example:
    python3 quick_import.py ocean_sunset "Ocean Sunset" --category nature
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

def get_file_size(filepath):
    """Get file size in bytes"""
    return os.path.getsize(filepath) if os.path.exists(filepath) else 0

def format_bytes(bytes_val):
    """Format bytes into human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"

def get_video_duration(video_path):
    """Get video duration in seconds"""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "quiet", 
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return 5.0  # Default duration

def process_heic_to_jpg(heic_path, jpg_path):
    """Convert HEIC to JPG"""
    print(f"📸 Converting {heic_path} to JPG...")
    subprocess.run([
        "ffmpeg", "-i", str(heic_path), 
        "-vframes", "1", 
        "-q:v", "2",  # High quality
        str(jpg_path), "-y"
    ], check=True, capture_output=True)

def create_thumbnail(source_image, thumb_path):
    """Create thumbnail from image"""
    print(f"🖼️  Creating thumbnail...")
    subprocess.run([
        "ffmpeg", "-i", str(source_image),
        "-vf", "scale=300:533",  # 9:16 aspect ratio
        "-q:v", "3",
        str(thumb_path), "-y"
    ], check=True, capture_output=True)

def quick_import(name, title, category="nature", is_premium=False):
    """Quick import files into gallery"""
    
    # Define file paths
    images_dir = Path("images")
    videos_dir = Path("videos")
    
    # Possible source files
    heic_file = images_dir / f"{name}.HEIC"
    heic_file2 = images_dir / f"{name}.heic"
    mov_file = videos_dir / f"{name}.MOV"
    mov_file2 = videos_dir / f"{name}.mov"
    
    # Check for video file
    video_path = None
    video_extension = None
    if mov_file.exists():
        video_path = mov_file
        video_extension = "MOV"
    elif mov_file2.exists():
        video_path = mov_file2
        video_extension = "mov"
    else:
        print(f"❌ No video file found for {name}")
        return False
    
    # Check for image file (HEIC)
    image_path = None
    image_extension = None
    if heic_file.exists():
        image_path = heic_file
        image_extension = "HEIC"
    elif heic_file2.exists():
        image_path = heic_file2
        image_extension = "heic"
    else:
        print(f"❌ No HEIC image file found for {name}")
        return False
    
    # Get file information
    img_size = get_file_size(image_path)
    mov_size = get_file_size(video_path)
    total_size = img_size + mov_size
    duration = get_video_duration(video_path)
    
    # Create JSON entry - using HEIC as both image and thumbnail
    entry = {
        "id": name.lower().replace(' ', '_'),
        "title": title,
        "description": f"{title} Live Photo",
        "imageURL": f"images/{name}.{image_extension}",
        "videoURL": f"videos/{name}.{video_extension}",
        "thumbnailURL": f"images/{name}.{image_extension}",  # Use same HEIC as thumbnail
        "isPremium": is_premium,
        "tags": [category, "custom"],
        "duration": round(duration, 1),
        "size": {
            "bytes": total_size,
            "formatted": format_bytes(total_size)
        },
        "createdAt": datetime.now().isoformat() + "Z"
    }
    
    print(f"\n✅ Import complete!")
    print(f"   📸 Image: {image_path} ({format_bytes(img_size)})")
    print(f"   🎬 Video: {video_path} ({format_bytes(mov_size)})")
    print(f"   🖼️  Thumbnail: Using same HEIC as image")
    print(f"   ⏱️  Duration: {duration:.1f}s")
    print(f"   📦 Total size: {format_bytes(total_size)}")
    
    print(f"\n📝 JSON entry to add to gallery-config.json:")
    print(json.dumps(entry, indent=2))
    
    return entry

def update_gallery_config(entry, category="labubu"):
    """Automatically update gallery-config.json with new entry"""
    config_path = Path("gallery-config.json")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Find the category
    for cat in config['categories']:
        if cat['id'] == category:
            # Check if item already exists
            existing_ids = [item['id'] for item in cat['items']]
            if entry['id'] not in existing_ids:
                cat['items'].append(entry)
                print(f"\n✅ Added to {category} category in gallery-config.json")
            else:
                print(f"\n⚠️  Item {entry['id']} already exists in {category}")
            break
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
        f.write('\n')  # Add trailing newline

def main():
    parser = argparse.ArgumentParser(description="Quick import Live Photos to gallery")
    parser.add_argument("name", help="File name (without extension)")
    parser.add_argument("title", help="Display title")
    parser.add_argument("--category", default="nature", choices=["nature", "abstract"], 
                        help="Category to add to")
    parser.add_argument("--premium", action="store_true", help="Mark as premium content")
    parser.add_argument("--auto", action="store_true", 
                        help="Automatically update gallery-config.json")
    
    args = parser.parse_args()
    
    print("🚀 Quick Import for Live Photos Gallery")
    print("=" * 40)
    
    entry = quick_import(args.name, args.title, args.category, args.premium)
    
    if entry and args.auto:
        update_gallery_config(entry, args.category)
        print("\n📋 Next steps:")
        print("1. Review the changes")
        print("2. Run: git add -A && git commit -m 'Add {args.title}' && git push")

if __name__ == "__main__":
    main() 