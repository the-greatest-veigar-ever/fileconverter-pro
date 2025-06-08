# FileConverter Pro

A powerful and user-friendly file conversion application built with Flask. Convert between 200+ file formats with professional-grade quality.

## Features

- Support for 200+ file formats
- Batch conversion
- Professional-grade output quality
- Secure file handling
- API access
- Modern, responsive UI

## System Requirements

Before installing FileConverter Pro, ensure your system meets the following requirements:

### System Dependencies

The application requires several system libraries for file processing. See [system_requirements.md](system_requirements.md) for detailed instructions.

Quick install for macOS:
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install freetype imagemagick ffmpeg libreoffice pandoc ghostscript p7zip
brew install unar
```

For other operating systems, please refer to [system_requirements.md](system_requirements.md).

### Python Requirements

- Python 3.12 or higher
- pip (Python package installer)
- virtualenv or venv (recommended)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fileconverter-pro.git
   cd fileconverter-pro
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Verify system dependencies:
   ```bash
   python scripts/check_dependencies.py
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Running the Application

1. Start the development server:
   ```bash
   python run.py
   ```

2. Visit http://localhost:5001 in your web browser

## Development

### Setting Up Development Environment

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 style guide. Use flake8 and black for linting and formatting:

```bash
flake8 .
black .
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [ImageMagick](https://imagemagick.org/)
- [FFmpeg](https://ffmpeg.org/)
- [LibreOffice](https://www.libreoffice.org/)
