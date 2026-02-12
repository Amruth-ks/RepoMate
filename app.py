import sys
import os
import threading
import wave
import sounddevice as sd
import numpy as np
import speech_recognition as sr
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QListWidget, QListWidgetItem, QLineEdit, QScrollArea, QFrame,
    QGridLayout, QGraphicsDropShadowEffect, QSizePolicy, QPlainTextEdit, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette

from git_assist.main import processor, planner, builder, validator
from git_assist.git_manager import GitManager

# ================== STYLES ==================
STYLESHEET = """
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}
/* Panels (Cards) */
QFrame#Card {
    background-color: #2d2d2d;
    border-radius: 12px;
    border: 1px solid #3d3d3d;
}
QFrame#Card:hover {
    border: 1px solid #4d4d4d;
}

/* Header */
QLabel#Title {
    font-size: 24px;
    font-weight: bold;
    color: #ffffff;
}
QLabel#Subtitle {
    font-size: 14px;
    color: #aaaaaa;
}

/* Buttons */
QPushButton {
    background-color: #3d3d3d;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    color: white;
}
QPushButton:hover {
    background-color: #4d4d4d;
}
QPushButton#PrimaryBtn {
    background-color: #007acc;
}
QPushButton#PrimaryBtn:hover {
    background-color: #008ae6;
}
QPushButton#ExecuteBtn {
    background-color: #28a745;
    font-weight: bold;
}
QPushButton#ExecuteBtn:hover {
    background-color: #34ce57;
}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 8px;
    color: white;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #007acc;
}

/* List */
QListWidget {
    background-color: transparent;
    border: none;
}
QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #3d3d3d;
}

/* Dropdown (Combo) */
QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 6px;
    padding-left: 10px;
    color: #e0e0e0;
    font-size: 13px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px; 
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    selection-background-color: #007acc;
    border: 1px solid #3d3d3d;
    color: #e0e0e0;
}
"""

# ================== AUDIO THREAD ==================
class AudioThread(QThread):
    finished = pyqtSignal(str)
    
    def __init__(self, device_index=None):
        super().__init__()
        self.running = False
        self.frames = []
        self.device_index = device_index
        self.samplerate = 16000 # fixed sample rate

    def callback(self, indata, frames, time, status):
        if self.running:
            self.frames.append(indata.copy())

    def run(self):
        self.running = True
        self.frames = []

        try:
            with sd.InputStream(
                device=self.device_index,
                samplerate=self.samplerate,
                channels=1,
                dtype="int16",
                callback=self.callback
            ):
                while self.running:
                    sd.sleep(50)
        except Exception as e:
             self.finished.emit(f"Error: {str(e)}")
             return

        # PROCESS AUDIO (Now in background thread)
        if not self.frames:
            self.finished.emit("")
            return

        # Concatenate
        raw_audio = np.concatenate(self.frames, axis=0)
        
        # --- NORMALIZE (Maximize Volume) ---
        # Convert to float
        audio_float = raw_audio.astype(np.float32)
        
        # Find peak
        peak = np.abs(audio_float).max()
        print(f"[DEBUG] Raw Peak: {peak}")
        
        if peak > 0:
            target_peak = 25000.0
            scale_factor = target_peak / peak
            scale_factor = min(scale_factor, 50.0) 
            
            audio_float *= scale_factor
            print(f"[DEBUG] Applied Gain: {scale_factor:.2f}x")
            
        # Clip and convert back
        audio_float = np.clip(audio_float, -32768, 32767)
        audio = audio_float.astype(np.int16)

        # DEBUG: Log final info
        vol = np.abs(audio).mean()
        print(f"[DEBUG] Final Mean Volume: {vol}")
        
        # Save to WAV for debugging
        try:
            with wave.open("debug_audio.wav", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2) # 16-bit
                wf.setframerate(16000)
                wf.writeframes(audio.tobytes())
            print("[DEBUG] Saved debug_audio.wav")
            # Emit debug info first (optional, but might be safer to just emit one final result or use a separate signal)
            # For simplicity, we'll rely on prints or append to final text if really needed, 
            # but emitting multiple times on 'finished' might confuse the slot.
            # Let's just print for now, or emit a special debug signal if we had one.
        except Exception as e:
            print(f"[WARN] Could not save wav: {e}")

        if vol < 50: 
             # Just print to console to avoid cluttering UI with non-final messages
             print(f"[DEBUG] Audio quiet (Vol: {vol:.2f}), trying anyway...")

        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(audio.tobytes(), 16000, 2)

        try:
            text = recognizer.recognize_google(audio_data)
            self.finished.emit(text)
        except sr.UnknownValueError:
            self.finished.emit(f"[DEBUG] Audio captured (Vol: {vol:.2f}) but not understood.")
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")

    def stop(self):
        self.running = False

# ================== WORKER THREADS ==================

class AIWorker(QThread):
    finished = pyqtSignal(object, list) # plan (dict), commands (list)
    error = pyqtSignal(str)
    
    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
             # 1. Normalize
            norm_text, lang = processor.normalize(self.text)
            
            # 2. Plan
            plan = planner.generate_plan(norm_text)
            
            # 3. Validate
            safe, msg = validator.validate(plan)
            if not safe:
                self.error.emit(f"Unsafe Plan: {msg}")
                return

            # 4. Build
            commands = builder.build(plan)
            self.finished.emit(plan, commands)
            
        except Exception as e:
            self.error.emit(str(e))

class CommandWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, git_manager, commands):
        super().__init__()
        self.git = git_manager
        self.commands = commands

    def run(self):
        self.progress.emit("[EXEC] Worker started...")
        try:
            # We iterate here to provide real-time updates if we refactor execute_commands later
            # For now, we assume execute_commands runs them all and returns results
            # To be non-blocking, this whole method is already in a thread, so it's fine.
            results = self.git.execute_commands(self.commands)
            for res in results:
                self.progress.emit(res)
        except Exception as e:
            self.progress.emit(f"[ERROR] Execution failed: {e}")
        finally:
            self.finished.emit()

# ================== CUSTOM WIDGETS ==================

class StatusCard(QFrame):
    def __init__(self, title, icon_char):
        super().__init__()
        self.setObjectName("Card")
        self.setStyleSheet("background-color: #252526;")
        
        layout = QVBoxLayout(self)
        
        self.lbl_icon = QLabel(icon_char)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet("font-size: 24px; color: #aaaaaa;")
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet("font-weight: bold; color: #cccccc;")
        
        self.lbl_value = QLabel("...")
        self.lbl_value.setAlignment(Qt.AlignCenter)
        self.lbl_value.setStyleSheet("font-size: 12px; color: #888888;")
        
        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        
    def set_status(self, is_good, text):
        self.lbl_value.setText(text)
        if is_good:
            self.lbl_icon.setStyleSheet("font-size: 24px; color: #28a745;") # Green
        else:
            self.lbl_icon.setStyleSheet("font-size: 24px; color: #dc3545;") # Red or Orange

class FileRowWidget(QWidget):
    def __init__(self, filename, status_code, color):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_status = QLabel(status_code)
        self.lbl_status.setFixedSize(30, 30)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet(f"background-color: {color}; color: black; border-radius: 4px; font-weight: bold;")
        
        self.lbl_name = QLabel(filename)
        self.lbl_name.setStyleSheet("padding-left: 10px;")
        
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.lbl_name)
        layout.addStretch()

# ================== MAIN APP ==================

class GitEaseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitEase - AI Version Control")
        self.resize(1000, 700)
        self.setStyleSheet(STYLESHEET)
        
        self.git = GitManager(".")
        self.current_plan = None
        
        self.setup_ui()
        
        # Log Audio Devices
        try:
            devices = sd.query_devices()
            print(f"[DEBUG] Audio Devices:\n{devices}")
            self.log_area.append(f"[INFO] Default Device: {sd.query_devices(kind='input')['name']}")
        except Exception as e:
            print(f"[WARN] Could not query devices: {e}")

        # Poll git status
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_git_status)
        self.timer.start(5000) # every 5s
        self.update_git_status() # Initial call

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- HEADER ---
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        self.title = QLabel("GitEase")
        self.title.setObjectName("Title")
        self.subtitle = QLabel("Version Control System (AIGVS)")
        self.subtitle.setObjectName("Subtitle")
        title_box.addWidget(self.title)
        title_box.addWidget(self.subtitle)
        
        self.path_label = QLabel("Path: ...")
        self.path_label.setStyleSheet("color: #888888;")
        
        header.addLayout(title_box)
        header.addStretch()
        header.addWidget(self.path_label)
        
        main_layout.addLayout(header)

        # --- BODY (Split) ---
        body = QHBoxLayout()
        
        # -- LEFT PANEL (Repo Status) --
        left_panel = QFrame()
        left_panel.setObjectName("Card")
        left_layout = QVBoxLayout(left_panel)
        
        # Repo Selector (Mock)
        self.btn_repoload = QPushButton("Select Repository")
        self.btn_repoload.setObjectName("PrimaryBtn")
        left_layout.addWidget(self.btn_repoload)
        
        # Status Cards Grid
        status_grid = QHBoxLayout()
        self.card_repo = StatusCard("Repo", "📂")
        self.card_remote = StatusCard("Remote", "☁️")
        self.card_tree = StatusCard("Tree", "🌳")
        status_grid.addWidget(self.card_repo)
        status_grid.addWidget(self.card_remote)
        status_grid.addWidget(self.card_tree)
        left_layout.addLayout(status_grid)
        
        # File List
        left_layout.addWidget(QLabel("File Status List:"))
        self.file_list = QListWidget()
        left_layout.addWidget(self.file_list)
        
        body.addWidget(left_panel, 1) # 1/3 width

        # -- RIGHT PANEL (Command Center) --
        right_panel = QFrame()
        right_panel.setObjectName("Card")
        right_layout = QVBoxLayout(right_panel)
        
        # Chat / Input
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setPlaceholderText("AI Chat History...")
        right_layout.addWidget(self.chat_area, 2)
        
        # Mic Selector
        self.combo_mic = QComboBox()
        self.populate_mics()
        right_layout.addWidget(self.combo_mic)
        
        input_box = QHBoxLayout()
        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Type instruction (e.g., 'Sync my work')...")
        self.btn_mic = QPushButton("🎤")
        self.btn_mic.setFixedSize(40, 40)
        self.btn_mic.clicked.connect(self.toggle_recording)
        
        input_box.addWidget(self.txt_input)
        input_box.addWidget(self.btn_mic)
        right_layout.addLayout(input_box)
        
        # Actions
        self.btn_plan = QPushButton("Plan Action")
        self.btn_plan.setObjectName("PrimaryBtn")
        self.btn_plan.clicked.connect(self.plan_action)
        right_layout.addWidget(self.btn_plan)
        
        right_layout.addWidget(QLabel("Planned Commands:"))
        self.plan_preview = QPlainTextEdit()
        self.plan_preview.setReadOnly(True)
        self.plan_preview.setStyleSheet("font-family: Consolas; font-size: 13px;")
        right_layout.addWidget(self.plan_preview, 2)
        
        self.btn_execute = QPushButton("Execute")
        self.btn_execute.setObjectName("ExecuteBtn")
        self.btn_execute.clicked.connect(self.execute_plan)
        self.btn_execute.setEnabled(False)
        right_layout.addWidget(self.btn_execute)

        body.addWidget(right_panel, 1) # 1/3 width
        
        main_layout.addLayout(body, 3) # Body takes 3 parts height

        # --- FOOTER (Logs) ---
        footer = QFrame()
        footer.setObjectName("Card")
        footer.setStyleSheet("background-color: #000000;")
        footer_layout = QVBoxLayout(footer)
        
        footer_layout.addWidget(QLabel("Logs & Output"))
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: transparent; border: none; font-family: Consolas;")
        footer_layout.addWidget(self.log_area)
        
        main_layout.addWidget(footer, 1) # Footer takes 1 part height

    # ================== LOGIC ==================
    
    def log(self, message):
        self.log_area.append(message)
        # Auto scroll
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_git_status(self):
        status = self.git.get_status()
        
        # Update Header
        self.path_label.setText(f"Path: {self.git.repo_path}  |  Branch: {status['current_branch']}")
        
        # Update Cards
        self.card_repo.set_status(status['initialized'], "Initialized" if status['initialized'] else "No Repo")
        self.card_remote.set_status(status['remote_connected'], "Connected" if status['remote_connected'] else "No Remote")
        self.card_tree.set_status(status['pending_changes'] == 0, f"{status['pending_changes']} Pending")
        
        # Update File List (Only redraw if count changed to avoid flickering, simplistic for now)
        # For a smooth UI, we should diff, but clearing is fine for prototype
        self.file_list.clear()
        for f in status['files']:
            item = QListWidgetItem(self.file_list)
            widget = FileRowWidget(f['name'], f['status'], f['color'])
            item.setSizeHint(widget.sizeHint())
            self.file_list.setItemWidget(item, widget)

    def populate_mics(self):
        self.combo_mic.clear()
        try:
            devices = sd.query_devices()
            # default_input = sd.query_devices(kind='input')
            # default_index = default_input['index'] if default_input else -1
            
            # User Preference: Default to index 7 if available
            target_index = 7
            has_target = False
            
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    name = dev['name']
                    # Mark requested default
                    if i == target_index:
                        name += " (Preferred)"
                        has_target = True
                        
                    self.combo_mic.addItem(f"{i}: {name}", i)
                    
                    if i == target_index:
                         self.combo_mic.setCurrentIndex(self.combo_mic.count() - 1)
            
            # If target 7 wasn't found, maybe select system default or 0
            if not has_target and self.combo_mic.count() > 0:
                 self.combo_mic.setCurrentIndex(0)

        except Exception as e:
            self.combo_mic.addItem(f"Error listing mics: {e}")

    def toggle_recording(self):
        if hasattr(self, "is_recording") and self.is_recording:
            # STOP RECORDING
            self.log("[INFO] processing audio...")
            self.btn_mic.setStyleSheet("background-color: orange;") # Orange for processing
            self.btn_mic.setEnabled(False) # Prevent double clicks
            self.recorder.stop()
            # self.recorder.wait() # REMOVED: Do not block GUI
            self.is_recording = False
        else:
            # START RECORDING
            idx = self.combo_mic.currentData()
            if idx is None:
                idx = sd.default.device[0] # Fallback
                
            self.log(f"[INFO] Listening on Device {idx}... (Click again to stop)")
            self.btn_mic.setStyleSheet("background-color: red;")
            
            self.recorder = AudioThread(device_index=idx)
            self.recorder.finished.connect(self.on_recording_finished)
            self.recorder.start()
            self.is_recording = True

    def on_recording_finished(self, text):
        # Reset UI
        self.btn_mic.setStyleSheet("") 
        self.btn_mic.setEnabled(True)
        
        if not text:
            self.log("[WARN] No speech detected")
            return

        if text.startswith("[DEBUG]"):
            self.log(text)
            return

        if text.startswith("Error"):
            self.log(f"[ERROR] {text}")
            return

        # Success case
        self.txt_input.setText(text)
        self.log(f"[AUDIO] Heard: {text}")
        self.plan_action() # Auto plan on voice

    def plan_action(self):
        instruction = self.txt_input.text()
        if not instruction:
            self.log("[WARN] Please enter an instruction")
            return
            
        self.log(f"[AI] Planning: '{instruction}'...")
        self.chat_area.append(f"User: {instruction}")
        self.btn_plan.setEnabled(False) # Disable while planning
        
        # Start AI Worker
        self.ai_worker = AIWorker(instruction)
        self.ai_worker.finished.connect(self.on_plan_finished)
        self.ai_worker.error.connect(self.on_plan_error)
        self.ai_worker.start()

    def on_plan_finished(self, plan, commands):
        self.btn_plan.setEnabled(True)
        self.current_plan = plan
        self.current_plan_commands = commands
        
        self.chat_area.append(f"AI: I have created a plan.")
        self.plan_preview.setPlainText("\n".join(commands))
        self.btn_execute.setEnabled(True)
        self.log(f"[SUCCESS] Plan generated with {len(commands)} commands.")

    def on_plan_error(self, msg):
        self.btn_plan.setEnabled(True)
        self.log(f"[ERROR] Planning failed: {msg}")
        self.chat_area.append(f"AI: Error: {msg}")

    def execute_plan(self):
        if not self.current_plan_commands:
            return
            
        self.log("[EXEC] Starting background execution...")
        self.btn_execute.setEnabled(False)
        
        # Start Command Worker
        self.cmd_worker = CommandWorker(self.git, self.current_plan_commands)
        self.cmd_worker.progress.connect(self.log)
        self.cmd_worker.finished.connect(self.on_execute_finished)
        self.cmd_worker.start()

    def on_execute_finished(self):
        self.log("[DONE] Execution finished.")
        self.update_git_status() # Refresh UI
        self.txt_input.clear()
        self.plan_preview.clear()
        self.current_plan_commands = None
        # self.btn_execute.setEnabled(True) # Keep disabled until new plan

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set Fusion Theme for consistent look across platforms
    app.setStyle("Fusion")
    
    window = GitEaseApp()
    window.show()
    sys.exit(app.exec_())
