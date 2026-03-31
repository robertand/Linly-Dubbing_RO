import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QCheckBox, QGroupBox)

from ui_components import CustomSlider, RadioButtonGroup

# Try to import actual function modules
try:
    from tools.step010_demucs_vr import separate_all_audio_under_folder
except ImportError:
    pass


class DemucsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Video Folder
        self.video_folder = QLineEdit("videos")
        self.layout.addWidget(QLabel("Video Folder"))
        self.layout.addWidget(self.video_folder)

        # Model
        self.model = RadioButtonGroup(
            ['htdemucs', 'htdemucs_ft', 'htdemucs_6s', 'hdemucs_mmi', 'mdx', 'mdx_extra', 'mdx_q', 'mdx_extra_q',
             'SIG'],
            "Model",
            'htdemucs_ft'
        )
        self.layout.addWidget(self.model)

        # Compute Device
        self.device = RadioButtonGroup(['auto', 'cuda', 'cpu'], "Compute Device", 'auto')
        self.layout.addWidget(self.device)

        # Show Progress Bar
        self.show_progress = QCheckBox("Show Progress Bar")
        self.show_progress.setChecked(True)
        self.layout.addWidget(self.show_progress)

        # Number of shifts
        self.shifts = CustomSlider(0, 10, 1, "Number of Shifts", 5)
        self.layout.addWidget(self.shifts)

        # Run Button
        self.run_button = QPushButton("Start Separation")
        self.run_button.clicked.connect(self.run_separation)
        self.layout.addWidget(self.run_button)

        # Status Display
        self.status_label = QLabel("Ready")
        self.layout.addWidget(QLabel("Separation Status:"))
        self.layout.addWidget(self.status_label)

        # Audio Controls
        vocals_group = QGroupBox("Vocals Audio")
        vocals_layout = QVBoxLayout()
        self.vocals_play_button = QPushButton("Play Vocals")
        vocals_layout.addWidget(self.vocals_play_button)
        vocals_group.setLayout(vocals_layout)

        accompaniment_group = QGroupBox("Accompaniment Audio")
        accompaniment_layout = QVBoxLayout()
        self.accompaniment_play_button = QPushButton("Play Accompaniment")
        accompaniment_layout.addWidget(self.accompaniment_play_button)
        accompaniment_group.setLayout(accompaniment_layout)

        audio_layout = QHBoxLayout()
        audio_layout.addWidget(vocals_group)
        audio_layout.addWidget(accompaniment_group)

        self.layout.addLayout(audio_layout)
        self.setLayout(self.layout)

    def run_separation(self):
        # This should call the original separate_all_audio_under_folder function
        # Temporary implementation, needs to be replaced with real call in actual application
        self.status_label.setText("Separating...")
        QMessageBox.information(self, "Feature Hint", "Vocal separation feature is being implemented...")

        # Uncomment the following in actual application

        try:
            status, vocals_path, accompaniment_path = separate_all_audio_under_folder(
                self.video_folder.text(),
                self.model.value(),
                self.device.value(),
                self.show_progress.isChecked(),
                self.shifts.value()
            )
            self.status_label.setText(status)
            if vocals_path and os.path.exists(vocals_path):
                self.vocals_play_button.setEnabled(True)
            if accompaniment_path and os.path.exists(accompaniment_path):
                self.accompaniment_play_button.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"Separation Failed: {str(e)}")
