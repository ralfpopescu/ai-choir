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

1. Install create-dmg (required for creating DMG files):
   ```bash
   brew install create-dmg
   ```

2. Run the build script:
   ```bash
   chmod +x build_mac.sh
   ./build_mac.sh
   ```

3. The packaged application will be available in the `dist` folder as `AI_Choir_Generator.app`
4. A DMG installer will be created in the root directory

### For Windows

1. Run the build script:
   ```bash
   build_windows.bat
   ```

2. The packaged application will be available in the `dist` folder as `AI_Choir_Generator.exe`

Note: For a more professional Windows installer, you can use NSIS (Nullsoft Scriptable Install System) to create an installer. Uncomment the NSIS line in `build_windows.bat` and install NSIS to use this feature.

### Code Signing for macOS

To distribute your application on macOS, you'll need to sign it with your Apple Developer ID. Here's how:

1. **Get an Apple Developer ID**
   - Sign up for the [Apple Developer Program](https://developer.apple.com/programs/)
   - Create a Developer ID Application certificate in Xcode or using the Apple Developer website

2. **Find your Developer ID**
   ```bash
   security find-identity -v -p codesigning
   ```
   This will show your Developer ID in the format: `Developer ID Application: Your Name (TEAM_ID)`

3. **Sign your application**
   ```bash
   chmod +x sign_mac.sh
   ./sign_mac.sh "Developer ID Application: Your Name (TEAM_ID)"
   ```

4. **Notarize your application** (optional but recommended)
   ```bash
   xcrun notarytool submit AI_Choir_Generator.dmg --apple-id "your.email@example.com" --password "app-specific-password" --team-id "TEAM_ID"
   ```

Note: For notarization, you'll need to:
- Enable 2FA on your Apple ID
- Generate an app-specific password
- Wait for the notarization process to complete (usually takes a few minutes)

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