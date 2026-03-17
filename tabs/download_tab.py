import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox)

from ui_components import CustomSlider, RadioButtonGroup, VideoPlayer

# Try to import actual function modules
try:
    from tools.step000_video_downloader import download_from_url
except ImportError:
    pass


class DownloadTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Video URL
        self.video_url = QLineEdit()
        self.video_url.setPlaceholderText("Please enter the URL of a Youtube or Bilibili video, playlist, or channel")
        self.video_url.setText("https://www.bilibili.com/video/BV1kr421M7vz/")
        self.layout.addWidget(QLabel("Video URL"))
        self.layout.addWidget(self.video_url)

        # Video Output Folder
        self.video_folder = QLineEdit("videos")
        self.layout.addWidget(QLabel("Video Output Folder"))
        self.layout.addWidget(self.video_folder)

        # Resolution
        self.resolution = RadioButtonGroup(
            ['4320p', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p'],
            "Resolution",
            '1080p'
        )
        self.layout.addWidget(self.resolution)

        # Number of Videos to Download
        self.video_count = CustomSlider(1, 100, 1, "Number of Videos to Download", 5)
        self.layout.addWidget(self.video_count)

        # Run Button
        self.run_button = QPushButton("Start Download")
        self.run_button.clicked.connect(self.run_download)
        self.layout.addWidget(self.run_button)

        # Status Display
        self.status_label = QLabel("Ready")
        self.layout.addWidget(QLabel("Download Status:"))
        self.layout.addWidget(self.status_label)

        # Video Player
        self.video_player = VideoPlayer("Sample Video")
        self.layout.addWidget(self.video_player)

        # Download Information
        self.download_info = QLabel("Download information will be displayed here")
        self.layout.addWidget(QLabel("Download Information:"))
        self.layout.addWidget(self.download_info)

        self.setLayout(self.layout)

    def run_download(self):
        # This should call the original download_from_url function
        # Temporary implementation, needs to be replaced with real call in actual application
        self.status_label.setText("Downloading...")
        QMessageBox.information(self, "Feature Hint", "Download feature is being implemented...")

        # Uncomment the following in actual application

        try:
            status, video_path, info = download_from_url(
                self.video_url.text(),
                self.video_folder.text(),
                self.resolution.value(),
                self.video_count.value()
            )
            self.status_label.setText(status)
            if video_path and os.path.exists(video_path):
                self.video_player.set_video(video_path)
            self.download_info.setText(str(info))
        except Exception as e:
            self.status_label.setText(f"Download Failed: {str(e)}")
