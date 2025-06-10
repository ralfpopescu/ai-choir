import sys
import os
import json
import subprocess
import shutil
import re
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QScrollArea, QFormLayout, QDoubleSpinBox,
                             QSpinBox, QCheckBox, QMessageBox, QComboBox, QGroupBox,
                             QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFontDatabase, QFont

class GenerationWorker(QThread):
    finished = Signal(bool, str)
    progress = Signal(int)
    status_update = Signal(str)
    
    def __init__(self, input_file, output_dir):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
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
    def __init__(self):
        super().__init__()
        self.initUI()
        self.apply_styles()
        
    def initUI(self):
        self.setWindowTitle("AI Choir Generator")
        self.setMinimumSize(1000, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(5)  # Reduced from 10
        
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
        
        # Configuration descriptions and ranges
        config_info = {
            "cleanup": ("Whether to clean up interim files", "true/false"),
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
            "voice_gain_male_3": ("Gain for male voice 3", "-inf to inf")
        }
        
        # Define which fields go in which column
        left_column_fields = [
            "cleanup", "convolution_reverb_dry_wet", "stereo_spread",
            "base_detune", "detune_drift", "detune_frequency", "output_gain"
        ]
        
        # Create form fields for each configuration item
        for key, value in self.config.items():
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
            elif isinstance(value, int):
                widget = QSpinBox()
                widget.setRange(-100, 100)
                widget.setValue(value)
            elif isinstance(value, float):
                widget = QDoubleSpinBox()
                widget.setRange(-100, 100)
                widget.setSingleStep(0.001)
                widget.setDecimals(3)
                widget.setValue(value)
            else:
                widget = QLineEdit()
                widget.setText(str(value))
            
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
            if key in config_info:
                help_button.setToolTip(f"{config_info[key][0]}\nRange: {config_info[key][1]}")
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
        
        # Set the layout directly on the config group
        config_group.setLayout(columns_layout)
        
        # Add all sections to the main layout
        main_layout.addWidget(input_group)
        main_layout.addWidget(output_group)
        main_layout.addWidget(config_group)
        
        # Progress section
        progress_group = QGroupBox("Generation Progress")
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
        font_id = QFontDatabase.addApplicationFont("font.ttf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app = QApplication.instance()
            app.setFont(QFont(font_family))
        
        self.setStyleSheet("""
            QMainWindow {
                background-image: url(bg.png);
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }
            QGroupBox {
                background-color: transparent;
                border: none;
                margin-top: 1em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: black;
            }
            QPushButton {
                background-color: transparent;
                border: 1px solid black;
                border-radius: 5px;
                padding: 8px 16px;
                color: black;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background-color: transparent;
                border: 1px solid black;
                border-radius: 5px;
                padding: 5px;
                color: black;
            }
            QProgressBar {
                border: 1px solid black;
                border-radius: 5px;
                text-align: center;
                background-color: transparent;
                color: black;
            }
            QProgressBar::chunk {
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
            }
            QLabel {
                color: black;
                background-color: transparent;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QCheckBox {
                background-color: transparent;
                color: black;
            }
            QCheckBox::indicator {
                border: 1px solid black;
            }
            QWidget {
                color: black;
            }
            QToolTip {
                color: black;
                background-color: white;
                border: 1px solid black;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        
        # Set tooltip delay to 0 to show them immediately
        QApplication.instance().setStyleSheet("QToolTip { show-delay: 0ms; }")
        
    def get_config(self):
        try:
            with open('config.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            QMessageBox.warning(self, "Warning", "config.json not found. Using default configuration.")
            return {
                "cleanup": True,
                "convolution_reverb_dry_wet": 0.2,
                "stereo_spread": 1.5,
                "drift": 1.2,
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
                "voice_gain_male_3": 0.0
            }
        
    def save_config(self):
        for key, widget in self.config_widgets.items():
            if isinstance(widget, QCheckBox):
                self.config[key] = widget.isChecked()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                self.config[key] = widget.value()
            else:
                self.config[key] = widget.text()
        
        with open('config.json', 'w') as file:
            json.dump(self.config, file, indent=4)
    
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
    
    def generate_choir(self):
        input_file = self.input_path.text()
        output_dir = self.output_path.text()
        
        if not input_file:
            QMessageBox.warning(self, "Warning", "Please select an input WAV file.")
            return
        
        if not os.path.exists(input_file):
            QMessageBox.warning(self, "Warning", "The selected input file does not exist.")
            return
        
        # Save configuration
        self.save_config()
        
        # Reset and show progress UI
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting generation...")
        
        # Create and start the worker thread
        self.worker = GenerationWorker(input_file, output_dir)
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIChoirApp()
    window.show()
    sys.exit(app.exec()) 