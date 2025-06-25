import sys
import os
import json
import subprocess
import shutil
import re
from pathlib import Path
import appdirs
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QScrollArea, QFormLayout, QDoubleSpinBox,
                             QSpinBox, QCheckBox, QMessageBox, QComboBox, QGroupBox,
                             QProgressBar, QSlider)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFontDatabase, QFont, QIcon

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class GenerationWorker(QThread):
    finished = Signal(bool, str)
    progress = Signal(int)
    status_update = Signal(str)
    
    def __init__(self, input_file, output_dir, impulse_file):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.impulse_file = impulse_file
        self.process = None
        
    def run(self):
        try:
            # Get the number of models for progress calculation
            models = self.get_model_count()
            total_steps = models + 4  # models + processing + curve + combine + convolve
            current_step = 0
            voice_count = 0
            segment_count = 0
            
            self.status_update.emit("Setting up environment...")
            self.progress.emit(1)  # Start with a small progress indication
            
            # Create arrays to store the output for debugging
            stdout_data = []
            stderr_data = []
            
            # If an impulse file is specified, copy it to the working directory
            if self.impulse_file and os.path.exists(self.impulse_file):
                shutil.copy2(self.impulse_file, 'impulse.wav')
            
            # Run the generation script
            self.process = subprocess.Popen(
                [sys.executable, 'gen.py', self.input_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Polling approach to read from both stdout and stderr
            import select
            
            # Initial progress updates
            self.progress.emit(5)
            
            # Use polling to read from the process outputs
            while self.process.poll() is None:
                # Use select to wait until the process has output to read, but with a timeout
                # so we don't block forever
                ready_to_read, _, _ = select.select(
                    [self.process.stdout, self.process.stderr],
                    [], [], 0.1
                )
                
                for stream in ready_to_read:
                    line = stream.readline()
                    if not line:
                        continue
                        
                    # Store the output for debugging
                    if stream is self.process.stdout:
                        stdout_data.append(line)
                        print(f"STDOUT: {line.strip()}")
                        
                        # Parse the output for progress updates based on actual log patterns
                        if "File copied and renamed to:" in line:
                            self.status_update.emit("Preparing input file...")
                            self.progress.emit(10)
                            
                        # Model availability checks
                        elif "model available" in line:
                            model_name = line.split("/")[2] if "/" in line else "Model"
                            self.status_update.emit(f"Found model: {model_name}")
                            self.progress.emit(15)
                            
                        # Loading models
                        elif line.strip() == "load":
                            voice_count += 1
                            progress = min(60, 15 + int((voice_count / models) * 45))
                            self.status_update.emit(f"Rendering voice model {voice_count}/{models}...")
                            self.progress.emit(progress)
                            
                        # Processing voice segments
                        elif "vits use time" in line:
                            segment_count += 1
                            self.status_update.emit(f"Processing voice {voice_count}/{models}, segment {segment_count}...")
                            # Small increment for each segment
                            self.progress.emit(min(65, 15 + int((voice_count / models) * 50)))
                            
                        # Cleanup phase
                        elif "Cleaned up:" in line:
                            self.status_update.emit("Cleaning up temporary files...")
                            self.progress.emit(90)
                            
                        # Various processing steps
                        elif "gen_process.py" in line:
                            self.status_update.emit("Processing individual voices...")
                            self.progress.emit(75)
                        elif "gen_curve.py" in line:
                            self.status_update.emit("Applying EQ curves...")
                            self.progress.emit(80)
                        elif "gen_combine.py" in line:
                            self.status_update.emit("Combining voices into choir...")
                            self.progress.emit(85)
                        elif "gen_convolve.py" in line:
                            self.status_update.emit("Applying convolution reverb...")
                            self.progress.emit(95)
                            
                        # Completion
                        elif "Done! See result in output folder." in line:
                            self.status_update.emit("Generation completed!")
                            self.progress.emit(100)
                    else:
                        stderr_data.append(line)
                        print(f"STDERR: {line.strip()}")
            
            # Wait for process to complete and get return code
            return_code = self.process.wait()
            
            # Read any remaining output
            remaining_stdout = self.process.stdout.read()
            if remaining_stdout:
                stdout_data.append(remaining_stdout)
                print(f"Remaining STDOUT: {remaining_stdout}")
                
                # Check if the completion message is in the remaining output
                if "Done! See result in output folder." in remaining_stdout:
                    self.status_update.emit("Generation completed!")
                    self.progress.emit(100)
                
            remaining_stderr = self.process.stderr.read()
            if remaining_stderr:
                stderr_data.append(remaining_stderr)
                print(f"Remaining STDERR: {remaining_stderr}")
                
            # Check if the process was successful
            if return_code == 0:
                # If a custom output directory was specified, move the files there
                if self.output_dir != "./output":
                    os.makedirs(self.output_dir, exist_ok=True)
                    for filename in os.listdir("./output"):
                        source_file = os.path.join("./output", filename)
                        destination_file = os.path.join(self.output_dir, filename)
                        if os.path.isfile(source_file):
                            shutil.copy2(source_file, destination_file)
                
                self.progress.emit(100)
                self.finished.emit(True, "Generation completed successfully!")
            else:
                error_msg = f"Error during generation. Return code: {return_code}"
                if stderr_data:
                    error_details = "\n".join(stderr_data)
                    error_msg += f"\nDetails: {error_details}"
                self.finished.emit(False, error_msg)
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            self.finished.emit(False, f"Error during generation: {str(e)}\n{traceback_str}")
            
    def get_model_count(self):
        """Get the number of models to be processed"""
        try:
            # Try to load the model count from util.py's get_models function
            models_path = "./models"
            if os.path.exists(models_path):
                count = 0
                for folder_name in os.listdir(models_path):
                    folder_path = os.path.join(models_path, folder_name)
                    if os.path.isdir(folder_path) and os.path.isfile(os.path.join(folder_path, 'config.json')):
                        count += 1
                return max(1, count)  # Ensure at least 1 model
            return 7  # Default fallback if can't determine
        except Exception:
            return 7  # Default estimate


class AIChoirApp(QMainWindow):
    # Configuration descriptions and ranges
    config_info = {
        "impulse_file": ("Select an impulse response file for convolution reverb", ""),
        "convolution_reverb_dry_wet": ("Adds convolution reverb to the output. Switch out the impulse.wav file for whatever impulse response you want!", "0 - 1.0"),
        "stereo_spread": ("How panned the voices should be. 0 is mono, 4.0 will be hard left/right", "0 to 4.0"),
        "base_detune": ("How detuned the voices should be", "0 to 0.05"),
        "detune_drift": ("How much the voices should fluctuate around the base detuning", "0 to 25% of base_detune"),
        "detune_frequency": ("How long voices will linger on a detuned note", "0 to 5.0"),
        "output_gain": ("Apply gain to the output", "-inf to inf"),
        "voice_gain_female_1": ("Gain for female voice 1", "-inf to inf"),
        "voice_gain_female_2": ("Gain for female voice 2", "-inf to inf"),
        "voice_gain_female_3": ("Gain for female voice 3", "-inf to inf"),
        "voice_gain_female_4": ("Gain for female voice 4", "-inf to inf"),
        "voice_gain_male_1": ("Gain for male voice 1", "-inf to inf"),
        "voice_gain_male_2": ("Gain for male voice 2", "-inf to inf"),
        "voice_gain_male_3": ("Gain for male voice 3", "-inf to inf"),
        "cleanup": ("Whether to clean up temporary files after generation", "true/false")
    }

    def __init__(self):
        super().__init__()
        # Set up config directory
        self.config_dir = Path(appdirs.user_config_dir("ai-choir", appauthor=False))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        
        # Store slider ranges for each parameter
        self.slider_ranges = {}
        
        self.initUI()
        self.apply_styles()
        
        # Connect config change signals
        self.connect_config_signals()
        
    def initUI(self):
        self.setWindowTitle("ai_choir")
        self.setMinimumSize(1000, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(5)  # Reduced from 10
        
        # Title section
        title_layout = QHBoxLayout()
        title_label = QLabel("ai_choir")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: black;
            }
        """)
        subtitle_label = QLabel("by offwhite")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: black;
                margin-left: 10px;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)
        
        # Input file section
        input_group = QGroupBox("Input Audio File")
        input_layout = QHBoxLayout()
        
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Select a WAV file")
        self.input_path.setReadOnly(True)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_input_file)
        
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(browse_button)
        input_group.setLayout(input_layout)
        
        # Output directory section
        output_group = QGroupBox("Output Directory")
        output_layout = QHBoxLayout()
        
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select an output directory")
        self.output_path.setText("./output")
        
        output_browse_button = QPushButton("Browse")
        output_browse_button.clicked.connect(self.browse_output_dir)
        
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_browse_button)
        output_group.setLayout(output_layout)
        
        # Configuration section
        config_group = QGroupBox("Configuration")
        
        # Create two column layout directly in the group box
        columns_layout = QHBoxLayout()
        left_column = QFormLayout()
        right_column = QFormLayout()
        
        # Set spacing for both columns
        left_column.setSpacing(2)
        right_column.setSpacing(2)
        left_column.setVerticalSpacing(2)
        right_column.setVerticalSpacing(2)
        left_column.setLabelAlignment(Qt.AlignmentFlag.AlignVCenter)
        right_column.setLabelAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Load configuration
        self.config = self.get_config()
        self.config_widgets = {}
        
        # Define which fields go in which column
        left_column_fields = [
            "impulse_file", "convolution_reverb_dry_wet", "stereo_spread",
            "base_detune", "detune_drift", "detune_frequency", "output_gain"
        ]
        
        # Create form fields for each configuration item
        for key, value in self.config.items():
            # Skip cleanup setting
            if key == "cleanup":
                continue
                
            if key == "impulse_file":
                # Create a horizontal layout for the impulse file selector
                impulse_layout = QHBoxLayout()
                impulse_layout.setSpacing(2)
                impulse_layout.setContentsMargins(0, 0, 0, 0)
                
                # Create the line edit and browse button
                impulse_edit = QLineEdit()
                impulse_edit.setText("default" if not value else str(value))
                impulse_edit.setReadOnly(True)
                impulse_edit.setPlaceholderText("default")
                impulse_edit.setFixedWidth(100)
                if not value:
                    impulse_edit.setStyleSheet("color: gray;")
                
                impulse_browse = QPushButton("Browse")
                impulse_browse.setFixedWidth(80)
                impulse_browse.clicked.connect(lambda: self.browse_impulse_file(impulse_edit))
                
                # Add help button
                help_button = QPushButton("?")
                help_button.setFixedSize(20, 20)
                help_button.setToolTip("Select an impulse response file for convolution reverb")
                help_button.setStyleSheet("""
                    QPushButton {
                        border-radius: 10px;
                        font-weight: bold;
                        padding: 0px;
                        margin-left: 5px;
                        background-color: transparent;
                        border: 1px solid black;
                        color: black !important;
                    }
                """)
                
                impulse_layout.addWidget(impulse_edit)
                impulse_layout.addWidget(impulse_browse)
                impulse_layout.addWidget(help_button)
                
                # Create a widget to hold the layout
                impulse_widget = QWidget()
                impulse_widget.setLayout(impulse_layout)
                impulse_widget.setContentsMargins(0, 0, 0, 0)
                
                left_column.addRow("Impulse File", impulse_widget)
                self.config_widgets[key] = impulse_edit
                continue
                
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
            elif isinstance(value, (int, float)):
                # Create slider with percentage display
                slider_widget = self.create_slider_widget(key, value)
                self.config_widgets[key] = slider_widget
                
                # Add to appropriate column
                if key in left_column_fields:
                    left_column.addRow(key.replace('_', ' ').title(), slider_widget["widget"])
                else:
                    right_column.addRow(key.replace('_', ' ').title(), slider_widget["widget"])
                continue
            else:
                widget = QLineEdit()
                widget.setText(str(value))
                widget.setFixedWidth(100)  # Set fixed width for all line edits
            
            # Format key for display (replace underscores with spaces, capitalize)
            display_key = key.replace('_', ' ').title()
            
            # Create a horizontal layout for the input and help button
            input_layout = QHBoxLayout()
            input_layout.setSpacing(2)
            input_layout.setContentsMargins(0, 0, 0, 0)
            
            # Add the input widget first
            input_layout.addWidget(widget)
            
            # Always add help button for all fields
            help_button = QPushButton("?")
            help_button.setFixedSize(20, 20)
            if key in self.config_info:
                help_button.setToolTip(f"{self.config_info[key][0]}\nRange: {self.config_info[key][1]}")
            else:
                help_button.setToolTip("No description available")
            help_button.setStyleSheet("""
                QPushButton {
                    border-radius: 10px;
                    font-weight: bold;
                    padding: 0px;
                    margin-left: 5px;
                    background-color: transparent;
                    border: 1px solid black;
                    color: black !important;
                }
            """)
            input_layout.addWidget(help_button)
            
            # Create a widget to hold the input layout
            input_widget = QWidget()
            input_widget.setLayout(input_layout)
            input_widget.setContentsMargins(0, 0, 0, 0)
            
            # Add to appropriate column
            if key in left_column_fields:
                left_column.addRow(display_key, input_widget)
            else:
                right_column.addRow(display_key, input_widget)
            
            self.config_widgets[key] = widget
        
        # Add columns to the main layout
        columns_layout.addLayout(left_column)
        columns_layout.addLayout(right_column)
        
        # Add reset button at the bottom of config group
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_config)
        reset_button.setStyleSheet("""
            QPushButton {
                margin-top: 10px;
                background-color: #f0f0f0;
                border: 1px solid #999;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Create a horizontal layout for the reset button to center it
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        reset_layout.addWidget(reset_button)
        reset_layout.addStretch()
        
        # Add the reset layout to the columns layout
        columns_layout.addLayout(reset_layout)
        
        # Set the layout directly on the config group
        config_group.setLayout(columns_layout)
        
        # Add all sections to the main layout
        main_layout.addWidget(input_group)
        main_layout.addWidget(output_group)
        main_layout.addWidget(config_group)
        
        # Progress section
        progress_group = QGroupBox()  # Removed the title
        progress_layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)
        
        # Generate button
        generate_button = QPushButton("Generate Choir")
        generate_button.setMinimumHeight(40)
        generate_button.clicked.connect(self.generate_choir)
        
        main_layout.addWidget(progress_group)
        main_layout.addWidget(generate_button)
        
        self.setCentralWidget(main_widget)
        
    def apply_styles(self):
        # Load and register the custom font
        try:
            font_path = get_resource_path("font.ttf")
            print(f"Attempting to load font from: {font_path}")
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                print(f"Successfully loaded font family: {font_family}")
                
                # Create a font object with specific properties
                custom_font = QFont(font_family)
                custom_font.setPointSize(10)  # Set a reasonable default size
                
                # Apply font to the application
                app = QApplication.instance()
                app.setFont(custom_font)
                
                # Apply font to all widgets in the window
                def apply_font_to_widget(widget):
                    widget.setFont(custom_font)
                    for child in widget.findChildren(QWidget):
                        child.setFont(custom_font)
                
                # Apply font to all widgets after the window is shown
                QTimer.singleShot(0, lambda: apply_font_to_widget(self))
            else:
                print("Failed to load font.ttf - font_id is -1")
        except Exception as e:
            print(f"Error loading font: {str(e)}")
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-image: url({get_resource_path("bg.png")});
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            QGroupBox {{
                background-color: transparent;
                border: none;
                margin-top: 1em;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: black;
            }}
            QPushButton {{
                background-image: url({get_resource_path("bg-button.png")});
                background-position: center;
                background-repeat: no-repeat;
                color: white !important;
                border: none;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox {{
                background-color: transparent;
                border: 1px solid black;
                border-radius: 5px;
                padding: 5px;
                color: black;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid black;
                height: 8px;
                background: transparent;
                border-radius: 4px;
                margin: 2px 0;
            }}
            QSlider::handle:horizontal {{
                background: black;
                border: 1px solid black;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: #333;
            }}
            QSlider::sub-page:horizontal {{
                background: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
            }}
            QSlider::add-page:horizontal {{
                background: transparent;
                border-radius: 4px;
            }}
            QProgressBar {{
                border: 1px solid black;
                border-radius: 5px;
                text-align: center;
                background-color: transparent;
                color: black;
            }}
            QProgressBar::chunk {{
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
            }}
            QLabel {{
                color: black;
                background-color: transparent;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QCheckBox {{
                background-color: transparent;
                color: black;
            }}
            QCheckBox::indicator {{
                border: 1px solid black;
            }}
            QWidget {{
                color: black;
            }}
            QToolTip {{
                color: black;
                background-color: white;
                border: 1px solid black;
                padding: 5px;
                border-radius: 3px;
            }}
        """)
        
        # Set tooltip delay to 0 to show them immediately
        QApplication.instance().setStyleSheet("QToolTip { show-delay: 0ms; }")
        
    def connect_config_signals(self):
        """Connect signals for all config widgets to save on change"""
        for key, widget in self.config_widgets.items():
            if isinstance(widget, dict) and "slider" in widget:
                # For slider widgets
                widget["slider"].valueChanged.connect(self.save_config)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.valueChanged.connect(self.save_config)
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.save_config)
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(self.save_config)

    def get_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as file:
                    return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            QMessageBox.warning(self, "Warning", f"Could not load configuration: {str(e)}\nUsing default configuration.")
        
        # Default configuration
        return {
            "impulse_file": "",
            "convolution_reverb_dry_wet": 0.2,
            "stereo_spread": 1.5,
            "base_detune": 0.014,
            "detune_drift": 0.002,
            "detune_frequency": 0.3,
            "output_gain": -10,
            "voice_gain_female_1": 0.0,
            "voice_gain_female_2": 0.0,
            "voice_gain_female_3": 0.0,
            "voice_gain_female_4": 0.0,
            "voice_gain_male_1": 0.0,
            "voice_gain_male_2": 0.0,
            "voice_gain_male_3": 0.0,
            "cleanup": True
        }
        
    def parse_range(self, range_str):
        """Parse a range string into min and max values."""
        if range_str == "true/false":
            return None, None
        if range_str == "-inf to inf":
            return float('-inf'), float('inf')
        
        # Handle percentage case
        if "%" in range_str:
            return None, None  # Will be handled specially
        
        # Handle standard range formats
        range_str = range_str.replace(" ", "")
        if "to" in range_str:
            min_val, max_val = range_str.split("to")
        elif "-" in range_str:
            min_val, max_val = range_str.split("-")
        else:
            return None, None
            
        try:
            return float(min_val), float(max_val)
        except ValueError:
            return None, None

    def save_config(self):
        try:
            for key, widget in self.config_widgets.items():
                if isinstance(widget, dict) and "slider" in widget:
                    # For slider widgets, convert percentage to actual value
                    percentage = widget["slider"].value()
                    self.config[key] = self.slider_to_value(key, percentage)
                elif isinstance(widget, QLineEdit):
                    # For impulse file, save empty string if it's set to "default"
                    if key == "impulse_file" and widget.text() == "default":
                        self.config[key] = ""
                    else:
                        self.config[key] = widget.text()
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    value = widget.value()
                    min_val, max_val = self.parse_range(self.config_info[key][1])
                    
                    # Handle percentage case for detune_drift
                    if key == "detune_drift" and "%" in self.config_info[key][1]:
                        base_detune = self.config["base_detune"]
                        max_val = base_detune * 0.25  # 25% of base_detune
                        min_val = 0
                    
                    if min_val is not None and max_val is not None:
                        value = max(min_val, min(value, max_val))
                    
                    self.config[key] = value
            
            # Save to user config directory
            with open(self.config_file, 'w') as file:
                json.dump(self.config, file, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not save configuration: {str(e)}")
    
    def browse_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select WAV File", "", "WAV Files (*.wav)"
        )
        if file_path:
            self.input_path.setText(file_path)
    
    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory"
        )
        if dir_path:
            self.output_path.setText(dir_path)
    
    def browse_impulse_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Impulse Response File", "", "WAV Files (*.wav)"
        )
        if file_path:
            line_edit.setText(file_path)
            line_edit.setStyleSheet("color: black;")
        else:
            line_edit.setText("default")
            line_edit.setStyleSheet("color: gray;")
    
    def generate_choir(self):
        input_file = self.input_path.text()
        output_dir = self.output_path.text()
        
        if not input_file:
            QMessageBox.warning(self, "Warning", "Please select an input WAV file.")
            return
        
        if not os.path.exists(input_file):
            QMessageBox.warning(self, "Warning", "The selected input file does not exist.")
            return
            
        # Get impulse file path, use default if none selected
        impulse_file = self.config_widgets["impulse_file"].text()
        if impulse_file == "default":
            impulse_file = ""
        elif not os.path.exists(impulse_file):
            QMessageBox.warning(self, "Warning", "The selected impulse file does not exist.")
            return
        
        # Save configuration
        self.save_config()
        
        # Copy config file to current working directory
        try:
            shutil.copy2(self.config_file, 'config.json')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy configuration file: {str(e)}")
            return
        
        # Reset and show progress UI
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting generation...")
        
        # Create and start the worker thread
        self.worker = GenerationWorker(input_file, output_dir, impulse_file)
        self.worker.progress.connect(self.update_progress)
        self.worker.status_update.connect(self.update_status)
        self.worker.finished.connect(self.generation_finished)
        self.worker.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        self.status_label.setText(message)
    
    def generation_finished(self, success, message):
        if success:
            self.status_label.setText("Generation complete!")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText("Generation failed")
            QMessageBox.critical(self, "Error", message)

    def reset_config(self):
        """Reset all configuration values to their defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Configuration",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Get default configuration
            default_config = {
                "impulse_file": "",
                "convolution_reverb_dry_wet": 0.2,
                "stereo_spread": 1.5,
                "base_detune": 0.014,
                "detune_drift": 0.002,
                "detune_frequency": 0.3,
                "output_gain": -10,
                "voice_gain_female_1": 0.0,
                "voice_gain_female_2": 0.0,
                "voice_gain_female_3": 0.0,
                "voice_gain_female_4": 0.0,
                "voice_gain_male_1": 0.0,
                "voice_gain_male_2": 0.0,
                "voice_gain_male_3": 0.0,
                "cleanup": True
            }
            
            # Update all widgets with default values
            for key, value in default_config.items():
                widget = self.config_widgets.get(key)
                if widget is not None:
                    if isinstance(widget, dict) and "slider" in widget:
                        # For slider widgets, convert value to percentage
                        percentage = self.value_to_slider(key, value)
                        widget["slider"].setValue(percentage)
                        widget["label"].setText(f"{percentage}%")
                    elif isinstance(widget, QLineEdit):
                        if key == "impulse_file":
                            widget.setText("default")
                            widget.setStyleSheet("color: gray;")
                        else:
                            widget.setText(str(value))
                    elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                        widget.setValue(float(value))
                    elif isinstance(widget, QCheckBox):
                        widget.setChecked(bool(value))
            
            # Update the config dictionary
            self.config = default_config.copy()
            
            # Save the reset configuration
            self.save_config()
            
            QMessageBox.information(
                self,
                "Configuration Reset",
                "All settings have been reset to their default values."
            )

    def create_slider_widget(self, key, value):
        """Create a slider widget with percentage display for a given parameter"""
        # Get the range for this parameter
        min_val, max_val = self.get_parameter_range(key)
        
        # Store the range for later use
        self.slider_ranges[key] = (min_val, max_val)
        
        # Create the main widget to hold slider and label
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create slider
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)  # Always 0-100 for percentage
        
        # Convert the actual value to percentage
        if max_val != min_val:
            percentage = int(((value - min_val) / (max_val - min_val)) * 100)
            percentage = max(0, min(100, percentage))  # Clamp to 0-100
        else:
            percentage = 50  # Default to middle if no range
        
        slider.setValue(percentage)
        
        # Create percentage label
        label = QLabel(f"{percentage}%")
        label.setFixedWidth(40)
        label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Add help button
        help_button = QPushButton("?")
        help_button.setFixedSize(20, 20)
        if key in self.config_info:
            help_button.setToolTip(f"{self.config_info[key][0]}\nRange: {self.config_info[key][1]}")
        else:
            help_button.setToolTip("No description available")
        help_button.setStyleSheet("""
            QPushButton {
                border-radius: 10px;
                font-weight: bold;
                padding: 0px;
                margin-left: 5px;
                background-color: transparent;
                border: 1px solid black;
                color: black !important;
            }
        """)
        
        # Connect slider value change to update label and save config
        def on_slider_changed():
            percentage = slider.value()
            label.setText(f"{percentage}%")
            self.save_config()
        
        slider.valueChanged.connect(on_slider_changed)
        
        # Add widgets to layout
        layout.addWidget(slider)
        layout.addWidget(label)
        layout.addWidget(help_button)
        
        widget.setLayout(layout)
        
        # Store both slider and label for later access
        return {"slider": slider, "label": label, "widget": widget}

    def get_parameter_range(self, key):
        """Get the min and max values for a parameter"""
        if key not in self.config_info:
            return 0.0, 1.0  # Default range
        
        range_str = self.config_info[key][1]
        
        # Handle special cases
        if range_str == "true/false":
            return 0.0, 1.0
        if range_str == "-inf to inf":
            return -50.0, 50.0  # Reasonable range for gain values
        
        # Handle percentage case for detune_drift
        if "%" in range_str:
            base_detune = self.config.get("base_detune", 0.014)
            return 0.0, base_detune * 0.25  # 25% of base_detune
        
        # Parse standard range formats
        range_str = range_str.replace(" ", "")
        if "to" in range_str:
            min_val, max_val = range_str.split("to")
        elif "-" in range_str:
            min_val, max_val = range_str.split("-")
        else:
            return 0.0, 1.0  # Default range
            
        try:
            return float(min_val), float(max_val)
        except ValueError:
            return 0.0, 1.0  # Default range

    def slider_to_value(self, key, percentage):
        """Convert slider percentage to actual parameter value"""
        if key not in self.slider_ranges:
            return 0.0
        
        min_val, max_val = self.slider_ranges[key]
        return min_val + (percentage / 100.0) * (max_val - min_val)

    def value_to_slider(self, key, value):
        """Convert actual parameter value to slider percentage"""
        if key not in self.slider_ranges:
            return 50
        
        min_val, max_val = self.slider_ranges[key]
        if max_val != min_val:
            percentage = ((value - min_val) / (max_val - min_val)) * 100
            return max(0, min(100, int(percentage)))
        return 50


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application icon based on platform
    if sys.platform.startswith('darwin'):  # macOS
        icon_paths = ["icon.icns", "icon.png"]
    elif sys.platform.startswith('win'):  # Windows
        icon_paths = ["icon.ico", "icon.png"]
    else:  # Linux and others
        icon_paths = ["icon.png"]
    
    # Try each icon path
    icon_path = None
    for icon_name in icon_paths:
        full_path = get_resource_path(icon_name)
        if os.path.exists(full_path):
            icon_path = full_path
            break
    
    if icon_path:
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    
    window = AIChoirApp()
    window.show()
    sys.exit(app.exec()) 