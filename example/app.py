import sys
import numpy as np
import sounddevice as sd
import speech_recognition as sr

from PyQt5.QtWidgets import (
    QApplication, QWidget,
    QPushButton, QTextEdit,
    QVBoxLayout, QLabel
)
from PyQt5.QtCore import QThread, pyqtSignal


# -------- Worker Thread (does audio work) --------
class SpeechWorker(QThread):
    finished_text = pyqtSignal(str)

    def run(self):
        recognizer = sr.Recognizer()

        # Record audio
        samplerate = 16000
        duration = 5  # seconds

        audio = sd.rec(
    int(duration * samplerate),
    samplerate=samplerate,
    channels=1,
    dtype="int16",
    device=2   # <-- Intel Microphone Array
)

        sd.wait()

        # Convert to SpeechRecognition format
        audio_data = sr.AudioData(
            audio.tobytes(),
            samplerate,
            2
        )

        try:
            text = recognizer.recognize_google(audio_data, language="en-IN")
        except sr.UnknownValueError:
            text = "Could not understand audio"
        except sr.RequestError:
            text = "Network error"

        self.finished_text.emit(text)


# -------- Main Window --------
class VoiceApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Voice to Text")
        self.resize(400, 300)

        self.label = QLabel("Click the button and speak")
        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)

        self.button = QPushButton(" Start Listening")
        self.button.clicked.connect(self.start_recording)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.text_box)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def start_recording(self):
        self.label.setText("Listening...")
        self.button.setEnabled(False)

        self.worker = SpeechWorker()
        self.worker.finished_text.connect(self.show_text)
        self.worker.start()

    def show_text(self, text):
        self.text_box.setText(text)
        self.label.setText("Done")
        self.button.setEnabled(True)


# -------- App Start --------
app = QApplication(sys.argv)
window = VoiceApp()
window.show()
sys.exit(app.exec_())
