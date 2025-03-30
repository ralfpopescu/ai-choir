import sys
import os
import json
import subprocess
import shutil
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QScrollArea, QFormLayout, QDoubleSpinBox,
                             QSpinBox, QCheckBox, QMessageBox, QComboBox, QGroupBox,
                             QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal

class GenerationWorker(QThread):
    finished = Signal(bool, str)
    progress = Signal(int)
    
    def __init__(self, input_file, output_dir):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        
    def run(self):
        try:
            # Run the generation script
            process = subprocess.Popen(
                [sys.executable, 'gen.py', self.input_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Simulate progress (since we can't easily get progress from the script)
            for i in range(10):
                self.progress.emit(i * 10)
                process.stdout.readline()  # Read some output to avoid blocking
            
            process.wait()
            
            # Check if the process was successful
            if process.returncode == 0:
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
                self.finished.emit(False, f"Error during generation. Return code: {process.returncode}")
        except Exception as e:
            self.finished.emit(False, f"Error during generation: {str(e)}")


class AIChoirApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("AI Choir Generator")
        self.setMinimumSize(700, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
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
        
        # Create a scroll area for configuration
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        config_layout = QFormLayout(scroll_content)
        
        # Load configuration
        self.config = self.get_config()
        self.config_widgets = {}
        
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
                widget.setSingleStep(0.1)
                widget.setValue(value)
            else:
                widget = QLineEdit()
                widget.setText(str(value))
            
            # Format key for display (replace underscores with spaces, capitalize)
            display_key = key.replace('_', ' ').title()
            config_layout.addRow(display_key, widget)
            self.config_widgets[key] = widget
        
        scroll.setWidget(scroll_content)
        config_group.setLayout(QVBoxLayout())
        config_group.layout().addWidget(scroll)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Generate button
        generate_button = QPushButton("Generate Choir")
        generate_button.setMinimumHeight(40)
        generate_button.clicked.connect(self.generate_choir)
        
        # Add all sections to the main layout
        main_layout.addWidget(input_group)
        main_layout.addWidget(output_group)
        main_layout.addWidget(config_group)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(generate_button)
        
        self.setCentralWidget(main_widget)
        
    def get_config(self):
        try:
            with open('config.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            QMessageBox.warning(self, "Warning", "config.json not found. Using default configuration.")
            return {
                "cleanup": False,
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
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create and start the worker thread
        self.worker = GenerationWorker(input_file, output_dir)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.generation_finished)
        self.worker.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def generation_finished(self, success, message):
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIChoirApp()
    window.show()
    sys.exit(app.exec()) 