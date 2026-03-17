import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QScrollArea, QCheckBox, QPushButton, QMessageBox)

from ui_components import (FloatSlider, CustomSlider, RadioButtonGroup,
                           AudioSelector, VideoPlayer)

# Try to import actual function modules
try:
    from tools.step050_synthesize_video import synthesize_all_video_under_folder
except ImportError:
    pass


class SynthesizeVideoTab(QWidget):
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

        # Add Subtitles
        self.add_subtitles = QCheckBox("Add Subtitles")
        self.add_subtitles.setChecked(True)
        self.scroll_layout.addWidget(self.add_subtitles)

        # Speed Factor
        self.speed_factor = FloatSlider(0.5, 2, 0.05, "Speed Factor", 1.00)
        self.scroll_layout.addWidget(self.speed_factor)

        # Frame Rate
        self.frame_rate = CustomSlider(1, 60, 1, "Frame Rate", 30)
        self.scroll_layout.addWidget(self.frame_rate)

        # Background Music
        self.background_music = AudioSelector("Background Music")
        self.scroll_layout.addWidget(self.background_music)

        # BGM Volume
        self.bg_music_volume = FloatSlider(0, 1, 0.05, "BGM Volume", 0.5)
        self.scroll_layout.addWidget(self.bg_music_volume)

        # Video Volume
        self.video_volume = FloatSlider(0, 1, 0.05, "Video Volume", 1.0)
        self.scroll_layout.addWidget(self.video_volume)

        # Resolution
        self.resolution = RadioButtonGroup(
            ['4320p', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p'],
            "Resolution",
            '1080p'
        )
        self.scroll_layout.addWidget(self.resolution)

        # Run Button
        self.run_button = QPushButton("Start Synthesizing Video")
        self.run_button.clicked.connect(self.run_synthesis)
        self.scroll_layout.addWidget(self.run_button)

        # Status Display
        self.status_label = QLabel("Ready")
        self.scroll_layout.addWidget(QLabel("Synthesis Status:"))
        self.scroll_layout.addWidget(self.status_label)

        # Video Player
        self.video_player = VideoPlayer("Synthesized Video")
        self.scroll_layout.addWidget(self.video_player)

        # Set scroll area
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)

    def run_synthesis(self):
        # This should call the original synthesize_all_video_under_folder function
        # Temporary implementation, needs to be replaced with real call in actual application
        self.status_label.setText("Synthesizing...")
        QMessageBox.information(self, "Feature Hint", "Video synthesis feature is being implemented...")

        # Uncomment the following in actual application

        try:
            status, video_path = synthesize_all_video_under_folder(
                self.video_folder.text(),
                self.add_subtitles.isChecked(),
                self.speed_factor.value(),
                self.frame_rate.value(),
                self.background_music.value(),
                self.bg_music_volume.value(),
                self.video_volume.value(),
                self.resolution.value()
            )
            self.status_label.setText(status)
            if video_path and os.path.exists(video_path):
                self.video_player.set_video(video_path)
        except Exception as e:
            self.status_label.setText(f"Synthesis Failed: {str(e)}")
