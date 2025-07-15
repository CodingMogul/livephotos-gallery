#!/usr/bin/env python3
"""
HEIC Batch Gallery Importer
Processes HEIC Live Photos in batch and adds them to the gallery config.

This script:
1. Extracts MOV videos from HEIC Live Photos
2. Copies HEIC files to images folder
3. Updates gallery-config.json with new items
4. Supports tag-based categorization from command line flags

Usage:
    python3 batch_heic_importer.py path/to/heic/files/*.HEIC --labubu --custom
    python3 batch_heic_importer.py /path/to/single/file.HEIC --nature --scenic --premium

Requirements:
    - exiftool (brew install exiftool)
    - ffmpeg (brew install ffmpeg)
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
    tools = ['exiftool', 'ffmpeg']
    missing = []
    
    for tool in tools:
        try:
            if tool == 'exiftool':
                result = subprocess.run([tool, '-ver'], capture_output=True, text=True)
            else:  # ffmpeg
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

def extract_video_from_heic(heic_path, output_name, videos_dir):
    """Extract MOV video from HEIC Live Photo"""
    heic_path = Path(heic_path)
    videos_dir = Path(videos_dir)
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    mov_output = videos_dir / f"{output_name}.mov"
    
    print(f"   🎬 Extracting video from {heic_path.name}...")
    
    # Use exiftool to extract embedded video
    try:
        result = subprocess.run([
            'exiftool', 
            '-b',  # Binary output
            '-EmbeddedVideoFile',  # Extract embedded video
            str(heic_path)
        ], capture_output=True)
        
        if result.returncode == 0 and result.stdout and len(result.stdout) > 0:
            # Write the extracted video data to file
            with open(mov_output, 'wb') as f:
                f.write(result.stdout)
            
            if mov_output.exists() and mov_output.stat().st_size > 0:
                print(f"   ✅ Successfully extracted video: {mov_output.name}")
                return mov_output
            else:
                print(f"   ⚠️  No video found in {heic_path.name} (static HEIC)")
                return None
        else:
            print(f"   ⚠️  No video found in {heic_path.name} (static HEIC)")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error extracting video from {heic_path.name}: {e}")
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

def create_gallery_item(heic_path, video_path, tags, gallery_root):
    """Create a gallery item dict for the config"""
    heic_path = Path(heic_path)
    gallery_root = Path(gallery_root)
    
    # Generate ID and title from filename
    base_name = sanitize_filename(heic_path.name)
    title = heic_path.stem.replace('_', ' ').title()
    
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
        "description": f"Custom Live Photo from HEIC",
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

def process_heic_files(heic_files, tags, gallery_root):
    """Process multiple HEIC files"""
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
    
    for heic_file in heic_files:
        heic_path = Path(heic_file)
        
        if not heic_path.exists():
            print(f"❌ File not found: {heic_file}")
            continue
        
        if not heic_path.suffix.upper() in ['.HEIC', '.HEIF']:
            print(f"❌ Skipping non-HEIC file: {heic_file}")
            continue
        
        print(f"\n📸 Processing {heic_path.name}...")
        
        # Generate output name
        output_name = sanitize_filename(heic_path.name)
        
        # Copy HEIC to images directory
        dest_heic = images_dir / heic_path.name
        if not dest_heic.exists():
            shutil.copy2(heic_path, dest_heic)
            print(f"   ✅ Copied image: {dest_heic.name}")
        else:
            print(f"   ⚠️  Image already exists: {dest_heic.name}")
        
        # Extract video if it's a Live Photo
        video_path = extract_video_from_heic(heic_path, output_name, videos_dir)
        
        # Create gallery item
        item = create_gallery_item(dest_heic, video_path, tags, gallery_root)
        
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
        description="Batch process HEIC Live Photos for gallery import",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process multiple files with tags
  python3 batch_heic_importer.py *.HEIC --labubu --custom
  
  # Process single file with premium tag
  python3 batch_heic_importer.py photo.HEIC --nature --premium
  
  # Process files in specific directory
  python3 batch_heic_importer.py /path/to/photos/*.HEIC --scenic
        """
    )
    
    parser.add_argument("files", nargs="+", help="HEIC files to process (supports wildcards)")
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
    
    print("🚀 HEIC Batch Gallery Importer")
    print("=" * 50)
    print(f"📁 Gallery root: {Path(args.gallery_root).absolute()}")
    print(f"🏷️  Tags: {', '.join(tags)}")
    print(f"📸 Files to process: {len(args.files)}")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Expand file patterns and filter existing files
    heic_files = []
    for pattern in args.files:
        if '*' in pattern or '?' in pattern:
            # Glob pattern
            from glob import glob
            matches = glob(pattern)
            heic_files.extend(matches)
        else:
            # Single file
            heic_files.append(pattern)
    
    # Filter to existing files
    existing_files = [f for f in heic_files if Path(f).exists()]
    
    if not existing_files:
        print("❌ No HEIC files found!")
        sys.exit(1)
    
    print(f"📋 Found {len(existing_files)} files to process")
    
    # Process files
    try:
        processed_items, config_path = process_heic_files(existing_files, tags, args.gallery_root)
        
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