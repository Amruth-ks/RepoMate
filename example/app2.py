import sys
import numpy as np
import sounddevice as sd
import speech_recognition as sr

from PyQt5.QtWidgets import (
    QApplication, QWidget,
    QPushButton, QTextEdit,
    QLabel, QHBoxLayout, QVBoxLayout
)
from PyQt5.QtCore import QThread, pyqtSignal


# ================= WORKER THREAD =================
class RecorderThread(QThread):
    text_ready = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recording = True
        self.frames = []

    def run(self):
        recognizer = sr.Recognizer()
        samplerate = 16000

        def callback(indata, frames, time, status):
            if self.recording:
                self.frames.append(indata.copy())

        with sd.InputStream(
            samplerate=samplerate,
            channels=1,
            callback=callback,
            device=2
        ):
            while self.recording:
                sd.sleep(100)

        if not self.frames:
            self.text_ready.emit("No audio captured")
            return

        audio_data = np.concatenate(self.frames).flatten()

        # 🔑 Convert float32 → int16
        audio_data = np.int16(audio_data * 32767)

        audio = sr.AudioData(
            audio_data.tobytes(),
            samplerate,
            2
        )

        try:
            text = recognizer.recognize_google(audio, language="en-IN")
        except sr.UnknownValueError:
            text = "Could not understand audio"
        except sr.RequestError:
            text = "Network error"

        self.text_ready.emit(text)

    def stop(self):
        self.recording = False



# ================= MAIN WINDOW =================
class VoiceApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Voice to Text")
        self.resize(700, 300)

        # -------- LEFT SIDE (RECORDING) --------
        self.status_label = QLabel("Hold the button and speak")
        self.status_label.setStyleSheet("font-size: 14px;")

        self.record_button = QPushButton("🎤 HOLD TO RECORD")
        self.record_button.setStyleSheet(
            "background-color: green; color: white; font-size: 16px; padding: 20px;"
        )

        self.record_button.pressed.connect(self.start_recording)
        self.record_button.released.connect(self.stop_recording)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.status_label)
        left_layout.addWidget(self.record_button)
        left_layout.addStretch()

        # -------- RIGHT SIDE (TEXT OUTPUT) --------
        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)
        self.text_box.setStyleSheet("font-size: 14px;")

        # -------- MAIN LAYOUT --------
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self.text_box, 2)

        self.setLayout(main_layout)

        self.worker = None

    def start_recording(self):
        self.status_label.setText("Recording...")
        self.text_box.clear()

        self.record_button.setStyleSheet(
            "background-color: red; color: white; font-size: 16px; padding: 20px;"
        )

        self.worker = RecorderThread()
        self.worker.text_ready.connect(self.show_text)
        self.worker.start()

    def stop_recording(self):
        if self.worker:
            self.status_label.setText("Processing...")
            self.record_button.setStyleSheet(
                "background-color: orange; color: black; font-size: 16px; padding: 20px;"
            )
            self.worker.stop()

    def show_text(self, text):
        self.text_box.setText(text)
        self.status_label.setText("Done")

        self.record_button.setStyleSheet(
            "background-color: green; color: white; font-size: 16px; padding: 20px;"
        )


# ================= APP START =================
app = QApplication(sys.argv)
window = VoiceApp()
window.show()
sys.exit(app.exec_())
