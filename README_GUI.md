# AI Choir Generator GUI

A cross-platform desktop application for generating choir-like audio from a single vocal input using AI voice models.

## Features

- Upload WAV files for choir generation
- Customize configuration parameters
- Specify output directory
- Progress tracking during generation
- Cross-platform (works on both macOS and Windows)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or download this repository**

2. **Install dependencies**

   ```bash
   # Install GUI dependencies
   pip install -r requirements_gui.txt
   
   # Install main script dependencies
   pip install -r requirements.txt
   ```

3. **Download models (if needed)**

   ```bash
   python download_models.py
   ```

## Packaging the Application

### For macOS

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for full details. Short version:

```bash
./build_mac.sh
```

This builds `dist/ai_choir.app`, signs it with your Developer ID (auto-detected
from the keychain), and produces a signed `dist/ai_choir.dmg` (~4 GB). The
voice models and speech encoder are bundled inside the app, so the DMG is
fully self-contained — make sure you've run `download_models.py` first.

To also notarize (so recipients don't need to right-click > Open), set up
credentials once and pass `NOTARY_PROFILE` — see the header of `build_mac.sh`.

### For Windows

1. Run the build script:
   ```bash
   build_windows.bat
   ```

2. The packaged application will be available in the `dist` folder as `AI_Choir_Generator.exe`

Note: For a more professional Windows installer, you can use NSIS (Nullsoft Scriptable Install System) to create an installer. Uncomment the NSIS line in `build_windows.bat` and install NSIS to use this feature.

## Running the Application

### On macOS

```bash
python app_gui.py
```

### On Windows

```bash
python app_gui.py
```

## Using the Application

1. **Select Input File**: Click the "Browse" button in the "Input Audio File" section to select a WAV file.

2. **Choose Output Directory**: Specify where you want the generated files to be saved.

3. **Adjust Configuration**: Modify the settings as needed:
   - Convolution reverb dry/wet mix
   - Stereo spread
   - Voice gain levels
   - And more...

4. **Generate**: Click the "Generate Choir" button to start the process.

5. **View Results**: When processing is complete, check the output directory for the generated files.

## Troubleshooting

- **Missing Models**: Ensure you've run the `download_models.py` script to download required models.
- **Audio Problems**: Make sure your input is a valid WAV file with clean vocals.
- **Script Errors**: Check the error message and ensure all dependencies are properly installed.

## License

[Your License Information]