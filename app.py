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
    QGridLayout, QGraphicsDropShadowEffect, QSizePolicy, QPlainTextEdit, QComboBox,
    QStackedWidget, QInputDialog, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette, QLinearGradient, QBrush, QPainter, QPen

# Local imports
try:
    from git_assist.main import processor, planner, builder, validator
    from git_assist.git_manager import GitManager
except ImportError:
    # Fallback for testing environment if needed
    pass

# ================== THEMES & STYLES ==================

THEMES = {
    "dark": {
        "bg": "#0b0f1a",
        "surface": "rgba(20, 26, 42, 180)",
        "surface_hover": "rgba(30, 38, 58, 200)",
        "card_bg": "rgba(22, 28, 48, 200)",
        "border": "#2a344a",
        "text_primary": "#ffffff",
        "text_secondary": "#a0aec0",
        "accent": "#00d2ff",
        "accent_glow": "rgba(0, 210, 255, 60)",
        "success": "#48bb78",
        "error": "#f56565",
        "sidebar_bg": "#121826",
        "input_bg": "rgba(10, 15, 30, 200)",
        "glow": "0px 0px 15px rgba(0, 210, 255, 0.3)"
    },
    "light": {
        "bg": "#f7fafc",
        "surface": "rgba(255, 255, 255, 180)",
        "surface_hover": "rgba(245, 247, 250, 200)",
        "card_bg": "rgba(255, 255, 255, 220)",
        "border": "#e2e8f0",
        "text_primary": "#2d3748",
        "text_secondary": "#718096",
        "accent": "#3182ce",
        "accent_glow": "rgba(49, 130, 206, 40)",
        "success": "#38a169",
        "error": "#e53e3e",
        "sidebar_bg": "#fdfdfd",
        "input_bg": "rgba(255, 255, 255, 200)",
        "glow": "0px 2px 10px rgba(0, 0, 0, 0.05)"
    }
}

def get_stylesheet(theme_name="dark"):
    t = THEMES[theme_name]
    return f"""
    QWidget {{
        background-color: transparent;
        color: {t['text_primary']};
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 14px;
    }}
    
    #MainWindow {{
        background-color: {t['bg']};
    }}
    
    #Sidebar {{
        background-color: {t['sidebar_bg']};
        border-right: 1px solid {t['border']};
    }}
    
    #HeaderBar {{
        background-color: {t['surface']};
        border-bottom: 1px solid {t['border']};
    }}

    QFrame#GlassPanel {{
        background-color: {t['card_bg']};
        border: 1px solid {t['border']};
        border-radius: 16px;
    }}
    
    QLabel#Title {{
        font-size: 20px;
        font-weight: 700;
        color: {t['text_primary']};
        letter-spacing: -0.5px;
    }}
    
    QLabel#SectionLabel {{
        font-size: 11px;
        font-weight: 700;
        color: {t['accent']};
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 4px;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 500;
        color: {t['text_primary']};
    }}
    QPushButton:hover {{
        background-color: {t['surface_hover']};
        border: 1px solid {t['accent']};
    }}
    
    QPushButton#PrimaryBtn {{
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 {t['accent']}, stop:1 #0080ff);
        color: #ffffff;
        border: none;
        font-weight: 700;
        padding: 10px 20px;
    }}
    QPushButton#PrimaryBtn:hover {{
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #33daff, stop:1 #33aaff);
    }}
    
    QPushButton#NavBtn {{
        text-align: left;
        padding: 12px 20px;
        border: none;
        border-radius: 12px;
        color: {t['text_secondary']};
        margin: 2px 0px;
    }}
    QPushButton#NavBtn:hover {{
        background-color: {t['surface_hover']};
        color: {t['text_primary']};
    }}
    QPushButton#NavBtn[active="true"] {{
        background-color: {t['accent_glow']};
        color: {t['accent']};
        font-weight: 700;
    }}

    /* Inputs */
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
        background-color: {t['input_bg']};
        border: 1px solid {t['border']};
        border-radius: 10px;
        padding: 10px;
        color: {t['text_primary']};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {t['accent']};
    }}

    /* Scrollbar Styling */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {t['border']};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    """

# ================== AUDIO THREAD ==================
class AudioThread(QThread):
    finished = pyqtSignal(str)
    
    def __init__(self, device_index=None):
        super().__init__()
        self.running = False
        self.frames = []
        self.device_index = device_index
        self.samplerate = 16000

    def callback(self, indata, frames, time, status):
        if self.running:
            self.frames.append(indata.copy())

    def run(self):
        self.running = True
        self.frames = []
        try:
            with sd.InputStream(device=self.device_index, samplerate=self.samplerate, 
                                channels=1, dtype="int16", callback=self.callback):
                while self.running:
                    sd.sleep(50)
        except Exception as e:
            self.finished.emit(f"Error: {e}")
            return

        if not self.frames:
            self.finished.emit("")
            return

        audio = np.concatenate(self.frames, axis=0)
        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(audio.tobytes(), self.samplerate, 2)
        try:
            text = recognizer.recognize_google(audio_data)
            self.finished.emit(text)
        except:
            self.finished.emit("")

    def stop(self):
        self.running = False

# ================== WORKER THREADS ==================
class AIWorker(QThread):
    finished = pyqtSignal(object, list)
    error = pyqtSignal(str)
    
    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            norm_text, _ = processor.normalize(self.text)
            plan = planner.generate_plan(norm_text)
            safe, msg = validator.validate(plan)
            if not safe:
                self.error.emit(f"Unsafe Plan: {msg}")
                return
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
        try:
            results = self.git.execute_commands(self.commands)
            for res in results:
                self.progress.emit(res)
        except Exception as e:
            self.progress.emit(f"[ERROR] {e}")
        finally:
            self.finished.emit()

# ================== CUSTOM WIDGETS ==================

class GlassPanel(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setObjectName("GlassPanel")
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(THEMES["dark"]['accent_glow']))
        self.setGraphicsEffect(self.shadow)
        
    def update_glow(self, theme_name):
        t = THEMES[theme_name]
        color = QColor(t['accent_glow']) if theme_name == "dark" else QColor(0, 0, 0, 20)
        self.shadow.setColor(color)

class StatusCard(GlassPanel):
    def __init__(self, title, icon_char):
        GlassPanel.__init__(self)
        self.setMinimumHeight(100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_icon = QLabel(icon_char)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet("font-size: 24px;")
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setObjectName("SectionLabel")
        
        self.lbl_value = QLabel("...")
        self.lbl_value.setAlignment(Qt.AlignCenter)
        self.lbl_value.setStyleSheet("font-size: 13px;")
        
        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        
    def set_status(self, is_good, text):
        self.lbl_value.setText(text)
        t = THEMES["dark"]
        color = t['success'] if is_good else t['text_secondary']
        self.lbl_value.setStyleSheet(f"color: {color};")

class WaveformWidget(QWidget):
    def __init__(self, main_app, parent=None):
        QWidget.__init__(self, parent)
        self.main = main_app
        self.setMinimumHeight(40)
        self.bars = 30
        self.active = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
        self.amplitudes = [2] * self.bars

    def set_active(self, active):
        self.active = active
        if not active: self.amplitudes = [2] * self.bars
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        t = THEMES[self.main.current_theme]
        color = QColor(t['accent'])
        w, h = self.width(), self.height()
        bar_w = w / self.bars - 4
        for i in range(self.bars):
            if self.active:
                import random
                self.amplitudes[i] = random.randint(5, h - 10)
            x = i * (bar_w + 4)
            bar_h = self.amplitudes[i]
            y = (h - bar_h) / 2
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(bar_h), 2, 2)

class NavItem(QPushButton):
    def __init__(self, text, icon_char, parent=None):
        QPushButton.__init__(self, parent)
        self.setObjectName("NavBtn")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(50)
        self.setText(f"{icon_char}   {text}")
        self.nav_name = text

class StatusPill(QLabel):
    def __init__(self, text, active=True, parent=None):
        super().__init__(text, parent)
        self.set_state(active)
        self.setFixedSize(130, 28)
        self.setAlignment(Qt.AlignCenter)

    def set_state(self, active):
        t = THEMES["dark"]
        color = t['success'] if active else t['error']
        bg = f"rgba({QColor(color).red()}, {QColor(color).green()}, {QColor(color).blue()}, 30)"
        self.setStyleSheet(f"background-color: {bg}; color: {color}; border: 1px solid {color}; border-radius: 14px; font-size: 11px; font-weight: bold;")

class ModernHeader(QFrame):
    def __init__(self, main_app):
        super().__init__()
        self.setObjectName("HeaderBar")
        self.setFixedHeight(70)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        logo = QLabel("🔗")
        logo.setStyleSheet("font-size: 24px;")
        title = QLabel("RepoMate – AI Git Assistant")
        title.setObjectName("Title")
        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addStretch()
        self.btn_theme = QPushButton("☀️" if main_app.current_theme == "dark" else "🌙")
        self.btn_theme.setFixedSize(40, 40)
        self.btn_theme.clicked.connect(main_app.toggle_theme)
        layout.addWidget(self.btn_theme)
        btn_sett = QPushButton("⚙️")
        btn_sett.setFixedSize(40, 40)
        layout.addWidget(btn_sett)

class ModernSidebar(QFrame):
    def __init__(self, main_app):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(240)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 30, 15, 30)
        layout.setSpacing(8)
        self.nav_items = []
        nav_config = [("Dashboard", "📊"), ("Repositories", "📂"), ("Commit", "📝"), ("Branches", "⇌"), ("History", "↺"), ("Settings", "⚙️")]
        for text, icon in nav_config:
            btn = NavItem(text, icon)
            btn.clicked.connect(main_app.on_nav_clicked)
            layout.addWidget(btn)
            self.nav_items.append(btn)
        layout.addStretch()
        self.pill_git = StatusPill("No Repository", False)
        layout.addWidget(self.pill_git)

class FileRowWidget(QWidget):
    def __init__(self, filename, status_code, color):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        s = QLabel(status_code)
        s.setFixedSize(24, 24)
        s.setAlignment(Qt.AlignCenter)
        s.setStyleSheet(f"background-color: {color}; color: black; border-radius: 4px; font-weight: bold;")
        n = QLabel(filename)
        n.setStyleSheet("padding-left: 8px;")
        layout.addWidget(s)
        layout.addWidget(n)
        layout.addStretch()

# ================== PAGES ==================

class BasePage(QWidget):
    def __init__(self, title, subtitle, main_app):
        super().__init__()
        self.main = main_app
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        header = QVBoxLayout()
        t = QLabel(title); t.setObjectName("Title"); header.addWidget(t)
        s = QLabel(subtitle); s.setStyleSheet("color: #a0aec0; font-size: 13px;"); header.addWidget(s)
        self.layout.addLayout(header)
        self.layout.addSpacing(20)
        self.content_layout = QVBoxLayout()
        self.layout.addLayout(self.content_layout)
        self.layout.addStretch()

class DashboardPage(BasePage):
    def __init__(self, main_app):
        super().__init__("Dashboard", "Welcome to RepoMate – AI Git Assistant", main_app)
        panel = GlassPanel()
        p_lay = QVBoxLayout(panel)
        p_lay.addWidget(QLabel("Repository Path").setObjectName("SectionLabel"))
        row = QHBoxLayout()
        self.txt_repo_path = QLineEdit(); self.txt_repo_path.setReadOnly(True)
        btn_br = QPushButton("Browse"); btn_br.clicked.connect(main_app.select_repo)
        row.addWidget(self.txt_repo_path); row.addWidget(btn_br)
        p_lay.addLayout(row)
        self.content_layout.addWidget(panel)
        grid = QHBoxLayout(); grid.setSpacing(24)
        left = QVBoxLayout(); left.setSpacing(20)
        cmd_p = GlassPanel(); cmd_lay = QVBoxLayout(cmd_p)
        cmd_lay.addWidget(QLabel("AI Command").setObjectName("SectionLabel"))
        self.txt_command = QTextEdit(); self.txt_command.setPlaceholderText("Enter command..."); self.txt_command.setFixedHeight(80)
        cmd_lay.addWidget(self.txt_command)
        ctrl = QHBoxLayout()
        self.btn_mic = QPushButton("🎤"); self.btn_mic.setFixedSize(40, 40); self.btn_mic.clicked.connect(main_app.toggle_recording)
        self.btn_plan = QPushButton("Generate Plan"); self.btn_plan.setObjectName("PrimaryBtn"); self.btn_plan.clicked.connect(main_app.plan_action)
        ctrl.addWidget(self.btn_mic); ctrl.addWidget(self.btn_plan)
        cmd_lay.addLayout(ctrl)
        left.addWidget(cmd_p)
        self.waveform = WaveformWidget(main_app); self.waveform.setVisible(False); left.addWidget(self.waveform)
        self.plan_card = GlassPanel(); self.plan_card.setVisible(False); plan_lay = QVBoxLayout(self.plan_card)
        plan_lay.addWidget(QLabel("Suggested Plan").setObjectName("SectionLabel"))
        self.txt_plan_preview = QPlainTextEdit(); self.txt_plan_preview.setReadOnly(True); self.txt_plan_preview.setStyleSheet("font-family: monospace;")
        plan_lay.addWidget(self.txt_plan_preview)
        self.btn_confirm = QPushButton("Confirm & Execute"); self.btn_confirm.setObjectName("PrimaryBtn"); self.btn_confirm.clicked.connect(main_app.execute_plan)
        plan_lay.addWidget(self.btn_confirm)
        left.addWidget(self.plan_card)
        self.commit_assist = GlassPanel(); self.commit_assist.setVisible(False); ca_lay = QVBoxLayout(self.commit_assist)
        ca_lay.addWidget(QLabel("Commit Message").setObjectName("SectionLabel"))
        c_row = QHBoxLayout(); self.txt_commit_msg = QLineEdit(); btn_ai = QPushButton("AI Gen"); btn_ai.clicked.connect(main_app.generate_commit_ai)
        c_row.addWidget(self.txt_commit_msg); c_row.addWidget(btn_ai)
        ca_lay.addLayout(c_row); left.addWidget(self.commit_assist); left.addStretch()
        right = QVBoxLayout(); right.setSpacing(20)
        out_p = GlassPanel(); out_lay = QVBoxLayout(out_p); out_lay.addWidget(QLabel("Git Output").setObjectName("SectionLabel"))
        self.git_output = QListWidget(); out_lay.addWidget(self.git_output); right.addWidget(out_p)
        st_p = GlassPanel(); st_lay = QVBoxLayout(st_p); st_lay.addWidget(QLabel("Status").setObjectName("SectionLabel"))
        self.card_branch = StatusCard("Branch", "⇌"); self.card_status = StatusCard("Changes", "●"); self.card_last = StatusCard("Last Commit", "🕒")
        st_lay.addWidget(self.card_branch); st_lay.addWidget(self.card_status); st_lay.addWidget(self.card_last); right.addWidget(st_p); right.addStretch()
        grid.addLayout(left, 3); grid.addLayout(right, 2); self.content_layout.addLayout(grid)

class RepositoriesPage(BasePage):
    def __init__(self, main_app):
        super().__init__("Repositories", "Manage workspace", main_app)
        p = GlassPanel(); l = QVBoxLayout(p); l.addWidget(QLabel("Active Repo").setObjectName("SectionLabel"))
        self.lbl_current = QLabel("None"); self.lbl_current.setStyleSheet("font-size: 16px; font-weight: bold;"); l.addWidget(self.lbl_current)
        b = QPushButton("Select Folder"); b.setObjectName("PrimaryBtn"); b.clicked.connect(main_app.select_repo); l.addWidget(b)
        self.content_layout.addWidget(p); self.content_layout.addStretch()

class CommitPage(BasePage):
    def __init__(self, main_app):
        super().__init__("Commit", "Review and finalize", main_app)
        split = QHBoxLayout(); s_p = GlassPanel(); s_l = QVBoxLayout(s_p); s_l.addWidget(QLabel("Pending Files").setObjectName("SectionLabel"))
        self.file_list = QListWidget(); s_l.addWidget(self.file_list)
        b_s = QPushButton("Stage All"); b_s.clicked.connect(main_app.git_stage_all); s_l.addWidget(b_s); split.addWidget(s_p)
        c_p = GlassPanel(); c_l = QVBoxLayout(c_p); c_l.addWidget(QLabel("Message").setObjectName("SectionLabel"))
        self.txt_msg = QTextEdit(); c_l.addWidget(self.txt_msg)
        b_c = QPushButton("Commit"); b_c.setObjectName("PrimaryBtn"); b_c.clicked.connect(self.commit_manual); c_l.addWidget(b_c); split.addWidget(c_p)
        self.content_layout.addLayout(split)
    def commit_manual(self):
        m = self.txt_msg.toPlainText()
        if m: self.main.git_commit(m); self.txt_msg.clear()

class BranchesPage(BasePage):
    def __init__(self, main_app):
        super().__init__("Branches", "Local branch management", main_app)
        p = GlassPanel(); l = QVBoxLayout(p); l.addWidget(QLabel("Branches").setObjectName("SectionLabel"))
        self.branch_list = QListWidget(); l.addWidget(self.branch_list)
        b = QPushButton("New Branch"); b.setObjectName("PrimaryBtn"); b.clicked.connect(main_app.git_create_branch); l.addWidget(b)
        self.content_layout.addWidget(p); self.content_layout.addStretch()

class HistoryPage(BasePage):
    def __init__(self, main_app):
        super().__init__("History", "Commit timeline", main_app)
        p = GlassPanel(); l = QVBoxLayout(p); l.addWidget(QLabel("Recent Log").setObjectName("SectionLabel"))
        self.history_list = QListWidget(); self.history_list.setStyleSheet("font-family: monospace;"); l.addWidget(self.history_list)
        self.content_layout.addWidget(p)

class SettingsPage(BasePage):
    def __init__(self, main_app):
        super().__init__("Settings", "Configure preferences", main_app)
        p = GlassPanel(); l = QVBoxLayout(p); l.addWidget(QLabel("Microphone").setObjectName("SectionLabel"))
        self.combo_mic = QComboBox(); l.addWidget(self.combo_mic)
        l.addSpacing(20); l.addWidget(QLabel("AI Model").setObjectName("SectionLabel"))
        self.combo_model = QComboBox(); self.combo_model.addItems(["GPT-4", "GPT-3.5", "Local"]); l.addWidget(self.combo_model)
        self.content_layout.addWidget(p); self.content_layout.addStretch()

# ================== MAIN APP CLASS ==================

class GitEaseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RepoMate – AI Git Assistant")
        self.resize(1100, 800)
        self.git = GitManager(".")
        self.current_theme = "dark"
        self.current_plan_commands = None
        self.is_recording = False
        self.setStyleSheet(get_stylesheet(self.current_theme))
        l = QHBoxLayout(self); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(0)
        self.sidebar = ModernSidebar(self); l.addWidget(self.sidebar)
        r = QWidget(); rl = QVBoxLayout(r); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(0)
        self.header = ModernHeader(self); rl.addWidget(self.header)
        self.stack = QStackedWidget(); self.stack.setContentsMargins(24, 24, 24, 24)
        self.pages = {
            "Dashboard": DashboardPage(self), "Repositories": RepositoriesPage(self),
            "Commit": CommitPage(self), "Branches": BranchesPage(self),
            "History": HistoryPage(self), "Settings": SettingsPage(self)
        }
        for p in self.pages.values(): self.stack.addWidget(p)
        rl.addWidget(self.stack); l.addWidget(r)
        self.populate_mics(); self.switch_to_page("Dashboard")
        self.sidebar.nav_items[0].setProperty("active", True)
        self.timer = QTimer(); self.timer.timeout.connect(self.update_git_status); self.timer.start(5000); self.update_git_status()

    def on_nav_clicked(self):
        s = self.sender()
        if not s: return
        for b in self.sidebar.nav_items: b.setProperty("active", b == s); b.setStyle(b.style())
        self.switch_to_page(s.nav_name)

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.setStyleSheet(get_stylesheet(self.current_theme))
        self.header.btn_theme.setText("☀️" if self.current_theme == "dark" else "🌙")
        for p in self.pages.values():
            for w in p.findChildren(GlassPanel): w.update_glow(self.current_theme)

    def switch_to_page(self, name):
        if name in self.pages: self.stack.setCurrentWidget(self.pages[name])

    def log(self, msg):
        self.pages["Dashboard"].git_output.addItem(msg)
        self.pages["Dashboard"].git_output.scrollToBottom()

    def update_git_status(self):
        s = self.git.get_status(); dash = self.pages["Dashboard"]
        self.sidebar.pill_git.set_state(s['initialized'])
        self.sidebar.pill_git.setText("Git Connected" if s['initialized'] else "No Repo")
        dash.txt_repo_path.setText(self.git.repo_path)
        dash.card_branch.set_status(s['initialized'], s['current_branch'])
        dash.card_status.set_status(s['initialized'], f"{s['pending_changes']} Changes")
        try:
            o, _, _ = self.git.run_git(["log", "-1", "--format=%cr"])
            dash.card_last.set_status(s['initialized'], o if o else "No commits")
        except: dash.card_last.set_status(False, "Unknown")
        self.pages["Repositories"].lbl_current.setText(self.git.repo_path)
        cp = self.pages["Commit"]; cp.file_list.clear()
        for f in s['files']:
            it = QListWidgetItem(cp.file_list)
            w = FileRowWidget(f['name'], f['status'], f['color'])
            it.setSizeHint(w.sizeHint()); cp.file_list.setItemWidget(it, w)
        bp = self.pages["Branches"]; bp.branch_list.clear()
        for b in self.git.get_branches(): bp.branch_list.addItem(f"● {b}" + (" (Current)" if b == s['current_branch'] else ""))
        hp = self.pages["History"]; hp.history_list.clear()
        try:
            for l in self.git.run_command(["log", "--oneline", "-n", "10"]).splitlines(): hp.history_list.addItem(l)
        except: pass

    def populate_mics(self):
        c = self.pages["Settings"].combo_mic; c.clear()
        try:
            for i, d in enumerate(sd.query_devices()):
                if d['max_input_channels'] > 0: c.addItem(f"{i}: {d['name']}", i)
        except: pass

    def toggle_recording(self):
        dash = self.pages["Dashboard"]
        if self.is_recording:
            self.log("[INFO] Processing audio..."); dash.btn_mic.setEnabled(False); dash.waveform.set_active(False); dash.waveform.setVisible(False)
            self.recorder.stop(); self.is_recording = False
        else:
            idx = self.pages["Settings"].combo_mic.currentData()
            if idx is None: idx = sd.default.device[0]
            self.log("[INFO] Listening..."); dash.btn_mic.setStyleSheet("background-color: #f56565; color: white;")
            dash.waveform.setVisible(True); dash.waveform.set_active(True)
            self.recorder = AudioThread(device_index=idx); self.recorder.finished.connect(self.on_recording_finished); self.recorder.start()
            self.is_recording = True

    def on_recording_finished(self, text):
        dash = self.pages["Dashboard"]; dash.btn_mic.setEnabled(True); dash.btn_mic.setStyleSheet("")
        if text: dash.txt_command.setPlainText(text); self.log(f"[AUDIO] {text}"); self.plan_action()
        else: self.log("[WARN] No speech detected")

    def plan_action(self):
        dash = self.pages["Dashboard"]; inst = dash.txt_command.toPlainText()
        if not inst: self.log("[WARN] Enter instruction"); return
        self.log(f"[AI] Planning..."); dash.btn_plan.setEnabled(False)
        self.ai = AIWorker(inst); self.ai.finished.connect(self.on_plan_finished); self.ai.error.connect(self.on_plan_error); self.ai.start()

    def on_plan_finished(self, plan, cmds):
        dash = self.pages["Dashboard"]; dash.btn_plan.setEnabled(True); self.current_plan_commands = cmds
        dash.txt_plan_preview.setPlainText("\n".join(cmds)); dash.plan_card.setVisible(True); dash.commit_assist.setVisible(True)
        if plan and 'commit_message' in plan: dash.txt_commit_msg.setText(plan['commit_message'])
        self.log(f"[SUCCESS] Plan ready ({len(cmds)} steps)")

    def on_plan_error(self, m): self.pages["Dashboard"].btn_plan.setEnabled(True); self.log(f"[ERROR] {m}")

    def execute_plan(self):
        if not self.current_plan_commands: self.log("[WARN] No plan"); return
        dash = self.pages["Dashboard"]; dash.btn_confirm.setEnabled(False); dash.btn_confirm.setText("Executing...")
        self.worker = CommandWorker(self.git, self.current_plan_commands); self.worker.progress.connect(self.log)
        self.worker.finished.connect(self.on_exec_finished); self.worker.start()

    def on_exec_finished(self):
        dash = self.pages["Dashboard"]; dash.btn_confirm.setEnabled(True); dash.btn_confirm.setText("Confirm & Execute")
        dash.plan_card.setVisible(False); dash.commit_assist.setVisible(False); self.update_git_status(); self.log("[SUCCESS] Done")

    def generate_commit_ai(self):
        dash = self.pages["Dashboard"]; inst = dash.txt_command.toPlainText() or "current changes"
        self.log("[AI] Generating commit message..."); dash.txt_commit_msg.setPlaceholderText("Generating...")
        def run():
            try:
                p = planner.generate_plan(f"Suggest commit message: {inst}")
                msg = p.get('commit_message', "Update")
                dash.txt_commit_msg.setText(msg); self.log(f"[AI] Suggested: {msg}")
            except Exception as e: self.log(f"[ERROR] {e}")
        threading.Thread(target=run, daemon=True).start()

    def select_repo(self):
        p = QFileDialog.getExistingDirectory(self, "Select Repo")
        if p: self.git = GitManager(p); self.update_git_status(); self.log(f"[INFO] Path: {p}")

    def git_stage_all(self): self.git.run_command(["add", "."]); self.update_git_status()
    def git_commit(self, m): self.git.run_command(["commit", "-m", m]); self.update_git_status(); self.log(f"[SUCCESS] Committed")
    def git_create_branch(self):
        n, ok = QInputDialog.getText(self, "New Branch", "Name:")
        if ok and n: self.git.run_command(["checkout", "-b", n]); self.update_git_status()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyle("Fusion")
    window = GitEaseApp(); window.show(); sys.exit(app.exec_())
