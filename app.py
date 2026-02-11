import sys
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from git_assist.main import run

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QTextEdit, QHBoxLayout, QVBoxLayout
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt


# ================== AUDIO THREAD ==================
class RecordingThread(QThread):
    result = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = False
        self.frames = []

    def callback(self, indata, frames, time, status):
        if self.running:
            self.frames.append(indata.copy())

    def run(self):
        sd.default.device = 7  
        samplerate = 16000
        self.running = True
        self.frames = []

        with sd.InputStream(
            samplerate=samplerate,
            channels=1,
            dtype="int16",
            callback=self.callback
        ):
            while self.running:
                sd.sleep(50)

    def stop(self):
        self.running = False

        if not self.frames:
            self.result.emit("❌ No audio captured")
            return

        audio = np.concatenate(self.frames, axis=0)
        volume = np.abs(audio).mean()

        if volume < 300:
            self.result.emit("❌ Mic too quiet")
            return

        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(audio.tobytes(), 16000, 2)

        try:
            text = recognizer.recognize_google(audio_data)
            run(text)
            self.result.emit(text)
        except sr.UnknownValueError:
            self.result.emit("❌ Could not understand")
        except sr.RequestError:
            self.result.emit("❌ Internet / API error")


class SpeechApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Push To Talk - Speech to Text")
        self.resize(700, 300)

        # STATUS
        self.status_label = QLabel("Hold mic to speak")
        self.status_label.setAlignment(Qt.AlignCenter)

        # MIC BUTTON
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedSize(100, 100)
        self.mic_btn.setStyleSheet(self.idle_style())

        self.mic_btn.pressed.connect(self.start_recording)
        self.mic_btn.released.connect(self.stop_recording)

        # TEXT BOX
        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)
        self.text_box.setPlaceholderText("Recognized text will appear here...")

        # LAYOUTS
        left = QVBoxLayout()
        left.addWidget(self.mic_btn, alignment=Qt.AlignCenter)
        left.addWidget(self.status_label)

        main = QHBoxLayout(self)
        main.addLayout(left, 1)
        main.addWidget(self.text_box, 2)


        self.recognized_text = ""   




    # ---------- STYLES ----------
    def idle_style(self):
        return """
        QPushButton {
            background-color: #1db954;
            border-radius: 50px;
            font-size: 40px;
        }
        """

    def recording_style(self):
        return """
        QPushButton {
            background-color: red;
            border-radius: 50px;
            font-size: 40px;
            color: white;
        }
        """

    # ---------- RECORD CONTROL ----------
    def start_recording(self):
        self.status_label.setText("🎙️ Recording... (hold)")
        self.mic_btn.setStyleSheet(self.recording_style())

        self.thread = RecordingThread()
        self.thread.result.connect(self.display_text)
        self.thread.start()

    def stop_recording(self):
        self.status_label.setText("⏹️ Processing...")
        if hasattr(self, "thread"):
            self.thread.stop()

    def display_text(self, text):
        self.text_box.append(text)
        self.status_label.setText("Hold mic to speak")
        self.mic_btn.setStyleSheet(self.idle_style())


        self.recognized_text = text   
        self.text_box.append(text)



# ================== RUN ==================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpeechApp()
    window.show()
    sys.exit(app.exec_())
