import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QPushButton, QMessageBox, QGroupBox)

# Try to import actual function modules
try:
    from tools.step040_tts import generate_all_wavs_under_folder
    from tools.utils import SUPPORT_VOICE
except ImportError:
    # Define temporary support voice list
    SUPPORT_VOICE = ['zh-CN-XiaoxiaoNeural', 'en-US-JennyNeural',
                     'ja-JP-NanamiNeural', 'ro-RO-AlinaNeural']


class TTSTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Video Folder
        self.video_folder = QLineEdit("videos")
        self.layout.addWidget(QLabel("Video Folder"))
        self.layout.addWidget(self.video_folder)

        # AI Speech Generation Method
        self.tts_method = QComboBox()
        self.tts_method.addItems(['xtts', 'cosyvoice', 'EdgeTTS'])
        self.layout.addWidget(QLabel("AI Speech Generation Method"))
        self.layout.addWidget(self.tts_method)

        # Target Language
        self.target_language = QComboBox()
        self.target_language.addItems(['Chinese', 'English', 'Cantonese', 'Japanese', 'Korean', 'Spanish', 'French', 'Romanian'])
        self.target_language.setCurrentText('Chinese')
        self.layout.addWidget(QLabel("Target Language"))
        self.layout.addWidget(self.target_language)

        # EdgeTTS Voice Selection
        self.edge_tts_voice = QComboBox()
        self.edge_tts_voice.addItems(SUPPORT_VOICE)
        self.edge_tts_voice.setCurrentText('zh-CN-XiaoxiaoNeural')
        self.layout.addWidget(QLabel("EdgeTTS Voice Selection"))
        self.layout.addWidget(self.edge_tts_voice)

        # Run Button
        self.run_button = QPushButton("Start Generating Speech")
        self.run_button.clicked.connect(self.run_tts)
        self.layout.addWidget(self.run_button)

        # Status Display
        self.status_label = QLabel("Ready")
        self.layout.addWidget(QLabel("Synthesis Status:"))
        self.layout.addWidget(self.status_label)

        # Audio Controls
        synthesized_group = QGroupBox("Synthesized Speech")
        synthesized_layout = QVBoxLayout()
        self.synthesized_play_button = QPushButton("Play Synthesized Speech")
        synthesized_layout.addWidget(self.synthesized_play_button)
        synthesized_group.setLayout(synthesized_layout)

        original_group = QGroupBox("Original Audio")
        original_layout = QVBoxLayout()
        self.original_play_button = QPushButton("Play Original Audio")
        original_layout.addWidget(self.original_play_button)
        original_group.setLayout(original_layout)

        audio_layout = QHBoxLayout()
        audio_layout.addWidget(synthesized_group)
        audio_layout.addWidget(original_group)

        self.layout.addLayout(audio_layout)
        self.setLayout(self.layout)

    def run_tts(self):
        # This should call the original generate_all_wavs_under_folder function
        # Temporary implementation, needs to be replaced with real call in actual application
        self.status_label.setText("Generating...")
        QMessageBox.information(self, "Feature Hint", "AI speech synthesis feature is being implemented...")

        # Uncomment the following in actual application

        try:
            status, synthesized_path, original_path = generate_all_wavs_under_folder(
                self.video_folder.text(),
                self.tts_method.currentText(),
                self.target_language.currentText(),
                self.edge_tts_voice.currentText()
            )
            self.status_label.setText(status)
            if synthesized_path and os.path.exists(synthesized_path):
                self.synthesized_play_button.setEnabled(True)
            if original_path and os.path.exists(original_path):
                self.original_play_button.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"Generation Failed: {str(e)}")
