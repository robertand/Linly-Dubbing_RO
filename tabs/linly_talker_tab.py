import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QComboBox, QMessageBox)

from ui_components import VideoPlayer


class LinlyTalkerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Video folder
        self.video_folder = QLineEdit("videos")
        self.layout.addWidget(QLabel("Video Folder"))
        self.layout.addWidget(self.video_folder)

        # AI Dubbing Method
        self.talker_method = QComboBox()
        self.talker_method.addItems(['Wav2Lip', 'Wav2Lipv2', 'SadTalker'])
        self.layout.addWidget(QLabel("AI Dubbing Method"))
        self.layout.addWidget(self.talker_method)

        # Construction tip
        construction_label = QLabel("Under construction, please stay tuned. Refer to https://github.com/Kedreamix/Linly-Talker")
        construction_label.setOpenExternalLinks(True)
        self.layout.addWidget(construction_label)

        # Status display
        self.status_label = QLabel("Under Development")
        self.layout.addWidget(QLabel("Synthesis Status:"))
        self.layout.addWidget(self.status_label)

        # Video player
        self.video_player = VideoPlayer("Synthesized Video")
        self.layout.addWidget(self.video_player)

        self.setLayout(self.layout)