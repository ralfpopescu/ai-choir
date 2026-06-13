import sys
import os
import json
import shutil
import tempfile
from pathlib import Path
import appdirs

# Keep sklearn/joblib sequential: loky worker processes re-exec the frozen
# binary (ghost GUI instances) and inference gains nothing from them.
os.environ.setdefault("JOBLIB_MULTIPROCESSING", "0")

# Uniform height for every control in the settings form (sliders, the impulse
# text field and its Browse button) so the rows line up.
ROW_CONTROL_H = 28
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QScrollArea, QFormLayout, QDoubleSpinBox,
                             QSpinBox, QCheckBox, QMessageBox, QComboBox, QGroupBox,
                             QProgressBar, QSlider)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFontDatabase, QFont, QIcon

import model_manager

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

    def __init__(self, input_file, output_dir, impulse_file, config_file):
        super().__init__()
        # Resolve everything to absolute paths now: run() chdirs into a temp
        # dir, where a relative path like "./output" would silently alias the
        # temp dir's own output folder (self-copy error, render lost).
        self.input_file = os.path.abspath(input_file)
        self.output_dir = os.path.abspath(os.path.expanduser(output_dir))
        self.impulse_file = os.path.abspath(impulse_file) if impulse_file else impulse_file
        self.config_file = config_file
        self.temp_dir = None

    def run(self):
        original_cwd = os.getcwd()
        try:
            self.status_update.emit("Setting up environment...")
            self.progress.emit(1)

            # Create the output directory up front so a bad path fails here,
            # not after minutes of rendering.
            os.makedirs(self.output_dir, exist_ok=True)

            # Create a temporary directory for the generation process
            self.temp_dir = tempfile.mkdtemp(prefix="ai_choir_")

            # Copy necessary data to the temporary directory
            resource_base = get_resource_path("")

            # Copy the config file to the temporary directory
            shutil.copy2(self.config_file, os.path.join(self.temp_dir, 'config.json'))

            # Copy the so-vits-svc code (small), excluding the pretrain checkpoint
            sovits_src = os.path.join(resource_base, 'so-vits-svc')
            sovits_dst = os.path.join(self.temp_dir, 'so-vits-svc')
            shutil.copytree(sovits_src, sovits_dst, ignore=shutil.ignore_patterns('pretrain'))

            # Link the hubert checkpoint into the copied tree
            pretrain_dir = os.path.join(sovits_dst, 'so-vits-svc-4.1-Stable', 'pretrain')
            os.makedirs(pretrain_dir, exist_ok=True)
            os.symlink(str(model_manager.get_hubert_path()),
                       os.path.join(pretrain_dir, model_manager.HUBERT_FILENAME))

            # Link the downloaded voice models (multi-GB; never copy)
            os.symlink(str(model_manager.get_models_dir()),
                       os.path.join(self.temp_dir, 'models'))

            # Copy impulse.wav (default or user-specified)
            if self.impulse_file and os.path.exists(self.impulse_file):
                shutil.copy2(self.impulse_file, os.path.join(self.temp_dir, 'impulse.wav'))
            else:
                default_impulse = os.path.join(resource_base, 'impulse.wav')
                if os.path.exists(default_impulse):
                    shutil.copy2(default_impulse, os.path.join(self.temp_dir, 'impulse.wav'))

            # Create output directory in temp dir
            os.makedirs(os.path.join(self.temp_dir, 'output'), exist_ok=True)

            # Change to the temporary directory so relative paths in scripts work
            os.chdir(self.temp_dir)

            # Add temp dir to Python path so gen modules can be imported
            if resource_base not in sys.path:
                sys.path.insert(0, resource_base)

            self.progress.emit(5)

            # Track progress via callback
            models_count = self.get_model_count()
            voice_count = [0]  # mutable for closure

            def on_status(stage, message):
                if stage == "setup":
                    self.status_update.emit("Setting up...")
                    self.progress.emit(10)
                elif stage == "inference":
                    if "Processing voice model" in message:
                        voice_count[0] += 1
                        progress = min(65, 15 + int((voice_count[0] / max(1, models_count)) * 50))
                        self.status_update.emit(f"Rendering voice {voice_count[0]}/{models_count}...")
                        self.progress.emit(progress)
                elif stage == "process":
                    self.status_update.emit("Processing individual voices...")
                    self.progress.emit(70)
                elif stage == "curve":
                    self.status_update.emit("Applying EQ curves...")
                    self.progress.emit(80)
                elif stage == "combine":
                    self.status_update.emit("Combining voices into choir...")
                    self.progress.emit(85)
                elif stage == "convolve":
                    self.status_update.emit("Applying convolution reverb...")
                    self.progress.emit(92)
                elif stage == "done":
                    self.status_update.emit("Generation completed!")
                    self.progress.emit(98)

            # Run the generation pipeline directly (no subprocess)
            import gen
            gen.run_generation(self.input_file, status_callback=on_status)

            # Copy output files to the specified output directory
            output_dir_path = os.path.join(self.temp_dir, "output")
            if os.path.exists(output_dir_path):
                for filename in os.listdir(output_dir_path):
                    source_file = os.path.join(output_dir_path, filename)
                    destination_file = os.path.join(self.output_dir, filename)
                    if os.path.isfile(source_file):
                        shutil.copy2(source_file, destination_file)

            self.progress.emit(100)
            self.finished.emit(True, "Generation completed successfully!")

        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            self.finished.emit(False, f"Error during generation: {str(e)}\n{traceback_str}")
        finally:
            # Always restore the original working directory and cleanup temp dir
            os.chdir(original_cwd)
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)

    def get_model_count(self):
        """Get the number of models to be processed"""
        try:
            return max(1, len(model_manager.installed_models()))
        except Exception:
            return 7


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

        # Models ship inside the app; this only fails on a broken bundle or a
        # source checkout that hasn't run download_models.py yet.
        self.check_models()

    def check_models(self):
        missing = model_manager.missing_components()
        if not missing:
            return
        self.generate_button.setEnabled(False)
        self.status_label.setText("Voice models missing")
        QMessageBox.critical(
            self, "Error",
            "Missing components:\n- " + "\n- ".join(missing) +
            "\n\nThis app bundle appears to be incomplete. Please re-download "
            "the app. (If running from source, run download_models.py first.)"
        )

    def initUI(self):
        self.setWindowTitle("ai_choir")
        self.setMinimumSize(960, 548)
        self.resize(1000, 552)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(28, 20, 28, 22)
        main_layout.setSpacing(14)

        # Header
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        title_label = QLabel("ai_choir")
        title_label.setObjectName("titleLabel")
        subtitle_label = QLabel("by offwhite")
        subtitle_label.setObjectName("subtitleLabel")
        url_label = QLabel(
            '<a href="https://www.offwhite.studio" '
            'style="color: black; text-decoration: none;">www.offwhite.studio</a>'
        )
        url_label.setOpenExternalLinks(True)
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label, alignment=Qt.AlignmentFlag.AlignBottom)
        title_layout.addStretch()
        title_layout.addWidget(url_label, alignment=Qt.AlignmentFlag.AlignBottom)
        main_layout.addLayout(title_layout)
        
        # Input / output row
        io_row = QHBoxLayout()
        io_row.setSpacing(28)

        input_col = QVBoxLayout()
        input_col.setSpacing(6)
        input_header = QLabel("INPUT FILE")
        input_header.setObjectName("sectionLabel")
        input_field_row = QHBoxLayout()
        input_field_row.setSpacing(8)
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Select a WAV file")
        self.input_path.setReadOnly(True)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_input_file)
        input_field_row.addWidget(self.input_path)
        input_field_row.addWidget(browse_button)
        input_col.addWidget(input_header)
        input_col.addLayout(input_field_row)

        output_col = QVBoxLayout()
        output_col.setSpacing(6)
        output_header = QLabel("OUTPUT DIRECTORY")
        output_header.setObjectName("sectionLabel")
        output_field_row = QHBoxLayout()
        output_field_row.setSpacing(8)
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select an output directory")
        self.output_path.setText(os.path.join(os.path.expanduser("~"), "Music", "ai_choir"))
        output_browse_button = QPushButton("Browse")
        output_browse_button.clicked.connect(self.browse_output_dir)
        output_field_row.addWidget(self.output_path)
        output_field_row.addWidget(output_browse_button)
        output_col.addWidget(output_header)
        output_col.addLayout(output_field_row)

        io_row.addLayout(input_col, 1)
        io_row.addLayout(output_col, 1)
        main_layout.addLayout(io_row)
        main_layout.addStretch(1)
        
        # Settings: sound shaping (left) and voice gains (right)
        self.config = self.get_config()
        self.config_widgets = {}

        display_names = {
            "impulse_file": "Impulse File",
            "convolution_reverb_dry_wet": "Reverb Dry/Wet",
            "stereo_spread": "Stereo Spread",
            "base_detune": "Base Detune",
            "detune_drift": "Detune Drift",
            "detune_frequency": "Detune Frequency",
            "output_gain": "Output Gain",
            "voice_gain_female_1": "Female 1",
            "voice_gain_female_2": "Female 2",
            "voice_gain_female_3": "Female 3",
            "voice_gain_female_4": "Female 4",
            "voice_gain_male_1": "Male 1",
            "voice_gain_male_2": "Male 2",
            "voice_gain_male_3": "Male 3",
        }

        settings_row = QHBoxLayout()
        settings_row.setSpacing(36)

        left_column = QFormLayout()
        right_column = QFormLayout()
        for column in (left_column, right_column):
            column.setHorizontalSpacing(14)
            column.setVerticalSpacing(16)
            column.setLabelAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            # Controls fill the full width of their column instead of sitting
            # at their size hint (which read as awkwardly centered).
            column.setFieldGrowthPolicy(
                QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        sound_header = QLabel("SOUND")
        sound_header.setObjectName("sectionLabel")
        left_box = QVBoxLayout()
        left_box.setSpacing(10)
        left_box.addWidget(sound_header)
        left_box.addLayout(left_column)
        left_box.addStretch()

        voices_header = QLabel("VOICES")
        voices_header.setObjectName("sectionLabel")
        right_box = QVBoxLayout()
        right_box.setSpacing(10)
        right_box.addWidget(voices_header)
        right_box.addLayout(right_column)
        right_box.addStretch()

        # Define which fields go in which column
        left_column_fields = [
            "impulse_file", "convolution_reverb_dry_wet", "stereo_spread",
            "base_detune", "detune_drift", "detune_frequency", "output_gain"
        ]
        
        # Create form fields for each configuration item
        for key, value in self.config.items():
            if key == "cleanup":
                continue
            display_key = display_names.get(key, key.replace('_', ' ').title())
                
            if key == "impulse_file":
                impulse_layout = QHBoxLayout()
                impulse_layout.setSpacing(6)
                impulse_layout.setContentsMargins(0, 0, 0, 0)

                impulse_edit = QLineEdit()
                impulse_edit.setObjectName("rowEdit")
                impulse_edit.setFixedHeight(ROW_CONTROL_H)
                impulse_edit.setText("default" if not value else str(value))
                impulse_edit.setReadOnly(True)
                impulse_edit.setPlaceholderText("default")
                if not value:
                    impulse_edit.setStyleSheet("color: gray;")

                impulse_browse = QPushButton("Browse")
                impulse_browse.setObjectName("rowButton")
                impulse_browse.setFixedHeight(ROW_CONTROL_H)
                impulse_browse.clicked.connect(lambda: self.browse_impulse_file(impulse_edit))

                impulse_layout.addWidget(impulse_edit, 1)
                impulse_layout.addWidget(impulse_browse)
                impulse_layout.addWidget(self._make_help_button(key))

                impulse_widget = QWidget()
                impulse_widget.setLayout(impulse_layout)
                impulse_widget.setContentsMargins(0, 0, 0, 0)

                left_column.addRow(display_key, impulse_widget)
                self.config_widgets[key] = impulse_edit
                continue
                
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
            elif isinstance(value, (int, float)):
                slider_widget = self.create_slider_widget(key, value)
                self.config_widgets[key] = slider_widget
                if key in left_column_fields:
                    left_column.addRow(display_key, slider_widget["widget"])
                else:
                    right_column.addRow(display_key, slider_widget["widget"])
                continue
            else:
                widget = QLineEdit()
                widget.setText(str(value))

            input_layout = QHBoxLayout()
            input_layout.setSpacing(6)
            input_layout.setContentsMargins(0, 0, 0, 0)
            input_layout.addWidget(widget)
            input_layout.addWidget(self._make_help_button(key))

            input_widget = QWidget()
            input_widget.setLayout(input_layout)
            input_widget.setContentsMargins(0, 0, 0, 0)

            if key in left_column_fields:
                left_column.addRow(display_key, input_widget)
            else:
                right_column.addRow(display_key, input_widget)

            self.config_widgets[key] = widget
        
        settings_row.addLayout(left_box, 1)
        settings_row.addLayout(right_box, 1)
        main_layout.addLayout(settings_row)
        main_layout.addStretch(1)

        # Footer: reset | status + progress | generate
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_config)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setMinimumWidth(360)

        progress_col = QVBoxLayout()
        progress_col.setSpacing(5)
        progress_col.addWidget(self.status_label)
        progress_col.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.generate_button = QPushButton("Generate Choir")
        self.generate_button.setObjectName("generateButton")
        self.generate_button.setFixedHeight(46)
        self.generate_button.setMinimumWidth(220)
        self.generate_button.clicked.connect(self.generate_choir)

        footer = QHBoxLayout()
        footer.setSpacing(16)
        footer.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignBottom)
        footer.addStretch()
        footer.addLayout(progress_col)
        footer.addStretch()
        footer.addWidget(self.generate_button, alignment=Qt.AlignmentFlag.AlignBottom)
        main_layout.addLayout(footer)

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
            QWidget {{
                color: black;
            }}
            QMainWindow {{
                background-image: url({get_resource_path("bg.png")});
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            QLabel {{
                color: black;
                background-color: transparent;
            }}
            QLabel#titleLabel {{
                font-size: 26px;
                font-weight: bold;
            }}
            QLabel#subtitleLabel {{
                font-size: 14px;
                margin-bottom: 3px;
            }}
            QLabel#sectionLabel {{
                font-size: 12px;
                font-weight: bold;
                color: #545d3f;
            }}
            QPushButton {{
                background-image: url({get_resource_path("bg-button.png")});
                background-position: center;
                background-repeat: no-repeat;
                color: #f3f5e3;
                border: none;
                padding: 8px 18px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
            }}
            QPushButton#generateButton {{
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton#rowButton {{
                padding: 0px 14px;
            }}
            QPushButton#helpDot {{
                background-image: none;
                background-color: #545d3f;
                color: #f3f5e3;
                border: none;
                padding: 0px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton#helpDot:hover {{
                background-color: #6a7551;
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox {{
                background-color: rgba(255, 255, 255, 0.35);
                border: 1px solid #545d3f;
                padding: 8px;
                color: black;
            }}
            QLineEdit#rowEdit {{
                padding: 2px 8px;
            }}
            QSlider {{
                min-height: 22px;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid #545d3f;
                height: 18px;
                background: rgba(255, 255, 255, 0.3);
                margin: 0;
            }}
            QSlider::handle:horizontal {{
                background: #545d3f;
                border: none;
                width: 10px;
                margin: 0;
            }}
            QSlider::handle:horizontal:hover {{
                background: #6a7551;
            }}
            QSlider::sub-page:horizontal {{
                background: rgba(84, 93, 63, 0.4);
            }}
            QSlider::add-page:horizontal {{
                background: transparent;
            }}
            QProgressBar {{
                border: 1px solid #545d3f;
                background-color: rgba(255, 255, 255, 0.3);
            }}
            QProgressBar::chunk {{
                background-color: #545d3f;
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
            QToolTip {{
                color: black;
                background-color: white;
                border: 1px solid black;
                padding: 5px;
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
        
        # Reset and show progress UI
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting generation...")
        
        # Create and start the worker thread
        self.worker = GenerationWorker(input_file, output_dir, impulse_file, self.config_file)
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

    def _make_help_button(self, key):
        """Small round help marker; styled via #helpDot in apply_styles."""
        btn = QPushButton("?")
        btn.setObjectName("helpDot")
        btn.setFixedSize(18, 18)
        desc, value_range = self.config_info.get(key, ("No description available", ""))
        btn.setToolTip(f"{desc}\nRange: {value_range}" if value_range else desc)
        return btn

    def create_slider_widget(self, key, value):
        """Create a slider widget with percentage display for a given parameter"""
        # Get the range for this parameter
        min_val, max_val = self.get_parameter_range(key)
        
        # Store the range for later use
        self.slider_ranges[key] = (min_val, max_val)
        
        # Create the main widget to hold slider and label
        widget = QWidget()
        widget.setFixedHeight(ROW_CONTROL_H)
        layout = QHBoxLayout()
        layout.setSpacing(6)
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
        label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        help_button = self._make_help_button(key)

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
    # Multiprocessing children re-exec this binary when frozen; without this,
    # each spawn boots a second copy of the GUI instead of running its task.
    import multiprocessing
    multiprocessing.freeze_support()

    app = QApplication(sys.argv)

    # Headless build verification: AI_CHOIR_SELFTEST=<input.wav> runs one
    # generation synchronously and exits non-zero on failure.
    if os.environ.get('AI_CHOIR_SELFTEST'):
        results = {}
        worker = GenerationWorker(
            os.environ['AI_CHOIR_SELFTEST'],
            os.path.join(tempfile.gettempdir(), 'ai_choir_selftest_output'),
            "",
            get_resource_path('config.json'),
        )
        worker.finished.connect(lambda ok, msg: results.update(ok=ok, msg=msg))
        worker.run()
        print("SELFTEST result:", results.get('ok'), results.get('msg', ''))
        sys.exit(0 if results.get('ok') else 1)


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