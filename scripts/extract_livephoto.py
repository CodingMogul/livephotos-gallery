#!/usr/bin/env python3
"""
Live Photo Extractor
Extracts JPEG and MOV files from Live Photos for gallery use.

Usage:
    python3 extract_livephoto.py /path/to/livephoto.HEIC output_name

This will create:
    - output_name.jpg (the still image)
    - output_name.mov (the video component)
    - output_name_thumb.jpg (thumbnail for gallery)
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def extract_livephoto(input_path, output_name, output_dir="./"):
    """Extract JPEG and MOV components from a Live Photo"""
    
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    if not input_path.exists():
        print(f"❌ Error: Input file {input_path} does not exist")
        return False
        
    # Create output directories
    images_dir = output_dir / "images"
    videos_dir = output_dir / "videos" 
    thumbnails_dir = output_dir / "thumbnails"
    
    for dir_path in [images_dir, videos_dir, thumbnails_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Output file paths
    jpg_output = images_dir / f"{output_name}.jpg"
    mov_output = videos_dir / f"{output_name}.mov"
    thumb_output = thumbnails_dir / f"{output_name}_thumb.jpg"
    
    try:
        # Extract JPEG (still image)
        print(f"📸 Extracting JPEG from {input_path.name}...")
        subprocess.run([
            "ffmpeg", "-i", str(input_path), 
            "-vframes", "1", 
            "-q:v", "2",  # High quality
            str(jpg_output)
        ], check=True, capture_output=True)
        
        # Extract MOV (video component) 
        print(f"🎬 Extracting MOV from {input_path.name}...")
        subprocess.run([
            "ffmpeg", "-i", str(input_path),
            "-c", "copy",  # Copy without re-encoding
            "-map", "0:1",  # Select video stream (usually stream 1)
            str(mov_output)
        ], check=True, capture_output=True)
        
        # Create thumbnail (resized version of JPEG)
        print(f"🖼️  Creating thumbnail...")
        subprocess.run([
            "ffmpeg", "-i", str(jpg_output),
            "-vf", "scale=300:533",  # 9:16 aspect ratio, 300px width
            "-q:v", "3",
            str(thumb_output)
        ], check=True, capture_output=True)
        
        print(f"✅ Successfully extracted Live Photo components:")
        print(f"   📸 Image: {jpg_output}")
        print(f"   🎬 Video: {mov_output}")
        print(f"   🖼️  Thumbnail: {thumb_output}")
        
        # Get file sizes for JSON config
        jpg_size = jpg_output.stat().st_size
        mov_size = mov_output.stat().st_size
        total_size = jpg_size + mov_size
        
        print(f"\n📊 File sizes:")
        print(f"   JPEG: {format_bytes(jpg_size)}")
        print(f"   MOV: {format_bytes(mov_size)}")
        print(f"   Total: {format_bytes(total_size)}")
        
        # Get video duration
        duration = get_video_duration(str(mov_output))
        print(f"   Duration: {duration:.1f}s")
        
        # Generate JSON entry
        print(f"\n📝 JSON configuration entry:")
        print(generate_json_entry(output_name, total_size, duration))
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running ffmpeg: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_video_duration(video_path):
    """Get video duration in seconds"""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "quiet", 
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return 5.0  # Default duration

def format_bytes(bytes_val):
    """Format bytes into human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"

def generate_json_entry(name, total_size, duration):
    """Generate a JSON entry for the gallery config"""
    formatted_size = format_bytes(total_size)
    
    return f"""{{
  "id": "{name.lower().replace(' ', '_')}",
  "title": "{name.title()}",
  "description": "Description for {name}",
  "imageURL": "images/{name}.jpg",
  "videoURL": "videos/{name}.mov",
  "thumbnailURL": "thumbnails/{name}_thumb.jpg",
  "isPremium": false,
  "tags": ["tag1", "tag2"],
  "duration": {duration:.1f},
  "size": {{
    "bytes": {total_size},
    "formatted": "{formatted_size}"
  }},
  "createdAt": "2024-12-19T10:00:00Z"
}}"""

def main():
    parser = argparse.ArgumentParser(description="Extract JPEG and MOV from Live Photos")
    parser.add_argument("input", help="Path to Live Photo (.HEIC file)")
    parser.add_argument("output_name", help="Output name (without extension)")
    parser.add_argument("-o", "--output-dir", default="./", help="Output directory")
    
    args = parser.parse_args()
    
    print("🔄 Live Photo Extractor")
    print("=" * 40)
    
    success = extract_livephoto(args.input, args.output_name, args.output_dir)
    
    if success:
        print("\n✅ Extraction completed successfully!")
        print("\n📋 Next steps:")
        print("1. Review the generated files")
        print("2. Copy the JSON entry above into your gallery-config.json")
        print("3. Commit and push to your GitHub repository")
    else:
        print("\n❌ Extraction failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 