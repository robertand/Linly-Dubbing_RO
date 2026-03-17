import os
import threading
import datetime
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QScrollArea, QPushButton, QMessageBox, QSplitter,
                               QProgressBar, QTextEdit, QFileDialog)
from PySide6.QtCore import QTimer, Signal, QObject, Qt
import subprocess

from ui_components import VideoPlayer

# Try to import actual function modules
try:
    from tools.do_everything import do_everything
    from tools.utils import SUPPORT_VOICE
except ImportError:
    # Define temporary support voice list
    SUPPORT_VOICE = ['zh-CN-XiaoxiaoNeural', 'en-US-JennyNeural',
                     'ja-JP-NanamiNeural', 'ro-RO-AlinaNeural']


# Create a signal class for thread communication
class WorkerSignals(QObject):
    finished = Signal(str, str)  # Finish signal: status, video path
    progress = Signal(int, str)  # Progress signal: percentage, status message
    log = Signal(str)  # Log signal: log text


class FullAutoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # For storing current configuration
        self.config = self.load_config()

        # Create main horizontal layout, left for URL input, right for processing buttons and video player
        self.main_layout = QHBoxLayout(self)

        # Left configuration area - local video selection
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)

        # Video path selection
        self.video_path_label = QLabel("Video File")
        self.video_path_input = QLineEdit()
        self.video_path_input.setPlaceholderText("Select a local video file for processing")
        self.video_path_input.setReadOnly(True)

        # Select local video button
        self.select_video_button = QPushButton("Select Video")
        self.select_video_button.clicked.connect(self.select_local_video)
        self.select_video_button.setMinimumHeight(40)

        self.left_layout.addWidget(self.video_path_label)
        self.left_layout.addWidget(self.video_path_input)
        self.left_layout.addWidget(self.select_video_button)

        # Add a configuration summary
        self.config_summary = QTextEdit()
        self.config_summary.setReadOnly(True)
        self.config_summary.setMaximumHeight(200)
        self.update_config_summary()

        self.config_summary_label = QLabel("Current Configuration Summary:")
        self.left_layout.addWidget(self.config_summary_label)
        self.left_layout.addWidget(self.config_summary)

        # Right control and display area
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)

        # Execution button area
        self.button_layout = QHBoxLayout()

        # Execution button
        self.run_button = QPushButton("One-Click Process")
        self.run_button.clicked.connect(self.run_process)
        self.run_button.setMinimumHeight(50)
        self.run_button.setStyleSheet("background-color: #4CAF50; color: white;")

        # Stop button
        self.stop_button = QPushButton("Stop Processing")
        self.stop_button.clicked.connect(self.stop_process)
        self.stop_button.setMinimumHeight(50)
        self.stop_button.setEnabled(False)  # Initially disabled

        # Preview button
        self.preview_button = QPushButton("Preview Video")
        self.preview_button.clicked.connect(self.preview_video)
        self.preview_button.setMinimumHeight(50)
        self.preview_button.setEnabled(False)  # Initially disabled

        # Open file folder button
        self.open_folder_button = QPushButton("Open Directory")
        self.open_folder_button.clicked.connect(self.open_folder)
        self.open_folder_button.setMinimumHeight(50)
        self.open_folder_button.setEnabled(False)  # Initially disabled

        # Add buttons to button layout
        self.button_layout.addWidget(self.run_button)
        self.button_layout.addWidget(self.stop_button)
        self.button_layout.addWidget(self.open_folder_button)
        self.button_layout.addWidget(self.preview_button)
        self.right_layout.addLayout(self.button_layout)

        # Progress bar
        self.progress_layout = QVBoxLayout()
        self.progress_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_layout.addWidget(QLabel("Processing Progress:"))
        self.progress_layout.addWidget(self.progress_bar)
        self.progress_layout.addWidget(self.progress_label)
        self.right_layout.addLayout(self.progress_layout)

        # Status display
        self.status_label = QLabel("Ready")
        self.right_layout.addWidget(QLabel("Processing Status:"))
        self.right_layout.addWidget(self.status_label)

        # Create a vertical splitter on the right, video player on top, log at bottom
        self.right_splitter = QSplitter(Qt.Vertical)

        # Video player container
        self.video_container = QWidget()
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.addWidget(QLabel("Synthesis Video Preview:"))
        self.video_player = VideoPlayer("Synthesis Video")
        self.video_layout.addWidget(self.video_player)
        self.video_container.setLayout(self.video_layout)

        # Log container
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.addWidget(QLabel("Processing Log:"))

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)  # Set to read-only
        self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)  # Auto wrap
        self.log_layout.addWidget(self.log_text)

        # Log control buttons
        self.log_button_layout = QHBoxLayout()
        self.clear_log_button = QPushButton("Clear Log")
        self.clear_log_button.clicked.connect(self.clear_log)
        self.save_log_button = QPushButton("Save Log")
        self.save_log_button.clicked.connect(self.save_log)
        self.log_button_layout.addWidget(self.clear_log_button)
        self.log_button_layout.addWidget(self.save_log_button)
        self.log_layout.addLayout(self.log_button_layout)

        self.log_container.setLayout(self.log_layout)

        # Add video and log areas to right splitter
        self.right_splitter.addWidget(self.video_container)
        self.right_splitter.addWidget(self.log_container)

        # Set initial split ratio (60% video, 40% log)
        self.right_splitter.setSizes([600, 400])

        # Add splitter to right layout
        self.right_layout.addWidget(self.right_splitter)

        # Add left and right areas to main layout
        # Use QSplitter to allow users to adjust left/right width
        self.main_splitter = QSplitter()
        self.main_splitter.addWidget(self.left_widget)
        self.main_splitter.addWidget(self.right_widget)

        # Set initial split ratio (30% left, 70% right)
        self.main_splitter.setSizes([300, 700])

        self.main_layout.addWidget(self.main_splitter)
        self.setLayout(self.main_layout)

        # Worker thread
        self.worker_thread = None
        self.is_processing = False
        self.signals = WorkerSignals()
        self.signals.finished.connect(self.process_finished)
        self.signals.progress.connect(self.update_progress)
        self.signals.log.connect(self.append_log)

        # Store generated video path
        self.generated_video_path = None

        # Actual progress updates
        self.current_progress = 0
        self.progress_steps = [
            "Downloading Video...", "Vocal Separation...", "AI Speech Recognition...",
            "Subtitle Translation...", "AI Speech Synthesis...", "Video Synthesis..."
        ]
        self.current_step = 0

        # Initialize log
        self.append_log("System initialization complete, ready")

    def update_config_summary(self):
        """Update configuration summary display"""
        config = self.load_config()
        if config:
            summary_text = "● Video Output Directory: {}\n".format(config.get("video_folder", "videos"))
            summary_text += "● Resolution: {}\n".format(config.get("resolution", "1080p"))
            summary_text += "● Vocal Separation: {}, Device: {}\n".format(
                config.get("model", "htdemucs_ft"),
                config.get("device", "auto")
            )
            summary_text += "● Speech Recognition: {}, Model: {}\n".format(
                config.get("asr_model", "WhisperX"),
                config.get("whisperx_size", "large")
            )
            summary_text += "● Translation Method: {}\n".format(config.get("translation_method", "LLM"))
            summary_text += "● TTS Method: {}, Language: {}\n".format(
                config.get("tts_method", "EdgeTTS"),
                config.get("target_language_tts", "Chinese")
            )
            summary_text += "● Add Subtitles: {}, Speed Factor: {}\n".format(
                "Yes" if config.get("add_subtitles", True) else "No",
                config.get("speed_factor", 1.00)
            )
            self.config_summary.setText(summary_text)
        else:
            self.config_summary.setText("No configuration info found, using defaults")

    def select_local_video(self):
        """Select local video file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mkv *.mov *.flv)"
        )
        if file_path:
            self.video_path_input.setText(file_path)
            self.append_log(f"Selected local video file: {file_path}")

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(config_dir, "config.json")

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config
            else:
                return None
        except Exception as e:
            self.append_log(f"Failed to load config: {str(e)}")
            return None

    def update_config(self, new_config):
        """Update current configuration"""
        self.config = new_config
        self.update_config_summary()

    def update_progress(self, progress, status):
        """Update processing progress"""
        # Ensure progress bar matches status info
        self.current_progress = progress
        self.progress_bar.setValue(progress)
        self.progress_label.setText(status)
        self.append_log(f"Progress Update: {progress}% - {status}")

    def process_thread(self):
        """Asynchronous processing thread"""
        config = self.load_config() or {}
        try:
            self.signals.log.emit("Starting process...")
            self.signals.progress.emit(0, "Initializing process...")
            local_video_path = self.video_path_input.text()

            if not local_video_path or not os.path.exists(local_video_path):
                self.signals.log.emit("Error: No valid local video file selected.")
                self.signals.finished.emit("Failed: No video selected", "")
                return

            # Log important parameters
            self.signals.log.emit(f"Video folder: {config.get('video_folder', 'videos')}")
            self.signals.log.emit(f"Input Video: {local_video_path}")
            self.signals.log.emit(f"Resolution: {config.get('resolution', '1080p')}")

            # More detailed parameter logging
            self.signals.log.emit("-" * 50)
            self.signals.log.emit("Processing Parameters:")
            self.signals.log.emit(f"Resolution: {config.get('resolution', '1080p')}")
            self.signals.log.emit(f"Vocal Separation Model: {config.get('model', 'htdemucs_ft')}")
            self.signals.log.emit(f"Compute Device: {config.get('device', 'auto')}")
            self.signals.log.emit(f"Number of Shifts: {config.get('shifts', 5)}")
            self.signals.log.emit(f"ASR Method: {config.get('asr_method', 'WhisperX')}")
            self.signals.log.emit(f"WhisperX Model Size: {config.get('whisperx_size', 'large')}")
            self.signals.log.emit(f"Translation Method: {config.get('translation_method', 'LLM')}")
            self.signals.log.emit(f"TTS Method: {config.get('tts_method', 'EdgeTTS')}")
            self.signals.log.emit("-" * 50)

            # Update progress info - Step 1: Preparing Video
            self.signals.progress.emit(5, "Preparing Video (5%)")

            # Actual processing call
            result, video_path = do_everything(
                root_folder=config.get('video_folder', 'videos'),
                video_path=local_video_path,
                demucs_model=config.get('model', 'htdemucs_ft'),
                device=config.get('device', 'auto'),
                shifts=config.get('shifts', 5),
                asr_method=config.get('asr_method', 'WhisperX'),
                whisper_model=config.get('whisperx_size', 'large'),
                batch_size=config.get('batch_size', 32),
                diarization=config.get('separate_speakers', True),
                whisper_min_speakers=config.get('min_speakers', None),
                whisper_max_speakers=config.get('max_speakers', None),
                translation_method=config.get('translation_method', 'LLM'),
                translation_target_language=config.get('target_language_translation', 'Romanian'),
                tts_method=config.get('tts_method', 'EdgeTTS'),
                tts_target_language=config.get('target_language_tts', 'Romanian'),
                voice=config.get('edge_tts_voice', 'ro-RO-AlinaNeural'),
                subtitles=config.get('add_subtitles', True),
                speed_up=config.get('speed_factor', 1.00),
                fps=config.get('frame_rate', 30),
                background_music=config.get('background_music', None),
                bgm_volume=config.get('bg_music_volume', 0.5),
                video_volume=config.get('video_volume', 1.0),
                target_resolution=config.get('output_resolution', '1080p'),
                max_retries=config.get('max_retries', 3)
            )

            # Finish processing, set 100% progress
            self.signals.progress.emit(100, "Processing Complete!")
            self.signals.log.emit(f"Process Complete: {result}")
            if video_path:
                self.signals.log.emit(f"Generated video path: {video_path}")

            # Process finished, send signal
            self.signals.finished.emit(result, video_path if video_path else "")

        except Exception as e:
            # Capture and log full stack trace
            import traceback
            stack_trace = traceback.format_exc()
            error_msg = f"Processing Failed: {str(e)}\n\nStack Trace:\n{stack_trace}"
            self.signals.log.emit(error_msg)
            self.signals.progress.emit(0, "Processing Failed")
            self.signals.finished.emit(f"Processing Failed: {str(e)}", "")

    def run_process(self):
        """Start processing"""
        if self.is_processing:
            return

        if not self.video_path_input.text():
            QMessageBox.warning(self, "Warning", "Please select a video file first!")
            return

        self.is_processing = True
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.preview_button.setEnabled(False)
        self.open_folder_button.setEnabled(False)
        self.status_label.setText("Processing...")

        # Reset progress
        self.current_progress = 0
        self.current_step = 0
        self.progress_bar.setValue(0)
        self.progress_label.setText("Preparing to process...")

        # Log start processing
        self.append_log("-" * 50)
        self.append_log(f"Starting Process - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.append_log(f"Video Path: {self.video_path_input.text()}")

        # Create and start processing thread
        self.worker_thread = threading.Thread(target=self.process_thread)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def stop_process(self):
        """Stop processing"""
        if not self.is_processing:
            return

        # In actual application, add logic to stop processing
        # TODO: Add code to interrupt processing thread

        self.is_processing = False
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Processing Stopped")
        self.append_log("User manually stopped processing")

    def process_finished(self, result, video_path):
        """Process finished callback"""
        self.is_processing = False
        self.run_button.setEnabled(True)  # Re-enable one-click process button
        self.stop_button.setEnabled(False)  # Disable stop process button
        self.status_label.setText(result)

        # Store generated video path
        self.generated_video_path = video_path

        # Log process complete
        self.append_log(f"Process Complete - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.append_log(f"Result: {result}")

        # If video path exists, enable preview and open folder buttons, and load video
        if video_path and os.path.exists(video_path):
            self.preview_button.setEnabled(True)
            self.open_folder_button.setEnabled(True)
            self.video_player.set_video(video_path)
            self.append_log(f"Generated video path: {video_path}")
        else:
            self.append_log("No video generated or invalid video path")

    def preview_video(self):
        """Preview generated video"""
        if self.generated_video_path and os.path.exists(self.generated_video_path):
            # If already loaded, play directly. Otherwise reload.
            if not hasattr(self.video_player,
                           'video_path') or self.video_player.video_path != self.generated_video_path:
                self.video_player.set_video(self.generated_video_path)

            # Play video
            self.video_player.play_pause()
            self.append_log(f"Previewing video: {self.generated_video_path}")

    def open_folder(self):
        """Open directory where file is located"""
        if self.generated_video_path and os.path.exists(self.generated_video_path):
            folder_path = os.path.dirname(self.generated_video_path)
            self.append_log(f"Opening folder: {folder_path}")

            # Open folder based on OS
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS, Linux
                if 'darwin' in os.sys.platform:  # macOS
                    subprocess.run(['open', folder_path])
                else:  # Linux
                    subprocess.run(['xdg-open', folder_path])

    def append_log(self, message):
        """Add log message"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        self.log_text.append(log_message)
        # Scroll to bottom
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def clear_log(self):
        """Clear log"""
        self.log_text.clear()
        self.append_log("Log cleared")

    def save_log(self):
        """Save log"""
        try:
            # Create logs folder
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Create log filename
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(log_dir, f"process_log_{timestamp}.txt")

            # Save log content
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())

            self.append_log(f"Log saved to: {log_file}")
        except Exception as e:
            self.append_log(f"Failed to save log: {str(e)}")