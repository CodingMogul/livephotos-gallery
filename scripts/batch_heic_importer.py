#!/usr/bin/env python3
"""
HEIC Batch Gallery Importer
Processes folders containing paired HEIC and MOV files for Live Photos.

This script:
1. Processes folders containing paired .HEIC and .MOV files
2. Copies HEIC files to images folder and MOV files to videos folder
3. Updates gallery-config.json with new items linking the pairs
4. Supports tag-based categorization from command line flags

Usage:
    python3 batch_heic_importer.py path/to/folders/* --labubu --custom
    python3 batch_heic_importer.py /path/to/single/folder --nature --scenic --premium

Requirements:
    - ffmpeg (brew install ffmpeg) for video analysis
"""

import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
import re

def check_dependencies():
    """Check if required tools are installed"""
    tools = ['ffmpeg']
    missing = []
    
    for tool in tools:
        try:
            result = subprocess.run([tool, '-version'], capture_output=True, text=True)
            
            if result.returncode != 0:
                missing.append(tool)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)
    
    if missing:
        print(f"❌ Missing required tools: {', '.join(missing)}")
        print("\nTo install missing tools:")
        for tool in missing:
            print(f"   brew install {tool}")
        return False
    
    return True

def copy_video_file(mov_path, output_name, videos_dir):
    """Copy MOV video file to videos directory"""
    mov_path = Path(mov_path)
    videos_dir = Path(videos_dir)
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    mov_output = videos_dir / f"{output_name}.mov"
    
    print(f"   🎬 Copying video file {mov_path.name}...")
    
    try:
        if not mov_path.exists():
            print(f"   ❌ Video file not found: {mov_path}")
            return None
            
        shutil.copy2(mov_path, mov_output)
        
        if mov_output.exists() and mov_output.stat().st_size > 0:
            print(f"   ✅ Successfully copied video: {mov_output.name}")
            return mov_output
        else:
            print(f"   ❌ Failed to copy video file")
            return None
            
    except Exception as e:
        print(f"   ❌ Error copying video file {mov_path.name}: {e}")
        return None

def get_video_duration(video_path):
    """Get video duration in seconds"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ], capture_output=True, text=True, check=True)
        
        duration_str = result.stdout.strip()
        if duration_str and duration_str != 'N/A':
            return float(duration_str)
        return 1.0  # Default for static images
    except:
        return 1.0

def get_file_size(file_path):
    """Get file size in bytes and formatted string"""
    try:
        size_bytes = Path(file_path).stat().st_size
        
        # Format size
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                if unit == 'bytes':
                    formatted = f"{int(size_bytes)} {unit}"
                else:
                    formatted = f"{size_bytes:.1f} {unit}"
                break
            size_bytes /= 1024.0
        else:
            formatted = f"{size_bytes:.1f} TB"
        
        return Path(file_path).stat().st_size, formatted
    except:
        return 0, "0 bytes"

def sanitize_filename(filename):
    """Sanitize filename for use as ID and title"""
    # Remove extension and convert to lowercase
    name = Path(filename).stem.lower()
    # Replace spaces and special chars with underscores
    name = re.sub(r'[^a-z0-9_]', '_', name)
    # Remove multiple underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name

def create_gallery_item(heic_path, video_path, tags, gallery_root, folder_name):
    """Create a gallery item dict for the config"""
    heic_path = Path(heic_path)
    gallery_root = Path(gallery_root)
    
    # Generate ID and title from folder name
    base_name = sanitize_filename(folder_name)
    title = folder_name.replace('_', ' ').title()
    
    # Get file sizes and duration
    image_size_bytes, image_size_formatted = get_file_size(heic_path)
    
    # Determine duration
    if video_path and video_path.exists():
        duration = get_video_duration(video_path)
        video_url = f"videos/{video_path.name}"
    else:
        duration = 1.0
        video_url = ""
    
    # Create gallery item
    item = {
        "id": base_name,
        "title": title,
        "description": f"Live Photo from paired HEIC and MOV files",
        "imageURL": f"images/{heic_path.name}",
        "videoURL": video_url,
        "thumbnailURL": f"images/{heic_path.name}",
        "isPremium": "premium" in tags,
        "tags": tags,
        "duration": round(duration, 1),
        "size": {
            "bytes": image_size_bytes,
            "formatted": image_size_formatted
        },
        "createdAt": datetime.now(timezone.utc).isoformat()
    }
    
    return item

def load_gallery_config(config_path):
    """Load existing gallery config"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create new config if it doesn't exist
        return {
            "version": "1.0.0",
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "baseURL": "https://raw.githubusercontent.com/CodingMogul/livephotos-gallery/master",
            "categories": []
        }

def save_gallery_config(config, config_path):
    """Save gallery config with proper formatting"""
    config["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def find_or_create_category(config, category_name):
    """Find existing category or create new one"""
    # Look for existing category with this name
    for category in config["categories"]:
        if category["id"] == category_name:
            return category
    
    # Create new category
    new_category = {
        "id": category_name,
        "name": category_name.title(),
        "description": f"Beautiful {category_name} scenes",
        "items": []
    }
    
    config["categories"].append(new_category)
    return new_category

def process_intake_folders(folder_paths, tags, gallery_root):
    """Process multiple folders containing paired HEIC and MOV files"""
    gallery_root = Path(gallery_root)
    images_dir = gallery_root / "images"
    videos_dir = gallery_root / "videos"
    config_path = gallery_root / "gallery-config.json"
    
    # Create directories
    images_dir.mkdir(parents=True, exist_ok=True)
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing config
    config = load_gallery_config(config_path)
    
    # Determine category name from first tag, or use 'custom' as default
    category_name = tags[0] if tags else "custom"
    category = find_or_create_category(config, category_name)
    
    processed_items = []
    
    for folder_path in folder_paths:
        folder = Path(folder_path)
        
        if not folder.exists() or not folder.is_dir():
            print(f"❌ Folder not found or not a directory: {folder_path}")
            continue
        
        print(f"\n📁 Processing folder: {folder.name}...")
        
        # Find HEIC and MOV files in the folder
        heic_files = list(folder.glob("*.HEIC")) + list(folder.glob("*.heic"))
        mov_files = list(folder.glob("*.MOV")) + list(folder.glob("*.mov"))
        
        if not heic_files:
            print(f"   ❌ No HEIC files found in {folder.name}")
            continue
            
        if not mov_files:
            print(f"   ❌ No MOV files found in {folder.name}")
            continue
        
        # Use the first HEIC and MOV files found (assumes one pair per folder)
        heic_file = heic_files[0]
        mov_file = mov_files[0]
        
        print(f"   📸 Found HEIC: {heic_file.name}")
        print(f"   🎬 Found MOV: {mov_file.name}")
        
        # Generate output name based on folder name
        output_name = sanitize_filename(folder.name)
        
        # Copy HEIC to images directory
        dest_heic = images_dir / heic_file.name
        if not dest_heic.exists():
            shutil.copy2(heic_file, dest_heic)
            print(f"   ✅ Copied image: {dest_heic.name}")
        else:
            print(f"   ⚠️  Image already exists: {dest_heic.name}")
        
        # Copy MOV to videos directory
        video_path = copy_video_file(mov_file, output_name, videos_dir)
        
        # Create gallery item
        item = create_gallery_item(dest_heic, video_path, tags, gallery_root, folder.name)
        
        # Check if item already exists (by ID)
        existing_item = None
        for i, existing in enumerate(category["items"]):
            if existing["id"] == item["id"]:
                existing_item = i
                break
        
        if existing_item is not None:
            # Update existing item
            category["items"][existing_item] = item
            print(f"   ✅ Updated existing gallery item: {item['id']}")
        else:
            # Add new item
            category["items"].append(item)
            print(f"   ✅ Added new gallery item: {item['id']}")
        
        processed_items.append(item)
    
    # Save updated config
    save_gallery_config(config, config_path)
    
    return processed_items, config_path

def main():
    parser = argparse.ArgumentParser(
        description="Batch process folders containing paired HEIC and MOV files for gallery import",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process multiple folders with tags
  python3 batch_heic_importer.py intake/* --labubu --custom
  
  # Process single folder with premium tag
  python3 batch_heic_importer.py intake/photo_folder --nature --premium
  
  # Process folders in specific directory
  python3 batch_heic_importer.py /path/to/intake/* --scenic
        """
    )
    
    parser.add_argument("folders", nargs="+", help="Folders containing paired HEIC and MOV files (supports wildcards)")
    parser.add_argument("--gallery-root", default=".", help="Gallery root directory (default: current directory)")
    
    # Parse remaining arguments as tags
    args, unknown_args = parser.parse_known_args()
    
    # Extract tags from remaining arguments (anything starting with --)
    tags = []
    for arg in unknown_args:
        if arg.startswith('--'):
            tag = arg[2:]  # Remove --
            if tag:  # Don't add empty tags
                tags.append(tag)
    
    # If no tags provided, add 'custom' as default
    if not tags:
        tags = ['custom']
    
    print("🚀 HEIC Batch Gallery Importer (Folder Mode)")
    print("=" * 50)
    print(f"📁 Gallery root: {Path(args.gallery_root).absolute()}")
    print(f"🏷️  Tags: {', '.join(tags)}")
    print(f"📁 Folders to process: {len(args.folders)}")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Expand folder patterns and filter existing folders
    intake_folders = []
    for pattern in args.folders:
        if '*' in pattern or '?' in pattern:
            # Glob pattern
            from glob import glob
            matches = glob(pattern)
            intake_folders.extend(matches)
        else:
            # Single folder
            intake_folders.append(pattern)
    
    # Filter to existing folders
    existing_folders = [f for f in intake_folders if Path(f).exists() and Path(f).is_dir()]
    
    if not existing_folders:
        print("❌ No folders found!")
        sys.exit(1)
    
    print(f"📋 Found {len(existing_folders)} folders to process")
    
    # Process folders
    try:
        processed_items, config_path = process_intake_folders(existing_folders, tags, args.gallery_root)
        
        print(f"\n✅ Successfully processed {len(processed_items)} items!")
        print(f"📄 Updated gallery config: {config_path}")
        print(f"\n📊 Summary:")
        print(f"   Category: {tags[0] if tags else 'custom'}")
        print(f"   Tags: {', '.join(tags)}")
        print(f"   Items processed: {len(processed_items)}")
        
        # Show items
        print(f"\n📋 Processed items:")
        for item in processed_items:
            video_status = "Live Photo" if item["videoURL"] else "Static image"
            premium_status = " (Premium)" if item["isPremium"] else ""
            print(f"   • {item['title']} - {video_status}{premium_status}")
        
        print(f"\n🎉 Gallery import completed successfully!")
        print(f"\n📋 Next steps:")
        print(f"1. Review the updated gallery-config.json")
        print(f"2. Test the gallery in your app")
        print(f"3. Commit and push changes to your gallery repository")
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()