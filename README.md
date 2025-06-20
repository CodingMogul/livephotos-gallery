# Live Photos Gallery

Dynamic gallery content for the Live Photos app. This repository hosts the configuration and media files that are downloaded by the app.

## 📁 Repository Structure

```
livephotos-gallery/
├── gallery-config.json          # Main configuration file
├── images/                       # JPEG still images
├── videos/                       # MOV video components
├── thumbnails/                   # Small preview images
├── scripts/                      # Utility scripts
│   └── extract_livephoto.py     # Extract JPEG+MOV from Live Photos
└── README.md                    # This file
```

## 🚀 Quick Setup

### 1. Fork/Clone this Repository

```bash
git clone https://github.com/yourusername/livephotos-gallery.git
cd livephotos-gallery
```

### 2. Install Dependencies (for extraction script)

```bash
# macOS with Homebrew
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows with Chocolatey
choco install ffmpeg
```

### 3. Update App Configuration

In your iOS app, update `GalleryService.swift`:

```swift
private let configurationURL = "https://raw.githubusercontent.com/yourusername/livephotos-gallery/main/gallery-config.json"
```

## 📸 Adding New Live Photos

### Method 1: From Existing Live Photos (HEIC files)

1. **Extract components from Live Photo:**

```bash
python3 scripts/extract_livephoto.py /path/to/your/livephoto.HEIC ocean_sunset
```

This creates:

- `images/ocean_sunset.jpg` (still image)
- `videos/ocean_sunset.mov` (video component)
- `thumbnails/ocean_sunset_thumb.jpg` (thumbnail)

2. **Copy the generated JSON entry** into `gallery-config.json`

3. **Commit and push to GitHub:**

```bash
git add .
git commit -m "Add ocean sunset Live Photo"
git push origin main
```

### Method 2: From Separate Video + Image Files

1. **Prepare your files:**

   - High-quality JPEG image (9:16 aspect ratio recommended)
   - Short MOV video (3-10 seconds, same aspect ratio)

2. **Place files in correct directories:**

   - `images/your_name.jpg`
   - `videos/your_name.mov`

3. **Create thumbnail:**

```bash
ffmpeg -i images/your_name.jpg -vf scale=300:533 -q:v 3 thumbnails/your_name_thumb.jpg
```

4. **Add entry to gallery-config.json**

## 📝 Configuration Format

### Gallery Config Structure

```json
{
  "version": "1.0.0",
  "lastUpdated": "2024-12-19T10:00:00Z",
  "baseURL": "https://raw.githubusercontent.com/yourusername/livephotos-gallery/main",
  "categories": [
    {
      "id": "category_id",
      "name": "Category Name",
      "description": "Category description",
      "items": [...]
    }
  ]
}
```

### Item Structure

```json
{
  "id": "unique_id",
  "title": "Display Title",
  "description": "Item description",
  "imageURL": "images/filename.jpg",
  "videoURL": "videos/filename.mov",
  "thumbnailURL": "thumbnails/filename_thumb.jpg",
  "isPremium": false,
  "tags": ["tag1", "tag2"],
  "duration": 5.0,
  "size": {
    "bytes": 3145728,
    "formatted": "3.0 MB"
  },
  "createdAt": "2024-12-19T10:00:00Z"
}
```

## 🎨 Content Guidelines

### Image Requirements

- **Format:** JPEG
- **Aspect Ratio:** 9:16 (portrait) preferred
- **Resolution:** 1080x1920 or higher
- **Quality:** High (minimal compression)

### Video Requirements

- **Format:** MOV (H.264)
- **Duration:** 3-10 seconds
- **Aspect Ratio:** Same as image (9:16)
- **Frame Rate:** 30fps or 60fps
- **Quality:** High bitrate for smooth playback

### Thumbnail Requirements

- **Format:** JPEG
- **Size:** 300x533 pixels (9:16 ratio)
- **Purpose:** Fast loading preview

## 🔧 Live Photo Extraction Tips

### From iPhone/iPad Photos App

1. Share Live Photo → Save to Files as HEIC
2. Use extraction script to get JPEG + MOV
3. Upload components to repository

### From macOS Photos App

1. Export Live Photo (keep Live Photo data)
2. Results in HEIC file + MOV file
3. Use extraction script on HEIC for JPEG

### Quality Considerations

- Original Live Photos have Apple's metadata
- Extracted files lose some metadata but keep visual quality
- App recreates Live Photo metadata during conversion

## 🚀 Deployment

### GitHub Pages (Recommended)

1. Push files to `main` branch
2. Files available via GitHub's raw content URLs
3. Instant updates when you push changes

### Custom Server

1. Upload files to your web server
2. Update `baseURL` in gallery-config.json
3. Ensure CORS headers allow app access

## 📱 App Integration

The iOS app automatically:

1. Downloads `gallery-config.json` on launch
2. Shows categories and thumbnails
3. Downloads videos when user taps items
4. Combines JPEG + MOV back into Live Photos
5. Caches downloaded content for offline use

## 🆕 Adding New Content (No App Update Required!)

1. **Add new files** to images/, videos/, thumbnails/
2. **Update gallery-config.json** with new entries
3. **Push to GitHub**
4. **App automatically fetches** updates

Users get new content instantly without app store updates!

## 🛠️ Advanced Usage

### Batch Processing

Create multiple Live Photos at once:

```bash
for file in *.HEIC; do
    name=$(basename "$file" .HEIC)
    python3 scripts/extract_livephoto.py "$file" "$name"
done
```

### Custom Categories

Add new categories to organize content:

```json
{
  "id": "seasonal",
  "name": "Seasonal",
  "description": "Holiday and seasonal themes",
  "items": [...]
}
```

### Premium Content

Mark items as premium for monetization:

```json
{
  "isPremium": true,
  "..."
}
```

## 📊 Analytics & Monitoring

Track popular content by monitoring:

- Download frequency per item
- Category popularity
- User engagement metrics

Add analytics endpoints to track usage patterns.

## 🤝 Contributing

1. Fork the repository
2. Add your Live Photo content
3. Test with the extraction script
4. Submit pull request with new content

## 📄 License

Content in this repository is licensed under [your preferred license].
Live Photos are created by users and retain their original copyrights.

---

**Need help?** Open an issue in this repository or check the iOS app documentation.
