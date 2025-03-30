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