import os
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
                               QPushButton, QMessageBox, QSplitter)
from PySide6.QtCore import Qt, Signal

from ui_components import (CustomSlider, FloatSlider, RadioButtonGroup,
                           AudioSelector, VideoPlayer)


class SettingsTab(QWidget):
    """
    Settings page, allows users to set all processing parameters and save to config.json
    """
    # Define configuration change signal
    config_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize configuration page UI"""
        self.layout = QVBoxLayout(self)

        # Create a scroll area to contain configuration items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        # Add all configuration widgets
        self.add_config_widgets()

        # Create save configuration buttons
        self.button_layout = QHBoxLayout()
        self.save_config_button = QPushButton("Save Configuration")
        self.save_config_button.clicked.connect(self.save_config)
        self.save_config_button.setMinimumHeight(40)
        self.save_config_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.reset_config_button = QPushButton("Reset Configuration")
        self.reset_config_button.clicked.connect(self.reset_config)
        self.reset_config_button.setMinimumHeight(40)
        self.button_layout.addWidget(self.reset_config_button)
        self.button_layout.addWidget(self.save_config_button)

        # Set scroll area
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def add_config_widgets(self):
        """Add all configuration widgets"""
        # Video Configuration
        self.scroll_layout.addWidget(QLabel("=== Video Download Configuration ==="))
        self.scroll_layout.addWidget(QLabel("Video Output Folder"))
        self.video_folder = self.add_label_value("videos", "Video output to this folder")

        # Resolution
        self.resolution = RadioButtonGroup(
            ['4320p', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p'],
            "Resolution",
            '1080p'
        )
        self.scroll_layout.addWidget(self.resolution)

        # Video download count
        self.video_count = CustomSlider(1, 100, 1, "Number of Videos to Download", 5)
        self.scroll_layout.addWidget(self.video_count)

        # Audio processing configuration
        self.scroll_layout.addWidget(QLabel("=== Audio Processing Configuration ==="))
        # Model
        self.model = RadioButtonGroup(
            ['htdemucs', 'htdemucs_ft', 'htdemucs_6s', 'hdemucs_mmi', 'mdx', 'mdx_extra', 'mdx_q', 'mdx_extra_q',
             'SIG'],
            "Vocal Separation Model",
            'htdemucs_ft'
        )
        self.scroll_layout.addWidget(self.model)

        # Compute device
        self.device = RadioButtonGroup(['auto', 'cuda', 'cpu'], "Compute Device", 'auto')
        self.scroll_layout.addWidget(self.device)

        # Number of shifts
        self.shifts = CustomSlider(0, 10, 1, "Number of Shifts", 5)
        self.scroll_layout.addWidget(self.shifts)

        # ASR configuration
        self.scroll_layout.addWidget(QLabel("=== Speech Recognition Configuration ==="))
        # ASR model selection
        self.asr_model_label = QLabel("ASR Model Selection")
        self.scroll_layout.addWidget(self.asr_model_label)
        self.asr_model = RadioButtonGroup(['WhisperX', 'FunASR'], "ASR Model Selection", 'WhisperX')
        self.scroll_layout.addWidget(self.asr_model)

        # WhisperX model size
        self.whisperx_size = RadioButtonGroup(['large', 'medium', 'small', 'base', 'tiny'], "WhisperX Model Size", 'large')
        self.scroll_layout.addWidget(self.whisperx_size)

        # Batch size
        self.batch_size = CustomSlider(1, 128, 1, "Batch Size", 32)
        self.scroll_layout.addWidget(self.batch_size)

        # Separate multiple speakers
        self.separate_speakers = RadioButtonGroup([True, False], "Separate Multiple Speakers", True)
        self.scroll_layout.addWidget(self.separate_speakers)

        # Min speakers
        self.min_speakers = RadioButtonGroup([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], "Min Speakers", None)
        self.scroll_layout.addWidget(self.min_speakers)

        # Max speakers
        self.max_speakers = RadioButtonGroup([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], "Max Speakers", None)
        self.scroll_layout.addWidget(self.max_speakers)

        # Translation configuration
        self.scroll_layout.addWidget(QLabel("=== Translation Configuration ==="))
        # Translation method
        self.translation_method_label = QLabel("Translation Method")
        self.scroll_layout.addWidget(self.translation_method_label)
        self.translation_method = RadioButtonGroup(
            ['OpenAI', 'LLM', 'Google Translate', 'Bing Translate', 'Ernie', 'ByteDance-DeepSeek', "deepseek-api",
             "Alibaba-Qwen","Ollama"], "Translation Method", 'LLM')
        self.scroll_layout.addWidget(self.translation_method)

        # Target language (Translation)
        self.target_language_translation_label = QLabel("Target Language (Translation)")
        self.scroll_layout.addWidget(self.target_language_translation_label)
        self.target_language_translation = RadioButtonGroup(
            ['Simplified Chinese', 'Traditional Chinese', 'English', 'Cantonese', 'Japanese', 'Korean', 'Romanian'], "Target Language (Translation)", 'Simplified Chinese')
        self.scroll_layout.addWidget(self.target_language_translation)

        # TTS configuration
        self.scroll_layout.addWidget(QLabel("=== Speech Synthesis Configuration ==="))
        # AI speech generation method
        self.tts_method_label = QLabel("AI Speech Generation Method")
        self.scroll_layout.addWidget(self.tts_method_label)
        self.tts_method = RadioButtonGroup(['xtts', 'cosyvoice', 'EdgeTTS'], "AI Speech Generation Method", 'EdgeTTS')
        self.scroll_layout.addWidget(self.tts_method)

        # Target language (TTS)
        self.target_language_tts_label = QLabel("Target Language (TTS)")
        self.scroll_layout.addWidget(self.target_language_tts_label)
        self.target_language_tts = RadioButtonGroup(
            ['Chinese', 'English', 'Cantonese', 'Japanese', 'Korean', 'Spanish', 'French', 'Romanian'], "Target Language (TTS)", 'Chinese')
        self.scroll_layout.addWidget(self.target_language_tts)

        # EdgeTTS voice selection
        self.edge_tts_voice_label = QLabel("EdgeTTS Voice Selection")
        self.scroll_layout.addWidget(self.edge_tts_voice_label)
        self.edge_tts_voice = RadioButtonGroup(
            ['zh-CN-XiaoxiaoNeural', 'zh-CN-YunxiNeural', 'en-US-JennyNeural', 'ja-JP-NanamiNeural'],
            "EdgeTTS Voice Selection", 'zh-CN-XiaoxiaoNeural')
        self.scroll_layout.addWidget(self.edge_tts_voice)

        # Video synthesis configuration
        self.scroll_layout.addWidget(QLabel("=== Video Synthesis Configuration ==="))
        # Add subtitles
        self.add_subtitles = RadioButtonGroup([True, False], "Add Subtitles", True)
        self.scroll_layout.addWidget(self.add_subtitles)

        # Speed factor
        self.speed_factor = FloatSlider(0.5, 2, 0.05, "Speed Factor", 1.00)
        self.scroll_layout.addWidget(self.speed_factor)

        # Frame rate
        self.frame_rate = CustomSlider(1, 60, 1, "Frame Rate", 30)
        self.scroll_layout.addWidget(self.frame_rate)

        # Background music
        self.background_music = AudioSelector("Background Music")
        self.scroll_layout.addWidget(self.background_music)

        # BGM volume
        self.bg_music_volume = FloatSlider(0, 1, 0.05, "BGM Volume", 0.5)
        self.scroll_layout.addWidget(self.bg_music_volume)

        # Video volume
        self.video_volume = FloatSlider(0, 1, 0.05, "Video Volume", 1.0)
        self.scroll_layout.addWidget(self.video_volume)

        # Output resolution
        self.output_resolution = RadioButtonGroup(
            ['4320p', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p'],
            "Output Resolution",
            '1080p'
        )
        self.scroll_layout.addWidget(self.output_resolution)

        # Advanced configuration
        self.scroll_layout.addWidget(QLabel("=== Advanced Configuration ==="))
        # Max Workers
        self.max_workers = CustomSlider(1, 100, 1, "Max Workers", 1)
        self.scroll_layout.addWidget(self.max_workers)

        # Max Retries
        self.max_retries = CustomSlider(1, 10, 1, "Max Retries", 3)
        self.scroll_layout.addWidget(self.max_retries)

    def add_label_value(self, value, tooltip=None):
        """Create a label for simple text values"""
        label = QLabel(value)
        if tooltip:
            label.setToolTip(tooltip)
        self.scroll_layout.addWidget(label)
        return label

    def get_config(self):
        """Get current configuration from UI controls"""
        config = {
            "video_folder": self.video_folder.text(),
            "resolution": self.resolution.value(),
            "video_count": self.video_count.value(),
            "model": self.model.value(),
            "device": self.device.value(),
            "shifts": self.shifts.value(),
            "asr_model": self.asr_model.value(),
            "whisperx_size": self.whisperx_size.value(),
            "batch_size": self.batch_size.value(),
            "separate_speakers": self.separate_speakers.value(),
            "min_speakers": self.min_speakers.value(),
            "max_speakers": self.max_speakers.value(),
            "translation_method": self.translation_method.value(),
            "target_language_translation": self.target_language_translation.value(),
            "tts_method": self.tts_method.value(),
            "target_language_tts": self.target_language_tts.value(),
            "edge_tts_voice": self.edge_tts_voice.value(),
            "add_subtitles": self.add_subtitles.value(),
            "speed_factor": self.speed_factor.value(),
            "frame_rate": self.frame_rate.value(),
            "background_music": self.background_music.value(),
            "bg_music_volume": self.bg_music_volume.value(),
            "video_volume": self.video_volume.value(),
            "output_resolution": self.output_resolution.value(),
            "max_workers": self.max_workers.value(),
            "max_retries": self.max_retries.value()
        }
        return config

    def apply_config(self, config):
        """Apply configuration to UI controls"""
        try:
            # Basic settings
            self.video_folder.setText(config.get("video_folder", "videos"))

            # Apply robust selection logic for each radio button group
            # Resolution
            resolution_value = config.get("resolution", "1080p")
            self._set_radio_button(self.resolution.buttons, resolution_value, "1080p")

            # Video count
            self.video_count.setValue(config.get("video_count", 5))

            # Model
            model_value = config.get("model", "htdemucs_ft")
            self._set_radio_button(self.model.buttons, model_value, "htdemucs_ft")

            # Device
            device_value = config.get("device", "auto")
            self._set_radio_button(self.device.buttons, device_value, "auto")

            # Shifts
            self.shifts.setValue(config.get("shifts", 5))

            # ASR model
            asr_model_value = config.get("asr_model", "WhisperX")
            self._set_radio_button(self.asr_model.buttons, asr_model_value, "WhisperX")

            # WhisperX size
            whisperx_size_value = config.get("whisperx_size", "large")
            self._set_radio_button(self.whisperx_size.buttons, whisperx_size_value, "large")

            # Batch size
            self.batch_size.setValue(config.get("batch_size", 32))

            # Separate speakers
            separate_speakers_value = config.get("separate_speakers", True)
            self._set_radio_button(self.separate_speakers.buttons, separate_speakers_value, True)

            # Min speakers
            min_speakers_value = config.get("min_speakers", None)
            self._set_radio_button(self.min_speakers.buttons, min_speakers_value, None)

            # Max speakers
            max_speakers_value = config.get("max_speakers", None)
            self._set_radio_button(self.max_speakers.buttons, max_speakers_value, None)

            # Translation method
            translation_method_value = config.get("translation_method", "LLM")
            self._set_radio_button(self.translation_method.buttons, translation_method_value, "LLM")

            # Target language (Translation)
            target_lang_trans_value = config.get("target_language_translation", "Simplified Chinese")
            self._set_radio_button(self.target_language_translation.buttons, target_lang_trans_value, "Simplified Chinese")

            # TTS method
            tts_method_value = config.get("tts_method", "EdgeTTS")
            self._set_radio_button(self.tts_method.buttons, tts_method_value, "EdgeTTS")

            # Target language (TTS)
            target_lang_tts_value = config.get("target_language_tts", "Chinese")
            self._set_radio_button(self.target_language_tts.buttons, target_lang_tts_value, "Chinese")

            # EdgeTTS voice
            edge_tts_voice_value = config.get("edge_tts_voice", "zh-CN-XiaoxiaoNeural")
            self._set_radio_button(self.edge_tts_voice.buttons, edge_tts_voice_value, "zh-CN-XiaoxiaoNeural")

            # Add subtitles
            add_subtitles_value = config.get("add_subtitles", True)
            self._set_radio_button(self.add_subtitles.buttons, add_subtitles_value, True)

            # Speed factor
            self.speed_factor.setValue(config.get("speed_factor", 1.00))

            # Frame rate
            self.frame_rate.setValue(config.get("frame_rate", 30))

            # Background music
            if config.get("background_music"):
                self.background_music.file_path.setText(config.get("background_music"))

            # BGM volume
            self.bg_music_volume.setValue(config.get("bg_music_volume", 0.5))

            # Video volume
            self.video_volume.setValue(config.get("video_volume", 1.0))

            # Output resolution
            output_resolution_value = config.get("output_resolution", "1080p")
            self._set_radio_button(self.output_resolution.buttons, output_resolution_value, "1080p")

            # Max workers
            self.max_workers.setValue(config.get("max_workers", 1))

            # Max retries
            self.max_retries.setValue(config.get("max_retries", 3))

        except Exception as e:
            QMessageBox.warning(self, "Configuration Loading Error", f"Error loading configuration: {str(e)}")

    def _set_radio_button(self, buttons, value, default_value):
        """Helper method: safely set radio button value"""
        try:
            # Try to find a matching option and check the corresponding button
            for option, button in buttons:
                if option == value:
                    button.setChecked(True)
                    return

            # If not found, use the default value
            for option, button in buttons:
                if option == default_value:
                    button.setChecked(True)
                    return
        except Exception:
            # If any error occurs, attempt to use the default value
            for option, button in buttons:
                if option == default_value:
                    button.setChecked(True)
                    return

    def save_config(self):
        """Save configuration to JSON file"""
        try:
            config = self.get_config()
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(config_dir, "config.json")

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            QMessageBox.information(self, "Save Successful", f"Configuration saved to {config_path}")

            # Send configuration change signal
            self.config_changed.emit(config)

        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"Error saving configuration: {str(e)}")

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(config_dir, "config.json")

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.apply_config(config)
        except Exception as e:
            QMessageBox.warning(self, "Load Configuration Failed", f"Error loading configuration: {str(e)}")

    def reset_config(self):
        """Reset configuration to default values"""
        if QMessageBox.question(self, "Confirm Reset", "Are you sure you want to reset all configurations to default values?") == QMessageBox.Yes:
            # Apply default configuration
            default_config = {
                "video_folder": "videos",
                "resolution": "1080p",
                "video_count": 5,
                "model": "htdemucs_ft",
                "device": "auto",
                "shifts": 5,
                "asr_model": "WhisperX",
                "whisperx_size": "large",
                "batch_size": 32,
                "separate_speakers": True,
                "min_speakers": None,
                "max_speakers": None,
                "translation_method": "LLM",
                "target_language_translation": "Simplified Chinese",
                "tts_method": "EdgeTTS",
                "target_language_tts": "Chinese",
                "edge_tts_voice": "zh-CN-XiaoxiaoNeural",
                "add_subtitles": True,
                "speed_factor": 1.00,
                "frame_rate": 30,
                "background_music": None,
                "bg_music_volume": 0.5,
                "video_volume": 1.0,
                "output_resolution": "1080p",
                "max_workers": 1,
                "max_retries": 3
            }
            self.apply_config(default_config)
            QMessageBox.information(self, "Reset Successful", "All configurations have been reset to default values")