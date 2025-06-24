#!/usr/bin/env python3
"""
Update gallery config to use HEIC files instead of JPG
"""

import json
from pathlib import Path

def update_to_heic():
    config_path = Path("gallery-config.json")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Update all items
    updated_count = 0
    for category in config['categories']:
        items_to_keep = []
        for item in category['items']:
            # Check if HEIC file exists
            heic_path = Path(f"images/{item['id']}.HEIC")
            if heic_path.exists():
                # Update to use HEIC
                item['imageURL'] = f"images/{item['id']}.HEIC"
                item['thumbnailURL'] = f"images/{item['id']}.HEIC"
                items_to_keep.append(item)
                print(f"✅ Updated {item['id']} to use HEIC")
                updated_count += 1
            else:
                print(f"❌ Skipping {item['id']} - no HEIC file found")
        
        # Only keep items that have HEIC files
        category['items'] = items_to_keep
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
        f.write('\n')
    
    print(f"\n✅ Gallery config updated! {updated_count} items now use HEIC files.")

if __name__ == "__main__":
    update_to_heic() 