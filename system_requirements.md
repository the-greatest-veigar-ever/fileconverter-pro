# System Requirements

## Required System Libraries

### Image Processing
- ImageMagick (`imagemagick`)
- FreeType (`freetype`)
- LibJPEG (`libjpeg`)
- LibPNG (`libpng`)
- LibTIFF (`libtiff`)

### Video Processing
- FFmpeg (`ffmpeg`)
- LibAV (`libav-tools`)

### Document Processing
- LibreOffice (`libreoffice`)
- Pandoc (`pandoc`)
- Ghostscript (`ghostscript`)

### Archive Handling
- p7zip (`p7zip-full`)
- UnRAR (`unrar`)
- ZIP (`zip`)

## Installation Instructions

### macOS (using Homebrew)
```bash
# Image processing dependencies
brew install freetype imagemagick

# Video processing dependencies
brew install ffmpeg

# Document processing dependencies
brew install libreoffice pandoc ghostscript

# Archive handling
brew install p7zip
brew install homebrew/cask/unrar
```

### Ubuntu/Debian
```bash
# Image processing dependencies
sudo apt-get update
sudo apt-get install -y imagemagick libmagickwand-dev

# Video processing dependencies
sudo apt-get install -y ffmpeg libav-tools

# Document processing dependencies
sudo apt-get install -y libreoffice pandoc ghostscript

# Archive handling
sudo apt-get install -y p7zip-full unrar zip
```

### CentOS/RHEL
```bash
# Enable EPEL repository
sudo yum install -y epel-release

# Image processing dependencies
sudo yum install -y ImageMagick ImageMagick-devel

# Video processing dependencies
sudo yum install -y ffmpeg

# Document processing dependencies
sudo yum install -y libreoffice pandoc ghostscript

# Archive handling
sudo yum install -y p7zip p7zip-plugins unrar zip
```

## Verification Script

You can verify your system dependencies by running:
```bash
python scripts/check_dependencies.py
```

## Troubleshooting

### ImageMagick Policy Issues
If you encounter ImageMagick permission issues, you might need to update the ImageMagick policy file:

1. Locate your policy file:
   - Usually at `/etc/ImageMagick-6/policy.xml` or `/etc/ImageMagick-7/policy.xml`
2. Add or modify the following policies:
   ```xml
   <policy domain="coder" rights="read|write" pattern="PDF" />
   <policy domain="coder" rights="read|write" pattern="LABEL" />
   ```

### FFmpeg Issues
- Ensure FFmpeg is installed with all necessary codecs
- For macOS: `brew install ffmpeg --with-fdk-aac --with-sdl2 --with-freetype`

### LibreOffice Headless Mode
- Ensure LibreOffice can run in headless mode:
  ```bash
  soffice --headless --convert-to pdf test.docx
  ```

## Environment Variables

Some system configurations require additional environment variables:

```bash
# Add to your .bashrc or .zshrc
export MAGICK_HOME=/usr/local/opt/imagemagick
export DYLD_LIBRARY_PATH=$MAGICK_HOME/lib/
export PATH=$MAGICK_HOME/bin:$PATH
``` 