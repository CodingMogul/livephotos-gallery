#!/usr/bin/env python3
"""
Update all thumbnailURL fields to use imageURL instead of separate thumbnail files
"""

import json
from pathlib import Path

def update_thumbnails():
    config_path = Path("gallery-config.json")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Update all items
    for category in config['categories']:
        for item in category['items']:
            # Update thumbnailURL to match imageURL
            item['thumbnailURL'] = item['imageURL']
            print(f"✅ Updated {item['id']}: thumbnailURL -> {item['imageURL']}")
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
        f.write('\n')
    
    print("\n✅ Gallery config updated! All thumbnails now use the main image.")

if __name__ == "__main__":
    update_thumbnails() 