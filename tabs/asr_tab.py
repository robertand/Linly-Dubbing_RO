import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QScrollArea, QComboBox, QCheckBox, QPushButton, QMessageBox)

from ui_components import CustomSlider, RadioButtonGroup

# Try to import actual function modules
try:
    from tools.step020_asr import transcribe_all_audio_under_folder
except ImportError:
    pass


class ASRTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Create a scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        # Video Folder
        self.video_folder = QLineEdit("videos")
        self.scroll_layout.addWidget(QLabel("Video Folder"))
        self.scroll_layout.addWidget(self.video_folder)

        # ASR Model Selection
        self.asr_model = QComboBox()
        self.asr_model.addItems(['WhisperX', 'FunASR'])
        self.scroll_layout.addWidget(QLabel("ASR Model Selection"))
        self.scroll_layout.addWidget(self.asr_model)

        # WhisperX Model Size
        self.whisperx_size = RadioButtonGroup(['large', 'medium', 'small', 'base', 'tiny'], "WhisperX Model Size", 'large')
        self.scroll_layout.addWidget(self.whisperx_size)

        # Compute Device
        self.device = RadioButtonGroup(['auto', 'cuda', 'cpu'], "Compute Device", 'auto')
        self.scroll_layout.addWidget(self.device)

        # Batch Size
        self.batch_size = CustomSlider(1, 128, 1, "Batch Size", 32)
        self.scroll_layout.addWidget(self.batch_size)

        # Separate Multiple Speakers
        self.separate_speakers = QCheckBox("Separate Multiple Speakers")
        self.separate_speakers.setChecked(True)
        self.scroll_layout.addWidget(self.separate_speakers)

        # Min Speakers
        self.min_speakers = RadioButtonGroup([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], "Min Speakers", None)
        self.scroll_layout.addWidget(self.min_speakers)

        # Max Speakers
        self.max_speakers = RadioButtonGroup([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], "Max Speakers", None)
        self.scroll_layout.addWidget(self.max_speakers)

        # Run Button
        self.run_button = QPushButton("Start Recognition")
        self.run_button.clicked.connect(self.run_asr)
        self.scroll_layout.addWidget(self.run_button)

        # Status Display
        self.status_label = QLabel("Ready")
        self.scroll_layout.addWidget(QLabel("ASR Status:"))
        self.scroll_layout.addWidget(self.status_label)

        # Recognition Details
        self.result_detail = QLabel("Recognition results will be displayed here")
        self.scroll_layout.addWidget(QLabel("Recognition Details:"))
        self.scroll_layout.addWidget(self.result_detail)

        # Set scroll area
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)

    def run_asr(self):
        # This should call the original transcribe_all_audio_under_folder function
        # Temporary implementation, needs to be replaced with real call in actual application
        self.status_label.setText("Recognizing...")
        QMessageBox.information(self, "Feature Hint", "AI speech recognition feature is being implemented...")

        # Uncomment the following in actual application

        try:
            status, result_json = transcribe_all_audio_under_folder(
                self.video_folder.text(),
                self.asr_model.currentText(),
                self.whisperx_size.value(),
                self.device.value(),
                self.batch_size.value(),
                self.separate_speakers.isChecked(),
                self.min_speakers.value(),
                self.max_speakers.value()
            )
            self.status_label.setText(status)
            self.result_detail.setText(str(result_json))
        except Exception as e:
            self.status_label.setText(f"Recognition Failed: {str(e)}")
