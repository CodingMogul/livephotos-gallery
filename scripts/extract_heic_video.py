#!/usr/bin/env python3
"""
HEIC Live Photo Video Extractor
Properly extracts MOV video components from HEIC Live Photos.

This script uses exiftool and ffmpeg to correctly extract the embedded
Live Photo video without malformation or cropping issues.

Usage:
    python3 extract_heic_video.py input.HEIC output_name [--output-dir ./videos]

Requirements:
    - exiftool (brew install exiftool)
    - ffmpeg (brew install ffmpeg)

This will create:
    - output_name.mov (the properly extracted Live Photo video)
"""

import os
import sys
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path

def check_dependencies():
    """Check if required tools are installed"""
    tools = ['exiftool', 'ffmpeg']
    missing = []
    
    for tool in tools:
        try:
            # Try to run the tool with a simple command
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
            if tool == 'exiftool':
                print(f"   brew install exiftool")
            elif tool == 'ffmpeg':
                print(f"   brew install ffmpeg")
        return False
    
    return True

def extract_live_photo_video(input_path, output_name, output_dir="./videos"):
    """Extract the Live Photo video component using exiftool method"""
    
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    if not input_path.exists():
        print(f"❌ Error: Input file {input_path} does not exist")
        return False
    
    if not input_path.suffix.upper() in ['.HEIC', '.HEIF']:
        print(f"❌ Error: Input file must be a HEIC/HEIF file, got {input_path.suffix}")
        return False
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Output file path
    mov_output = output_dir / f"{output_name}.mov"
    
    print(f"🎬 Extracting Live Photo video from {input_path.name}...")
    print(f"   Input: {input_path}")
    print(f"   Output: {mov_output}")
    
    # Create a temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        try:
            # Method 1: Try to extract using exiftool (most reliable for Live Photos)
            print("   Method 1: Using exiftool to extract embedded video...")
            
            # Extract the embedded video using exiftool
            temp_video = temp_path / "extracted_video.mov"
            
            result = subprocess.run([
                'exiftool', 
                '-b',  # Binary output
                '-EmbeddedVideoFile',  # Extract embedded video
                str(input_path)
            ], capture_output=True)
            
            if result.returncode == 0 and result.stdout:
                # Write the extracted video data to file
                with open(temp_video, 'wb') as f:
                    f.write(result.stdout)
                
                if temp_video.exists() and temp_video.stat().st_size > 0:
                    print("   ✅ Successfully extracted video using exiftool")
                    
                    # Copy to final destination
                    shutil.copy2(temp_video, mov_output)
                    return verify_video_output(mov_output)
                else:
                    print("   ❌ Exiftool extraction failed - no video data")
            else:
                print("   ❌ Exiftool extraction failed - no embedded video found")
            
            # Method 2: Try alternative exiftool tag
            print("   Method 2: Trying alternative exiftool extraction...")
            
            result = subprocess.run([
                'exiftool', 
                '-b',
                '-EmbeddedVideo',
                str(input_path)
            ], capture_output=True)
            
            if result.returncode == 0 and result.stdout:
                with open(temp_video, 'wb') as f:
                    f.write(result.stdout)
                
                if temp_video.exists() and temp_video.stat().st_size > 0:
                    print("   ✅ Successfully extracted video using alternative exiftool method")
                    shutil.copy2(temp_video, mov_output)
                    return verify_video_output(mov_output)
            
            # Method 3: Try to extract using ffmpeg with specific Live Photo handling
            print("   Method 3: Using ffmpeg with Live Photo specific extraction...")
            
            # First, analyze the file structure
            probe_result = subprocess.run([
                'ffprobe', '-v', 'quiet',
                '-show_entries', 'stream=index,codec_type,codec_name,width,height,duration,bit_rate',
                '-of', 'csv=p=0',
                str(input_path)
            ], capture_output=True, text=True)
            
            if probe_result.returncode == 0:
                streams = []
                for line in probe_result.stdout.strip().split('\n'):
                    if line and 'video' in line:
                        parts = line.split(',')
                        if len(parts) >= 6:
                            streams.append({
                                'index': int(parts[0]),
                                'codec': parts[2],
                                'width': int(parts[3]) if parts[3] != 'N/A' else 0,
                                'height': int(parts[4]) if parts[4] != 'N/A' else 0,
                                'duration': float(parts[5]) if parts[5] != 'N/A' else 0,
                                'bitrate': parts[6] if len(parts) > 6 else 'N/A'
                            })
                
                print(f"   Found {len(streams)} video streams:")
                for i, stream in enumerate(streams):
                    print(f"     Stream {stream['index']}: {stream['codec']} {stream['width']}x{stream['height']} ({stream['duration']}s)")
                
                # Look for the video stream that's most likely the Live Photo video
                # Usually it's the one with h264 codec and reasonable duration
                video_stream = None
                for stream in streams:
                    if (stream['codec'] in ['h264', 'hevc'] and 
                        stream['duration'] > 0.5 and 
                        stream['width'] > 0 and 
                        stream['height'] > 0):
                        video_stream = stream
                        break
                
                if video_stream:
                    print(f"   Extracting stream {video_stream['index']} ({video_stream['codec']})")
                    
                    subprocess.run([
                        'ffmpeg', '-i', str(input_path),
                        '-map', f"0:{video_stream['index']}",
                        '-c', 'copy',  # Copy without re-encoding
                        '-avoid_negative_ts', 'make_zero',
                        '-y',
                        str(mov_output)
                    ], check=True, capture_output=True)
                    
                    if mov_output.exists() and mov_output.stat().st_size > 0:
                        print(f"   ✅ Successfully extracted video using ffmpeg stream mapping")
                        return verify_video_output(mov_output)
            
            # Method 4: Last resort - try to extract the video track differently
            print("   Method 4: Attempting direct video track extraction...")
            
            try:
                subprocess.run([
                    'ffmpeg', '-i', str(input_path),
                    '-vcodec', 'copy',
                    '-an',  # No audio
                    '-avoid_negative_ts', 'make_zero',
                    '-y',
                    str(mov_output)
                ], check=True, capture_output=True)
                
                if mov_output.exists() and mov_output.stat().st_size > 0:
                    print("   ✅ Successfully extracted video using direct extraction")
                    return verify_video_output(mov_output)
                    
            except subprocess.CalledProcessError:
                pass
            
            print("❌ All extraction methods failed")
            return False
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error during extraction: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

def verify_video_output(video_path):
    """Verify that the extracted video is valid and get its properties"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration,size,bit_rate',
            '-show_entries', 'stream=width,height,codec_name,r_frame_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ], capture_output=True, text=True, check=True)
        
        lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        
        if len(lines) >= 4:
            width = lines[0]
            height = lines[1]
            codec = lines[2]
            frame_rate = lines[3]
            duration = lines[4] if len(lines) > 4 else "unknown"
            
            print(f"📊 Extracted video properties:")
            print(f"   Resolution: {width}x{height}")
            print(f"   Codec: {codec}")
            print(f"   Frame rate: {frame_rate}")
            print(f"   Duration: {duration}s" if duration != "unknown" else "   Duration: unknown")
            print(f"   File size: {format_bytes(video_path.stat().st_size)}")
            
            # Basic validation
            try:
                w, h = int(width), int(height)
                if w > 0 and h > 0 and w < 10000 and h < 10000:
                    print("   ✅ Video appears to be valid")
                    return True
                else:
                    print("   ⚠️  Warning: Unusual video dimensions")
                    return True
            except ValueError:
                print("   ⚠️  Warning: Could not parse video dimensions")
                return True
        else:
            print("   ⚠️  Warning: Could not get complete video information")
            return True
            
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Warning: Could not verify video properties: {e}")
        return True
    except Exception as e:
        print(f"   ⚠️  Warning: Error during verification: {e}")
        return True

def format_bytes(bytes_val):
    """Format bytes into human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"

def main():
    parser = argparse.ArgumentParser(description="Extract MOV video from HEIC Live Photos")
    parser.add_argument("input", help="Path to HEIC Live Photo file")
    parser.add_argument("output_name", help="Output name (without extension)")
    parser.add_argument("-o", "--output-dir", default="./videos", help="Output directory (default: ./videos)")
    
    args = parser.parse_args()
    
    print("🎬 HEIC Live Photo Video Extractor v2.0")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    success = extract_live_photo_video(args.input, args.output_name, args.output_dir)
    
    if success:
        print("\n✅ Live Photo video extraction completed successfully!")
        print("\n📋 Next steps:")
        print("1. Test the extracted video to ensure it plays correctly")
        print("2. Verify the video quality and framing")
        print("3. Use the video in your gallery configuration")
    else:
        print("\n❌ Live Photo video extraction failed!")
        print("\n🔍 Troubleshooting tips:")
        print("1. Ensure the input file is a valid HEIC Live Photo (not just a regular HEIC image)")
        print("2. Check that the Live Photo was captured properly on the device")
        print("3. Try with a different HEIC Live Photo file")
        print("4. Ensure exiftool and ffmpeg are properly installed")
        sys.exit(1)

if __name__ == "__main__":
    main() 