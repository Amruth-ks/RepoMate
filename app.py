import sys
import os
import threading
import wave
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QListWidget, QListWidgetItem, QLineEdit, QScrollArea, QFrame,
    QGridLayout, QGraphicsDropShadowEffect, QSizePolicy, QPlainTextEdit, QComboBox,
    QStackedWidget, QInputDialog, QFileDialog, QStyle, QStyleOptionButton, QDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QPropertyAnimation, QEasingCurve, pyqtSlot, pyqtProperty, QPoint
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette, QLinearGradient, QBrush, QPainter, QPen, QRadialGradient, QPainterPath, QPixmap

# TTS import
try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False

# Local imports
try:
    from git_assist.main import processor, planner, validator
    from git_assist.git_manager import GitManager
except ImportError:
    # Fallback for testing environment if needed
    processor = None
    planner = None
    validator = None
    GitManager = None

# ================== THEMES & STYLES ==================

# THEMES = {
#     "dark": {
#         "bg": "#06080c", # Ultra dark for maximum contrast
#         "surface": "rgba(20, 30, 45, 220)",
#         "surface_hover": "rgba(40, 60, 90, 240)",
#         "card_bg": "rgba(10, 15, 25, 240)",
#         "border": "rgba(255, 255, 255, 0.15)",
#         "text_primary": "#FFFFFF", # Absolute white
#         "text_secondary": "#E2E8F0", # Bright slate for high legibility
#         "accent": "#00BAFF",
#         "accent_glow": "rgba(0, 186, 255, 0.3)",
#         "success": "#22C55E",
#         "error": "#EF4444",
#         "sidebar_bg": "#020617",
#         "input_bg": "rgba(2, 6, 23, 200)",
#         "glow": "0 8px 32px 0 rgba(0, 0, 0, 0.7)"
#     },
#     "light": {
#         "bg": "#e2e8f0", # Slightly darker slate for better card contrast
#         "surface": "#ffffff", 
#         "surface_hover": "#f1f5f9",
#         "card_bg": "#ffffff",
#         "border": "#94a3b8", # Darker border for clear separation
#         "text_primary": "#0f172a", # Deep navy
#         "text_secondary": "#334155", # High-contrast slate
#         "accent": "#0ea5e9",
#         "accent_glow": "rgba(14, 165, 233, 0.2)",
#         "success": "#15803d",
#         "error": "#b91c1c",
#         "sidebar_bg": "#f1f5f9",
#         "input_bg": "#ffffff",
#         "glow": "0 2px 10px rgba(0, 0, 0, 0.1)"
#     }
# }



THEMES = {
    "dark": {
        "bg": "#05060A",
        "surface": "rgba(16, 20, 30, 0.95)",
        "surface_hover": "rgba(26, 32, 46, 0.98)",
        "card_bg": "rgba(10, 12, 20, 0.98)",
        "border": "rgba(255, 255, 255, 0.10)",
        "text_primary": "#F9FAFB",
        "text_secondary": "#CBD5F5",
        "accent": "#22D3EE",
        "accent_glow": "rgba(34, 211, 238, 0.35)",
        "success": "#16A34A",
        "error": "#F97373",
        "sidebar_bg": "#030712",
        "input_bg": "rgba(8, 10, 18, 0.98)",
        "glow": "0 18px 45px rgba(0, 0, 0, 0.85)"
    },

    "light": {
        # VS Code Light+ Theme (Default)
        "bg": "#FFFFFF",              # Pure white background
        "surface": "#FFFFFF",         # Editor background
        "surface_hover": "#F3F4F6",   # Hover states
        "card_bg": "#FFFFFF",         # Panel background
        
        "border": "#E5E7EB",          # Editor group border
        
        "text_primary": "#1E1E1E",    # Pure black text
        "text_secondary": "#6B7280",  # Grey text (foreground)
        
        "accent": "#0E639C",          # VS Code blue accent
        "accent_glow": "rgba(14, 99, 156, 0.25)",
        
        "success": "#3FB950",         # Green for success
        "error": "#F85149",           # Red for errors
        
        "sidebar_bg": "#F8F9FA",      # Activity bar background
        "input_bg": "#FFFFFF",        # Input field background
        
        "glow": "0 2px 8px rgba(0, 0, 0, 0.12)"
    }
}







def get_stylesheet(theme_name="dark"):
    t = THEMES[theme_name]
    return f"""
    QWidget {{
        background-color: transparent;
        color: {t['text_primary']};
        font-family: 'Inter', 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
        font-size: 12pt;
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
        border-radius: 20px;
    }}
    
    QLabel#Title {{
        font-size: 12pt;
        font-weight: 800;
        color: {t['text_primary']};
        letter-spacing: -1px;
    }}
    
    QLabel#SectionLabel {{
        font-size: 12pt;
        font-weight: 800;
        color: {t['accent']};
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }}

    /* Premium Buttons */
    QPushButton {{
        background-color: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: 600;
        color: {t['text_primary']};
        font-size: 12pt;
    }}
    QPushButton:hover {{
        background-color: {t['surface_hover']};
        border: 1px solid {t['accent']};
    }}
    QPushButton:pressed {{
        background-color: {t['accent_glow']};
    }}
    
    QPushButton#PrimaryBtn {{
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {t['accent']}, stop:1 #0ea5e9);
        color: #ffffff;
        border: none;
        font-weight: 700;
        padding: 12px 24px;
        font-size: 12pt;
    }}
    QPushButton#PrimaryBtn:hover {{
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #7dd3fc, stop:1 #38bdf8);
    }}
    
    QPushButton#NavBtn {{
        text-align: left;
        padding: 14px 24px;
        border: none;
        border-radius: 14px;
        color: {t['text_secondary']};
        margin: 4px 0px;
        font-weight: 500;
        font-size: 12pt;
    }}
    QPushButton#NavBtn:hover {{
        background-color: {t['surface_hover']};
        color: {t['text_primary']};
    }}
    QPushButton#NavBtn[active="true"] {{
        background-color: {t['accent_glow']};
        color: {t['accent']};
        font-weight: 700;
        border-left: 4px solid {t['accent']};
    }}

    /* Premium Inputs */
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
        background-color: {t['input_bg']};
        border: 1px solid {t['border']};
        border-radius: 12px;
        padding: 12px;
        color: {t['text_primary']};
        font-size: 12pt;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {t['accent']};
    }}

    /* Scrollbar Styling */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['border']};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t['accent']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    QListWidget {{
        border-radius: 16px;
        background-color: {t['input_bg']};
        border: 1px solid {t['border']};
        font-size: 12pt;
    }}
    QListWidget::item {{
        padding: 10px;
        border-radius: 8px;
        margin: 2px 4px;
        font-size: 12pt;
    }}
    QListWidget::item:selected {{
        background-color: {t['accent_glow']};
        color: {t['accent']};
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
            text = recognizer.recognize_google(audio_data, show_all=False)
            # Optional: filter out very short or unlikely results
            if isinstance(text, str) and len(text.strip()) >= 2:
                self.finished.emit(text.strip())
            else:
                self.finished.emit("")
        except sr.UnknownValueError:
            self.finished.emit("")
        except sr.RequestError as e:
            self.finished.emit("")
        except Exception:
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
            print("processing")
            norm_text, _ = processor.normalize(self.text)
            plan = planner.generate_plan(norm_text)
            print("planning",plan)
            safe, msg = validator.validate(plan)
            print("validating",safe,msg)
            if not safe:
                self.error.emit(f"Unsafe Plan: {msg}")
                return
            commands = plan.get("commands") if isinstance(plan, dict) else None
            if not isinstance(commands, list) or not commands:
                raise ValueError("Planner did not return a valid 'commands' list")
            print("hello")
            print(commands)
            
            self.finished.emit(plan, commands)
        except Exception as e:
            self.error.emit(str(e))

class CommandWorker(QThread):
    progress = pyqtSignal(str)
    explanation = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, git_manager, commands):
        super().__init__()
        self.git = git_manager
        self.commands = commands

    def run(self):
        explanations = []
        try:
            for cmd in self.commands:
                # Execute once
                result = self.git.execute_commands([cmd])
                self.progress.emit(result[0] if result else "")
                # Generate simple explanation
                if cmd.strip().startswith("git add"):
                    explanations.append("Staged changes for commit.")
                elif cmd.strip().startswith("git commit"):
                    msg = cmd.split("-m")[-1].strip().strip('"\'') if "-m" in cmd else "Committed changes."
                    explanations.append(f"Committed with message: {msg}")
                elif cmd.strip().startswith("git push"):
                    if "--set-upstream" in cmd:
                        explanations.append("Pushed the new branch to the remote and set it as the upstream branch.")
                    else:
                        explanations.append("Pushed commits to the remote repository.")
                elif cmd.strip().startswith("git pull"):
                    explanations.append("Pulled latest changes from the remote repository.")
                elif cmd.strip().startswith("git branch"):
                    explanations.append("Created or listed branches.")
                elif cmd.strip().startswith("git checkout"):
                    explanations.append("Switched to a different branch.")
                elif cmd.strip().startswith("git merge"):
                    explanations.append("Merged changes from another branch.")
                elif cmd.strip().startswith("git status"):
                    explanations.append("Checked the repository status.")
                else:
                    explanations.append(f"Executed: {cmd}")
                # If push failed due to no upstream, retry with --set-upstream
                if result and result[0] and "no upstream branch" in result[0]:
                    # Get current branch name
                    try:
                        out, _, code = self.git.run_git(["branch", "--show-current"])
                        branch = out.strip() if code == 0 else None
                        if branch:
                            retry_cmd = f"git push --set-upstream origin {branch}"
                            retry_res = self.git.execute_commands([retry_cmd])
                            self.progress.emit(retry_res[0] if retry_res else "")
                            explanations.append("Pushed the new branch to the remote and set it as the upstream branch.")
                        else:
                            self.progress.emit("[ERROR] Could not determine current branch for upstream push")
                            explanations.append("Failed to push: could not determine current branch.")
                    except Exception as e:
                        self.progress.emit(f"[ERROR] Auto-upstream retry failed: {e}")
                        explanations.append(f"Auto-upstream retry failed: {e}")
            # Emit combined explanation
            self.explanation.emit("\n".join(explanations) if explanations else "No commands executed.")
        except Exception as e:
            self.progress.emit(f"[ERROR] {e}")
            self.explanation.emit(f"Error during execution: {e}")
        finally:
            self.finished.emit()

class GenericWorker(QThread):
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            res = self.func(*self.args, **self.kwargs)
            self.result.emit(res)
        except Exception as e:
            self.error.emit(str(e))

class GitStatusWorker(QThread):
    status_updated = pyqtSignal(dict)
    branches_updated = pyqtSignal(list)
    log_updated = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, git_manager):
        super().__init__()
        self.git = git_manager

    def run(self):
        try:
            status = self.git.get_status()
            
            # Get last commit time for the status card
            try:
                out, _, _ = self.git.run_git(["log", "-1", "--format=%cr"])
                status["last_commit"] = out if out else "No commits"
            except:
                status["last_commit"] = "Unknown"
                
            self.status_updated.emit(status)
            
            branches = self.git.get_branches()
            self.branches_updated.emit(branches)
            
            # Fetch recent log
            try:
                log = self.git.run_command(["log", "--oneline", "-n", "10"]).splitlines()
                self.log_updated.emit(log)
            except:
                self.log_updated.emit([])
                
        except Exception as e:
            self.error.emit(str(e))

# ================== CUSTOM WIDGETS ==================

class GlassPanel(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setObjectName("GlassPanel")
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(30)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(4)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(self.shadow)
        
    def update_glow(self, theme_name):
        t = THEMES[theme_name]
        # Multi-layered glow for premium feel
        color = QColor(0, 0, 0, 80) if theme_name == "dark" else QColor(0, 0, 0, 30)
        self.shadow.setColor(color)

class ShimmerWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._pos = -1.0
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(1500)
        self.anim.setStartValue(-1.0)
        self.anim.setEndValue(2.0)
        self.anim.setLoopCount(-1)
        self.anim.start()

    @pyqtProperty(float)
    def pos(self): return self._pos
    @pos.setter
    def pos(self, value):
        self._pos = value
        self.update()

    def paintEvent(self, event):
        if not self.isVisible(): return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(self.width() * self._pos, 0, self.width() * (self._pos + 0.5), 0)
        c = QColor(255, 255, 255, 0)
        m = QColor(255, 255, 255, 40)
        grad.setColorAt(0, c)
        grad.setColorAt(0.5, m)
        grad.setColorAt(1, c)
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

class StatusCard(GlassPanel):
    def __init__(self, title, icon_char):
        super(StatusCard, self).__init__()
        self.setMinimumHeight(120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_icon = QLabel(icon_char)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet("font-size: 28px; color: #38bdf8;")
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setObjectName("SectionLabel")
        
        self.lbl_value = QLabel("...")
        self.lbl_value.setAlignment(Qt.AlignCenter)
        self.lbl_value.setStyleSheet("font-size: 15px; font-weight: 600;")
        
        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        
        self.shimmer = ShimmerWidget(self)
        self.shimmer.hide()

    def resizeEvent(self, event):
        self.shimmer.setFixedSize(self.size())
        super().resizeEvent(event)

    def set_status(self, is_good, text):
        self.shimmer.hide()
        if self.lbl_value.text() != text:
            # Pop animation on change
            self._pop_anim()
        self.lbl_value.setText(text)
        t = THEMES["dark"]
        color = t['success'] if is_good else t['text_secondary']
        self.lbl_value.setStyleSheet(f"color: {color};")

    def _pop_anim(self):
        self.p_anim = QPropertyAnimation(self.lbl_icon, b"geometry")
        self.p_anim.setDuration(300)
        curr = self.lbl_icon.geometry()
        self.p_anim.setStartValue(curr.adjusted(-2, -2, 2, 2))
        self.p_anim.setEndValue(curr)
        self.p_anim.setEasingCurve(QEasingCurve.OutElastic)
        self.p_anim.start()

    def show_loading(self):
        self.lbl_value.setText("")
        self.shimmer.show()
        self.shimmer.raise_()

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

class GradientLabel(QLabel):
    def __init__(self, text, parent=None):
        super(GradientLabel, self).__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self._glow = 0
        self.anim = QPropertyAnimation(self, b"glow")
        self.anim.setDuration(2000)
        self.anim.setStartValue(0)
        self.anim.setEndValue(100)
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1)
        self.anim.start()

    @pyqtProperty(int)
    def glow(self): return self._glow
    @glow.setter
    def glow(self, value):
        self._glow = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor("#38bdf8")) # Light blue
        grad.setColorAt(1, QColor("#818cf8")) # Indigo
        
        f = self.font()
        f.setBold(True)
        painter.setFont(f)
        
        # Draw gradient text using QPen with gradient brush
        pen = QPen()
        pen.setBrush(grad)
        painter.setPen(pen)
        
        # Center text vertically and horizontally
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

class PremiumButton(QPushButton):
    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self._scale = 1.0
        self._flash_alpha = 0
        self._hover_pos = QPoint(-100, -100)
        self.anim = QPropertyAnimation(self, b"scale")
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.OutBack)
        
        self.flash_anim = QPropertyAnimation(self, b"flash_alpha")
        self.flash_anim.setDuration(400)
        self.flash_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.setMouseTracking(True)

    @pyqtProperty(float)
    def scale(self): return self._scale
    @scale.setter
    def scale(self, value):
        self._scale = value
        self.update()

    @pyqtProperty(int)
    def flash_alpha(self): return self._flash_alpha
    @flash_alpha.setter
    def flash_alpha(self, value):
        self._flash_alpha = value
        self.update()

    def trigger_success(self):
        self.flash_anim.stop()
        self.flash_anim.setStartValue(180)
        self.flash_anim.setEndValue(0)
        self.flash_anim.start()

    def mousePressEvent(self, event):
        self.anim.stop()
        self.anim.setDuration(50)
        self.anim.setEndValue(0.95)
        self.anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.anim.stop()
        self.anim.setDuration(150)
        self.anim.setEndValue(1.05 if self.underMouse() else 1.0)
        self.anim.start()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self._scale)
        self.anim.setEndValue(1.05)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self._scale)
        self.anim.setEndValue(1.0)
        self.anim.start()
        self._hover_pos = QPoint(-100, -100)
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        self._hover_pos = event.pos()
        self.update()
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Apply scale transform BEFORE super().paintEvent
        if self._scale != 1.0:
            painter.translate(self.width()/2, self.height()/2)
            painter.scale(self._scale, self._scale)
            painter.translate(-self.width()/2, -self.height()/2)
            
        # Draw base button (QPushButton won't know we scaled, but painter carries transform)
        # However, super().paintEvent creates its own painter or uses the widget's?
        # Actually in Qt, super().paintEvent draws directly. 
        # But we want to scale everything.
        
        # Proper way: Render to a temporary buffer or use a QGraphicsEffect.
        # But for simple scale, we can use the transform on the shared painter IF it's shared.
        # In PyQt QPushButton, super().paintEvent(event) ignores the transform we just did!
        
        # Let's draw the background and content manually for perfect control
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        
        if self._scale != 1.0:
            painter.save()
            painter.translate(self.width()/2, self.height()/2)
            painter.scale(self._scale, self._scale)
            painter.translate(-self.width()/2, -self.height()/2)
            self.style().drawControl(QStyle.CE_PushButton, opt, painter, self)
            painter.restore()
        else:
            self.style().drawControl(QStyle.CE_PushButton, opt, painter, self)
        
        # Draw spotlight effect ON TOP
        if self.underMouse():
            grad = QRadialGradient(self._hover_pos, 90)
            grad.setColorAt(0, QColor(255, 255, 255, 50)) # More visible
            grad.setColorAt(1, Qt.transparent)
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect(), 12, 12)

        # Draw success flash
        if self._flash_alpha > 0:
            painter.setBrush(QColor(72, 187, 120, self._flash_alpha)) # Green flash
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect(), 12, 12)

class PulsingButton(PremiumButton):
    def __init__(self, *args, **kwargs):
        PremiumButton.__init__(self, *args, **kwargs)
        self._glow_alpha = 0
        self.pulse_anim = QPropertyAnimation(self, b"glow_alpha")
        self.pulse_anim.setDuration(1200)
        self.pulse_anim.setStartValue(0)
        self.pulse_anim.setEndValue(80)
        self.pulse_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.pulse_anim.setLoopCount(-1)
        self.pulse_anim.start()

    @pyqtProperty(int)
    def glow_alpha(self): return self._glow_alpha
    @glow_alpha.setter
    def glow_alpha(self, value):
        self._glow_alpha = value
        self.update()

    def paintEvent(self, event):
        # Always draw pulse for mic button (objectName check)
        is_mic = self.text() == "🎤"
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if (self.objectName() == "PrimaryBtn" or is_mic) and not self.underMouse():
            t = THEMES["dark"]
            color = QColor(t['accent'])
            color.setAlpha(self._glow_alpha)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(color, 2))
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
        super().paintEvent(event)

class NavItem(PremiumButton):
    def __init__(self, text, icon_char, parent=None):
        super(NavItem, self).__init__(parent)
        self.setObjectName("NavBtn")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(56)
        self.setText(f"{icon_char}   {text}")
        self.nav_name = text

class StatusPill(QLabel):
    def __init__(self, text, active=True, parent=None):
        QLabel.__init__(self, text, parent)
        self.set_state(active)
        self.setFixedSize(140, 32)
        self.setAlignment(Qt.AlignCenter)

    def set_state(self, active):
        t = THEMES["dark"]
        color = t['success'] if active else t['error']
        bg = f"rgba({QColor(color).red()}, {QColor(color).green()}, {QColor(color).blue()}, 30)"
        self.setStyleSheet(f"background-color: {bg}; color: {color}; border: 1px solid {color}; border-radius: 14px; font-size: 11px; font-weight: bold;")
    





class ModernHeader(QFrame):
    def __init__(self, main_app):
        super(ModernHeader, self).__init__()
        self.main = main_app # Store this
        self.setObjectName("HeaderBar")
        self.setFixedHeight(70)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        logo_lbl = QLabel()
        logo_pix = QPixmap("logo.png")
        if not logo_pix.isNull():
            logo_lbl.setPixmap(logo_pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_lbl.setText("󰊤")
            logo_lbl.setStyleSheet("font-size: 28px; color: #38bdf8;")
        
        self.title_label = GradientLabel("REPOMATE")
        self.title_label.setFont(QFont("Inter", 28, QFont.ExtraBold))
        self.title_label.setFixedWidth(260)
        
        if logo_lbl: layout.addWidget(logo_lbl)
        if hasattr(self, 'title_label'): layout.addWidget(self.title_label)
        layout.addStretch()
        
        self.btn_theme = PremiumButton("☀️" if main_app.current_theme == "dark" else "🌙")
        self.btn_theme.setFixedSize(50, 50)  # Larger button
        self.btn_theme.setToolTip("Toggle theme")
        self.btn_theme.clicked.connect(main_app.toggle_theme)
        layout.addWidget(self.btn_theme)
        btn_sett = PremiumButton("⚙️")
        btn_sett.setFixedSize(50, 50)  # Larger button
        btn_sett.setToolTip("Settings")
        btn_sett.clicked.connect(lambda: main_app.switch_to_page("Settings"))
        layout.addWidget(btn_sett)

class NavItem(QPushButton):
    def __init__(self, text, icon_name):
        super().__init__(text)
        self.nav_name = text  # Add nav_name attribute

        import qtawesome as qta

        self.setIcon(qta.icon(icon_name, color="#9CA3AF"))
        self.setIconSize(QSize(18,18))

        self.setObjectName("NavItem")
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet("""
        QPushButton#NavItem{
            text-align:left;
            padding:12px;
            border-radius:8px;
        }
        """)

class ModernSidebar(QFrame):
    def __init__(self, main_app):
        super(ModernSidebar, self).__init__(main_app)
        self.setObjectName("Sidebar")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setMaximumWidth(280)
        self.setMinimumWidth(200)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 30, 15, 30)
        layout.setSpacing(8)
        self.nav_items = []
        import qtawesome as qta

        nav_config = [
    ("Dashboard", "fa5s.tachometer-alt"),
    ("Repositories", "fa5s.folder"),
    ("Commit", "fa5s.check"),
    ("Branches", "fa5s.code-branch"),
    ("History", "fa5s.history"),
    ("Settings", "fa5s.cog"),
    ("About", "fa5s.info-circle"),
    ("Tutorial", "fa5s.graduation-cap")
]
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
        super(FileRowWidget, self).__init__()
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
    def __init__(self, name, subtitle, main_app):
        super(BasePage, self).__init__()
        self.main = main_app
        self.setObjectName(name)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Header
        header_container = QWidget()
        header_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(24, 24, 24, 12)
        header_layout.setSpacing(8)
        title = QLabel(name)
        title.setFont(QFont("Inter", 28, QFont.Bold))
        title.setStyleSheet("color: #38bdf8;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont("Inter", 14))
        subtitle_label.setStyleSheet("color: #64748b;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_container)
        layout.addSpacing(12)
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(16, 0, 16, 16)
        self.content_layout.setSpacing(16)
        layout.addLayout(self.content_layout)
        layout.addStretch()

class DashboardPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "Dashboard", "Welcome to REPOMATE – AI Git Assistant", main_app)
        # Main two-column grid
        grid = QHBoxLayout(); grid.setSpacing(16)
        grid.setContentsMargins(8, 8, 8, 8)
        left = QVBoxLayout(); left.setSpacing(16)
        # Real-time Status (same width as AI Command)
        top_p = GlassPanel(); top_lay = QVBoxLayout(top_p)
        _lbl_real_time_status = QLabel("Real-time Status")
        _lbl_real_time_status.setObjectName("SectionLabel")
        top_lay.addWidget(_lbl_real_time_status)
        cards_row = QHBoxLayout()
        self.card_branch = StatusCard("Active Branch", "󰘬"); self.card_status = StatusCard("Working Tree", "󱇬"); self.card_last = StatusCard("Latest Activity", "🕒")
        cards_row.addWidget(self.card_branch)
        cards_row.addWidget(self.card_status)
        cards_row.addWidget(self.card_last)
        cards_row.addStretch()
        top_lay.addLayout(cards_row)
        left.addWidget(top_p)
        # Repository Path panel
        repo_p = GlassPanel(); repo_lay = QVBoxLayout(repo_p)
        _lbl_repo_path = QLabel("Repository Path")
        _lbl_repo_path.setObjectName("SectionLabel")
        repo_lay.addWidget(_lbl_repo_path)
        row = QHBoxLayout()
        self.txt_repo_path = QLineEdit(); self.txt_repo_path.setReadOnly(True)
        btn_br = PremiumButton("Browse")
        # Add folder icon
        import qtawesome as qta
        btn_br.setIcon(qta.icon("fa5s.folder-open", color="#9CA3AF"))
        btn_br.setIconSize(QSize(16, 16))
        btn_br.clicked.connect(main_app.select_repo)
        row.addWidget(self.txt_repo_path); row.addWidget(btn_br)
        repo_lay.addLayout(row)
        left.addWidget(repo_p)
        # AI Command panel
        cmd_p = GlassPanel(); cmd_lay = QVBoxLayout(cmd_p)
        _lbl_ai_command = QLabel("AI Command")
        _lbl_ai_command.setObjectName("SectionLabel")
        cmd_lay.addWidget(_lbl_ai_command)
        self.txt_command = QTextEdit(); self.txt_command.setPlaceholderText("Enter command...")
        self.txt_command.setMaximumHeight(120)
        cmd_lay.addWidget(self.txt_command)
        ctrl = QHBoxLayout()
        self.btn_mic = PulsingButton("🎤")
        self.btn_mic.setToolTip("Voice command")
        self.btn_mic.clicked.connect(main_app.toggle_recording)

        self.btn_mic.setFixedSize(60, 60)

        self.btn_mic.setStyleSheet("""
        QPushButton{
            background-color:#25D366;
            border-radius:30px;
            color:white;
            font-size:22px;
        }
        QPushButton:hover{
            background-color:#20b858;
        }
        QPushButton:pressed{
            background-color:#1da851;
        }
        """)

        ctrl.addWidget(self.btn_mic)
        self.btn_plan = PulsingButton("Generate Plan")
        # Add magic wand icon for Generate Plan
        self.btn_plan.setIcon(qta.icon("fa5s.magic", color="#FFFFFF"))
        self.btn_plan.setIconSize(QSize(16, 16))
        self.btn_plan.setObjectName("PrimaryBtn"); self.btn_plan.clicked.connect(main_app.plan_action)
        ctrl.addWidget(self.btn_mic); ctrl.addWidget(self.btn_plan)
        cmd_lay.addLayout(ctrl)
        left.addWidget(cmd_p)
        self.waveform = WaveformWidget(main_app); self.waveform.setVisible(False); left.addWidget(self.waveform)
        self.plan_card = GlassPanel(); self.plan_card.setVisible(False); plan_lay = QVBoxLayout(self.plan_card)
        _lbl_suggested_plan = QLabel("Suggested Plan")
        _lbl_suggested_plan.setObjectName("SectionLabel")
        plan_lay.addWidget(_lbl_suggested_plan)
        self.txt_plan_preview = QPlainTextEdit(); self.txt_plan_preview.setReadOnly(True); self.txt_plan_preview.setStyleSheet("font-family: monospace;")
        self.txt_plan_preview.setMaximumHeight(200)
        plan_lay.addWidget(self.txt_plan_preview)
        self.btn_confirm = PulsingButton("Confirm & Execute")
        # Add play/rocket icon for Execute
        self.btn_confirm.setIcon(qta.icon("fa5s.rocket", color="#FFFFFF"))
        self.btn_confirm.setIconSize(QSize(16, 16))
        self.btn_confirm.setObjectName("PrimaryBtn"); self.btn_confirm.clicked.connect(main_app.execute_plan)
        plan_lay.addWidget(self.btn_confirm)
        left.addWidget(self.plan_card)
        self.commit_assist = GlassPanel(); self.commit_assist.setVisible(False); ca_lay = QVBoxLayout(self.commit_assist)
        _lbl_commit_message = QLabel("Commit Message")
        _lbl_commit_message.setObjectName("SectionLabel")
        ca_lay.addWidget(_lbl_commit_message)
        c_row = QHBoxLayout(); self.txt_commit_msg = QLineEdit(); 
        btn_ai = PremiumButton("AI Gen")
        # Add brain/lightbulb icon for AI Gen
        btn_ai.setIcon(qta.icon("fa5s.lightbulb", color="#9CA3AF"))
        btn_ai.setIconSize(QSize(16, 16))
        btn_ai.clicked.connect(main_app.generate_commit_ai)
        c_row.addWidget(self.txt_commit_msg); c_row.addWidget(btn_ai)
        ca_lay.addLayout(c_row); left.addWidget(self.commit_assist); left.addStretch()
        # Right column: Git Output at top, then CLI Output, Explanation
        right = QVBoxLayout(); right.setSpacing(16)
        # Git Output (top)
        out_p = GlassPanel(); out_lay = QVBoxLayout(out_p)
        _lbl_git_output = QLabel("Git Output")
        _lbl_git_output.setObjectName("SectionLabel")
        out_lay.addWidget(_lbl_git_output)
        self.git_output = QListWidget(); self.git_output.setMaximumHeight(120); out_lay.addWidget(self.git_output); right.addWidget(out_p)
        # CLI Output
        cli_p = GlassPanel(); cli_lay = QVBoxLayout(cli_p)
        _lbl_cli_output = QLabel("CLI Output")
        _lbl_cli_output.setObjectName("SectionLabel")
        cli_lay.addWidget(_lbl_cli_output)
        self.cli_output = QPlainTextEdit()
        self.cli_output.setReadOnly(True)
        self.cli_output.setStyleSheet("font-family: monospace;")
        self.cli_output.setMaximumHeight(180)
        cli_lay.addWidget(self.cli_output)
        right.addWidget(cli_p)
        # Explanation
        exp_p = GlassPanel(); exp_lay = QVBoxLayout(exp_p)
        _lbl_explanation = QLabel("Explanation")
        _lbl_explanation.setObjectName("SectionLabel")
        exp_lay.addWidget(_lbl_explanation)
        exp_row = QHBoxLayout()
        self.btn_speak_explanation = PremiumButton(" Speak")
        # Add volume-up icon for Speak
        self.btn_speak_explanation.setIcon(qta.icon("fa5s.volume-up", color="#9CA3AF"))
        self.btn_speak_explanation.setIconSize(QSize(16, 16))
        self.btn_speak_explanation.clicked.connect(self.speak_explanation)
        exp_row.addWidget(self.btn_speak_explanation)
        exp_row.addStretch()
        exp_lay.addLayout(exp_row)
        self.cli_explanation = QLabel("No commands executed yet.")
        self.cli_explanation.setWordWrap(True)
        self.cli_explanation.setStyleSheet("color: #ccc; font-size: 13px; padding: 8px; background: rgba(255,255,255,5); border-radius: 4px;")
        exp_lay.addWidget(self.cli_explanation)
        right.addWidget(exp_p)
        right.addStretch()
        grid.addLayout(left, 3)
        grid.addLayout(right, 2)
        self.content_layout.addLayout(grid)

    def speak_explanation(self):
        """Speak the current explanation text using TTS if available."""
        if not TTS_AVAILABLE:
            self.main.log("[WARN] TTS not available (pyttsx3 not installed)")
            return
        text = self.cli_explanation.text().strip()
        if not text or text == "No commands executed yet.":
            self.main.log("[WARN] No explanation to speak")
            return
        try:
            engine = pyttsx3.init()
            # Configure for clear, pleasant female voice
            voices = engine.getProperty('voices')
            # Prioritize high-quality female voices
            preferred_order = []
            for voice in voices:
                name = voice.name.lower()
                if 'zira' in name:
                    preferred_order.insert(0, voice)  # Zira (Windows) is high quality
                elif 'susan' in name or 'karen' in name:
                    preferred_order.append(voice)  # Other common female voices
                elif 'female' in name:
                    preferred_order.append(voice)
            # Try preferred voices first, then any female, then fallback
            selected_voice = None
            for voice in preferred_order:
                selected_voice = voice
                break
            if not selected_voice:
                for voice in voices:
                    if 'female' in voice.name.lower():
                        selected_voice = voice
                        break
            if not selected_voice and voices:
                selected_voice = voices[0]
            if selected_voice:
                engine.setProperty('voice', selected_voice.id)
            # Optimize for clarity and natural tone
            engine.setProperty('rate', 160)  # Slightly slower for clarity
            engine.setProperty('volume', 0.85)  # Comfortable volume
            # Some engines support pitch; try to set a slightly higher pitch for female tone
            try:
                engine.setProperty('pitch', 110)  # Slightly higher pitch
            except:
                pass  # Not all engines support pitch
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            self.main.log(f"[ERROR] TTS failed: {e}")

class RepositoriesPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "Repositories", "Manage workspace", main_app)
        p = GlassPanel(); l = QVBoxLayout(p)
        _lbl_active_repo = QLabel("Active Repo")
        _lbl_active_repo.setObjectName("SectionLabel")
        l.addWidget(_lbl_active_repo)
        self.lbl_current = QLabel("None"); self.lbl_current.setStyleSheet("font-size: 16px; font-weight: bold;"); l.addWidget(self.lbl_current)
        b = PulsingButton("Select Folder"); b.setObjectName("PrimaryBtn"); b.clicked.connect(main_app.select_repo); l.addWidget(b)
        self.content_layout.addWidget(p)
        
        # GitHub Search Section
        gh_p = GlassPanel(); gh_l = QVBoxLayout(gh_p)
        _lbl_github_repos = QLabel("GitHub Repositories")
        _lbl_github_repos.setObjectName("SectionLabel")
        gh_l.addWidget(_lbl_github_repos)
        
        search_row = QHBoxLayout()
        self.txt_gh_search = QLineEdit(); self.txt_gh_search.setPlaceholderText("Search GitHub or leave empty for your repos...")
        btn_gh_fetch = PremiumButton("Fetch"); btn_gh_fetch.clicked.connect(self.fetch_github_repos)
        search_row.addWidget(self.txt_gh_search); search_row.addWidget(btn_gh_fetch)
        gh_l.addLayout(search_row)
        
        self.gh_list = QListWidget(); self.gh_list.setFixedHeight(250)
        gh_l.addWidget(self.gh_list)
        
        btn_clone = PulsingButton("Clone Selected"); btn_clone.setObjectName("PrimaryBtn"); btn_clone.clicked.connect(self.clone_selected)
        gh_l.addWidget(btn_clone)
        
        self.content_layout.addWidget(gh_p)
        self.content_layout.addStretch()

    def fetch_github_repos(self):
        query = self.txt_gh_search.text()
        self.gh_list.clear()
        self.main.log("[INFO] Fetching GitHub repositories...")
        
        def run():
            try:
                if query:
                    repos = self.main.git.github.search_repos(query)
                else:
                    repos = self.main.git.github.get_user_repos()
                return repos
            except Exception as e:
                raise e

        self.worker = GenericWorker(run)
        self.worker.result.connect(self.on_repos_fetched)
        self.worker.error.connect(lambda e: self.main.log(f"[ERROR] {e}"))
        self.worker.start()

    def on_repos_fetched(self, repos):
        self.gh_list.clear()
        allowed = []
        for r in repos:
            owner = (r.get("owner") or {}).get("login")
            if not self.main.is_owner_allowed(owner):
                continue
            allowed.append(r)

        for r in allowed:
            it = QListWidgetItem(f"{r['full_name']} (Stars: {r['stargazers_count']})")
            it.setData(Qt.UserRole, r.get('clone_url'))
            self.gh_list.addItem(it)
        self.main.log(f"[SUCCESS] Loaded {len(allowed)} repositories")

    def clone_selected(self):
        it = self.gh_list.currentItem()
        if not it:
            self.main.log("[WARN] Select a repo to clone")
            return
        
        url = it.data(Qt.UserRole)
        if not self.main.is_remote_allowed(url):
            self.main.log("[ERROR] Clone blocked: repo is not owned by the connected GitHub account")
            return
        name = it.text().split(" (")[0].split("/")[-1]
        
        path = QFileDialog.getExistingDirectory(self, "Select Parent Directory for Clone")
        if not path: return
        
        target = os.path.join(path, name)
        self.main.log(f"[INFO] Cloning {url} to {target}...")
        
        self.worker = GenericWorker(self.main.git.clone, url, target)
        self.worker.result.connect(self.on_clone_finished)
        self.worker.error.connect(lambda e: self.main.log(f"[ERROR] {e}"))
        self.worker.start()

    def on_clone_finished(self, res):
        success, msg = res
        if success:
            self.main.log(f"[SUCCESS] {msg}")
            self.main.update_git_status()
        else:
            self.main.log(f"[ERROR] {msg}")

class CommitLogItem(QWidget):
    def __init__(self, commit_hash, author, date, message, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        # Avatar placeholder (circle with initials)
        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        initials = (author.split()[0][0] + author.split()[-1][0]).upper() if author and " " in author else (author[:2].upper() if author else "??")
        avatar.setStyleSheet(f"""
            background-color: #38bdf8;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        """)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setText(initials)
        layout.addWidget(avatar)
        # Commit details
        details = QVBoxLayout()
        details.setSpacing(2)
        # Hash and date row
        meta = QHBoxLayout()
        hash_label = QLabel(commit_hash[:7])
        hash_label.setStyleSheet("color: #38bdf8; font-family: monospace; font-size: 14px;")
        hash_label.setFixedWidth(60)
        date_label = QLabel(date)
        date_label.setStyleSheet("color: #64748b; font-size: 13px;")
        date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        meta.addWidget(hash_label)
        meta.addStretch()
        meta.addWidget(date_label)
        details.addLayout(meta)
        # Author
        author_label = QLabel(author)
        author_label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        details.addWidget(author_label)
        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: #e2e8f0; font-size: 15px; font-weight: 500;")
        details.addWidget(msg_label)
        
        # Store original stylesheet for theme switching
        self.msg_label = msg_label
        self.original_msg_style = "color: #e2e8f0; font-size: 15px; font-weight: 500;"
        self.light_msg_style = "color: #000000; font-size: 15px; font-weight: 500;"
        layout.addLayout(details)
        layout.addStretch()
        # Hover effect
        self.setStyleSheet("""
            CommitLogItem {
                background-color: rgba(255,255,255,5);
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,10);
            }
            CommitLogItem:hover {
                background-color: rgba(255,255,255,8);
                border: 1px solid rgba(56,189,248,30);
            }
        """)

class BranchSwitchDialog(QDialog):
    def __init__(self, branches, current, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Switch Branch")
        self.setFixedSize(400, 320)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e293b;
                color: #e2e8f0;
                border-radius: 12px;
            }
            QLabel {
                color: #38bdf8;
                font-size: 14px;
                font-weight: bold;
            }
            QListWidget {
                background-color: #334155;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                color: #e2e8f0;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #38bdf8;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #475569;
            }
            QPushButton {
                background-color: #38bdf8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0ea5e9;
            }
            QPushButton:pressed {
                background-color: #0284c7;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        label = QLabel("Select branch:")
        layout.addWidget(label)
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SingleSelection)
        self.list.addItems(branches)
        # Highlight current branch
        for i in range(self.list.count()):
            if self.list.item(i).text() == current:
                self.list.setCurrentRow(i)
                break
        layout.addWidget(self.list)
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Switch")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_ok.setDefault(True)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def selected_branch(self):
        items = self.list.selectedItems()
        branch = items[0].text() if items else None
        print(f"[DEBUG Dialog] selected_branch -> {branch}")
        return branch

class CommitPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "Commit Log", "Repository history", main_app)
        # Remove bottom margin from BasePage content layout
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        # Branch info bar (display only)
        branch_panel = GlassPanel()
        branch_layout = QHBoxLayout(branch_panel)
        branch_layout.setContentsMargins(20, 16, 20, 16)
        self.lbl_branch_icon = QLabel("🌳")
        self.lbl_branch_icon.setStyleSheet("font-size: 16px;")
        branch_layout.addWidget(self.lbl_branch_icon)
        self.lbl_branch_name = QLabel("Loading branch...")
        self.lbl_branch_name.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 14px;")
        branch_layout.addWidget(self.lbl_branch_name)
        branch_layout.addStretch()
        self.content_layout.addWidget(branch_panel)
        # Controls bar (refresh and count)
        controls = GlassPanel()
        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(20, 16, 20, 16)
        self.btn_refresh = PremiumButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.load_log)
        ctrl_layout.addWidget(self.btn_refresh)
        ctrl_layout.addStretch()
        self.lbl_count = QLabel("Loading...")
        self.lbl_count.setStyleSheet("color: #94a3b8; font-size: 13px;")
        ctrl_layout.addWidget(self.lbl_count)
        self.content_layout.addWidget(controls)

        self.log_widget = QWidget()
        self.log_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.log_layout = QVBoxLayout(self.log_widget)
        self.log_layout.setContentsMargins(32, 16, 32, 16)
        self.log_layout.setSpacing(8)

        self.log_layout.addStretch()

        self.content_layout.addWidget(self.log_widget, 1)

        # Load branch and log
        self.load_branch()
        self.load_log()

    def load_branch(self):
        if not self.main.git:
            self.lbl_branch_name.setText("No repo")
            return
        try:
            out, _, code = self.main.git.run_git(["rev-parse", "--abbrev-ref", "HEAD"])
            if code == 0:
                branch = out.strip()
                self.lbl_branch_name.setText(branch)
            else:
                self.lbl_branch_name.setText("Unknown")
        except Exception:
            self.lbl_branch_name.setText("Error")

    def load_log(self):
        if not self.main.git:
            self.lbl_count.setText("No repo")
            return
        self.lbl_count.setText("Loading...")
        # Clear existing items (keep stretch at bottom)
        for i in reversed(range(self.log_layout.count() - 1)):
            child = self.log_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        # Fetch log in background
        def run():
            try:
                out, _, code = self.main.git.run_git(["log", "--oneline", "--pretty=format:%H|%an|%ad|%s", "--date=short", "-100"])
                if code != 0:
                    return []
                lines = out.strip().splitlines()
                commits = []
                for line in lines:
                    parts = line.split("|", 3)
                    if len(parts) == 4:
                        commits.append(parts)
                return commits
            except Exception as e:
                raise e
        self.worker = GenericWorker(run)
        self.worker.result.connect(self.on_log_loaded)
        self.worker.error.connect(lambda e: self.main.log(f"[ERROR] {e}"))
        self.worker.start()

    def on_log_loaded(self, commits):
        self.lbl_count.setText(f"{len(commits)} commits")
        # Insert commits before the bottom stretch
        for i, (h, author, date, msg) in enumerate(commits):
            item = CommitLogItem(h, author, date, msg)
            self.log_layout.addWidget(item)

class BranchesPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "Branches", "Local branch management", main_app)
        p = GlassPanel(); l = QVBoxLayout(p)
        _lbl_branches = QLabel("Branches")
        _lbl_branches.setObjectName("SectionLabel")
        l.addWidget(_lbl_branches)
        self.branch_list = QListWidget(); l.addWidget(self.branch_list)
        b = PremiumButton("New Branch"); b.setObjectName("PrimaryBtn"); b.clicked.connect(main_app.git_create_branch); l.addWidget(b)
        self.content_layout.addWidget(p); self.content_layout.addStretch()

class HistoryPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "History", "Commit timeline", main_app)
        p = GlassPanel(); l = QVBoxLayout(p)
        _lbl_recent_log = QLabel("Recent Log")
        _lbl_recent_log.setObjectName("SectionLabel")
        l.addWidget(_lbl_recent_log)
        self.history_list = QListWidget(); self.history_list.setStyleSheet("font-family: monospace;"); l.addWidget(self.history_list)
        self.content_layout.addWidget(p)

class SettingsPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "Settings", "Configure preferences", main_app)
        p = GlassPanel(); l = QVBoxLayout(p)
        _lbl_microphone = QLabel("Microphone")
        _lbl_microphone.setObjectName("SectionLabel")
        l.addWidget(_lbl_microphone)
        self.combo_mic = QComboBox(); l.addWidget(self.combo_mic)
        l.addSpacing(20)
        _lbl_ai_model = QLabel("AI Model")
        _lbl_ai_model.setObjectName("SectionLabel")
        l.addWidget(_lbl_ai_model)
        self.combo_model = QComboBox(); self.combo_model.addItems(["GPT-4", "GPT-3.5", "Local"]); l.addWidget(self.combo_model)

        l.addSpacing(20)
        _lbl_github = QLabel("GitHub")
        _lbl_github.setObjectName("SectionLabel")
        l.addWidget(_lbl_github)
        self.txt_gh_token = QLineEdit()
        self.txt_gh_token.setEchoMode(QLineEdit.Password)
        self.txt_gh_token.setPlaceholderText("GitHub Token (PAT)")
        l.addWidget(self.txt_gh_token)
        row = QHBoxLayout()
        self.btn_gh_connect = PremiumButton("Connect")
        self.btn_gh_connect.clicked.connect(lambda: main_app.connect_github_account(self.txt_gh_token.text()))
        self.lbl_gh_user = QLabel("Not connected")
        row.addWidget(self.btn_gh_connect)
        row.addWidget(self.lbl_gh_user)
        l.addLayout(row)
        l.addSpacing(20)
        _lbl_git_user = QLabel("Git User")
        _lbl_git_user.setObjectName("SectionLabel")
        l.addWidget(_lbl_git_user)
        self.lbl_current_git_user = QLabel("Current: Not set")
        self.lbl_current_git_user.setWordWrap(True)
        self.lbl_current_git_user.setStyleSheet("color: #aaa; font-size: 12px; padding: 4px; background: rgba(255,255,255,5); border-radius: 4px;")
        l.addWidget(self.lbl_current_git_user)
        self.txt_git_name = QLineEdit()
        self.txt_git_name.setPlaceholderText("Git user name")
        l.addWidget(self.txt_git_name)
        self.txt_git_email = QLineEdit()
        self.txt_git_email.setPlaceholderText("Git email")
        l.addWidget(self.txt_git_email)
        self.btn_git_user_save = PremiumButton("Save")
        self.btn_git_user_save.clicked.connect(lambda: self.save_git_user_config(main_app))
        l.addWidget(self.btn_git_user_save)
        self.content_layout.addWidget(p); self.content_layout.addStretch()

    def save_git_user_config(self, main_app):
        name = self.txt_git_name.text().strip()
        email = self.txt_git_email.text().strip()
        if not name or not email:
            main_app.log("[WARN] Git name and email must not be empty")
            return
        try:
            if main_app.git:
                main_app.git.run_git(["config", "--global", "user.name", name])
                main_app.git.run_git(["config", "--global", "user.email", email])
                main_app.log(f"[SUCCESS] Global git user set to {name} <{email}>")
                # Update the display label immediately
                self.lbl_current_git_user.setText(f"Current: {name} <{email}>")
            else:
                main_app.log("[ERROR] Git backend not available")
        except Exception as e:
            main_app.log(f"[ERROR] Failed to set global git user: {e}")

    def update_current_git_user_display(self, main_app):
        """Refresh the 'Current: ...' label from global git config."""
        if not (hasattr(self, "lbl_current_git_user") and main_app.git):
            return
        try:
            out_name, _, code_name = main_app.git.run_git(["config", "--global", "user.name"])
            out_email, _, code_email = main_app.git.run_git(["config", "--global", "user.email"])
            if code_name == 0 and code_email == 0:
                name = out_name.strip()
                email = out_email.strip()
                self.lbl_current_git_user.setText(f"Current: {name} <{email}>")
                # Also populate the edit fields if empty
                if not self.txt_git_name.text().strip():
                    self.txt_git_name.setText(name)
                if not self.txt_git_email.text().strip():
                    self.txt_git_email.setText(email)
            else:
                self.lbl_current_git_user.setText("Current: Not set")
        except Exception:
            self.lbl_current_git_user.setText("Current: Unable to read")

class TutorialPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "Tutorial", "How to use RepoMate", main_app)
        card = GlassPanel(); lay = QVBoxLayout(card)
        lay.setSpacing(24); lay.setContentsMargins(32, 32, 32, 32)
        # Title
        title = QLabel("How to Use RepoMate")
        title.setFont(QFont("Inter", 28, QFont.Bold))
        title.setStyleSheet("color: #38bdf8; margin-bottom: 16px; font-size: 12pt;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title, alignment=Qt.AlignCenter)
        # Steps
        steps = QVBoxLayout()
        steps.setSpacing(16)
        for i, (heading, body) in enumerate(self._tutorial_steps(), 1):
            step = QVBoxLayout()
            step.setSpacing(8)
            h = QLabel(f"{i}. {heading}")
            h.setFont(QFont("Inter", 16, QFont.Bold))
            h.setStyleSheet("color: #38bdf8; font-size: 12pt;")
            step.addWidget(h)
            b = QLabel(body)
            b.setWordWrap(True)
            b.setStyleSheet("color: #bbb; font-size: 12pt; padding-left: 16px;")
            step.addWidget(b)
            steps.addLayout(step)
        lay.addLayout(steps)
        # Tips
        tips = self._section_widget("💡 Tips", "• Use natural language like 'commit the changes' or 'create a new branch feature/login'\n• Click the mic button for voice commands\n• AI Gen button writes commit messages from staged changes")
        tips.setStyleSheet("color: #bbb; font-size: 12pt;")
        lay.addWidget(tips)
        self.content_layout.addWidget(card)
        self.content_layout.addStretch()

    def _tutorial_steps(self):
        return [
            ("Select a Repository", "Open a local Git repository via the Dashboard's 'Browse' button or clone from GitHub in the Repositories page."),
            ("Give Commands", "In Dashboard, type a natural language instruction (e.g., 'stage all files and commit') or use the mic button for voice input."),
            ("Generate a Plan", "Click 'Generate Plan' to let AI create a step-by-step Git command list. Review the plan in the preview box."),
            ("Execute", "Click 'Confirm & Execute' to run the generated commands. View real-time CLI output and explanations below."),
            ("Commit Messages", "Use the 'AI Gen' button in the Commit section to generate commit messages from staged changes."),
            ("Configure Git User", "In Settings, set your global Git name and email so all commits use your identity."),
            ("Voice Control", "Select a microphone in Settings and use the mic button to issue commands by voice."),
            ("View History", "Go to History to see recent commits and repository timeline."),
            ("Manage Branches", "Use the Branches page to create, switch, or view local branches."),
        ]

    def _section_widget(self, title, content):
        grp = GlassPanel()
        lay = QVBoxLayout(grp)
        lbl = QLabel(title)
        lbl.setFont(QFont("Inter", 13, QFont.Bold))
        lbl.setStyleSheet("color: #38bdf8; margin-bottom: 4px;")
        lay.addWidget(lbl)
        txt = QLabel(content)
        txt.setWordWrap(True)
        txt.setStyleSheet("color: #bbb; font-size: 12px; padding-left: 8px;")
        lay.addWidget(txt)
        return grp

class AboutPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "About", "App information", main_app)
        # Main card
        card = GlassPanel(); main_lay = QVBoxLayout(card)
        main_lay.setSpacing(24)
        main_lay.setContentsMargins(32, 32, 32, 32)
        # Header
        header = QVBoxLayout()
        header.setAlignment(Qt.AlignCenter)
        # Logo placeholder (emoji)
        logo = QLabel("🔧")
        logo.setFont(QFont("Inter", 48))
        logo.setStyleSheet("color: #38bdf8;")
        header.addWidget(logo, alignment=Qt.AlignCenter)
        title = QLabel("RepoMate")
        title.setFont(QFont("Inter", 32, QFont.ExtraBold))
        title.setStyleSheet("color: #38bdf8;")
        header.addWidget(title, alignment=Qt.AlignCenter)
        tagline = QLabel("AI-Powered Git Assistant")
        tagline.setFont(QFont("Inter", 16))
        tagline.setStyleSheet("color: #ccc;")
        header.addWidget(tagline, alignment=Qt.AlignCenter)
        version = QLabel("Version 1.0")
        version.setFont(QFont("Inter", 14))
        version.setStyleSheet("color: #aaa;")
        header.addWidget(version, alignment=Qt.AlignCenter)
        header.addSpacing(16)
        main_lay.addLayout(header)
        # Two columns
        cols = QHBoxLayout()
        left = QVBoxLayout(); right = QVBoxLayout()
        left.setSpacing(16); right.setSpacing(16)
        # Left Column
        # Description
        left.addWidget(self._section_widget("📖 Description", "RepoMate is an AI-powered Git assistant that simplifies repository management by converting natural language into Git commands and generating intelligent commit messages."))
        # Features
        left.addWidget(self._section_widget("⚡ Features", "• Convert natural language instructions into Git commands\n• Generate AI-powered commit messages\n• View repository insights and activity\n• Voice-controlled Git interactions"))
        # Built With
        left.addWidget(self._section_widget("🛠️ Built With", "PyQt5 • OpenAI • Git • SpeechRecognition"))
        left.addStretch()
        # Right Column
        # System Information
        import platform, subprocess, sys
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        os_name = platform.system()
        os_ver = platform.version()
        git_ver = "Unknown"
        try:
            out, _, code = subprocess.run(["git", "--version"], capture_output=True, text=True)
            if code == 0:
                git_ver = out.strip().replace("git version ", "")
        except Exception:
            git_ver = "Not installed"
        sys_text = f"Python: {py_ver}\nOS: {os_name} {os_ver}\nGit: {git_ver}"
        right.addWidget(self._section_widget("💻 System Information", sys_text))
        # Developer
        right.addWidget(self._section_widget("👨‍💻 Developer", "Developer: Amruth ks"))
        # Links
        links = QVBoxLayout()
        links.setSpacing(8)
        btn_gh = PremiumButton("🔗 Open GitHub Repository")
        btn_gh.clicked.connect(self._open_github)
        links.addWidget(btn_gh)
        btn_docs = PremiumButton("📚 Documentation")
        btn_docs.clicked.connect(self._open_docs)
        links.addWidget(btn_docs)
        right.addLayout(links)
        right.addStretch()
        cols.addLayout(left); cols.addLayout(right)
        main_lay.addLayout(cols)
        # Bottom buttons
        btn_row = QHBoxLayout()
        btn_update = PremiumButton("🔄 Check for Updates")
        btn_update.clicked.connect(self._check_updates)
        btn_copy = PremiumButton("📋 Copy Version Info")
        btn_copy.clicked.connect(self._copy_version_info)
        btn_row.addWidget(btn_update); btn_row.addWidget(btn_copy)
        btn_row.addStretch()
        main_lay.addLayout(btn_row)
        self.content_layout.addWidget(card)
        self.content_layout.addStretch()

    def _section_widget(self, title, content):
        grp = GlassPanel()
        lay = QVBoxLayout(grp)
        lbl = QLabel(title)
        lbl.setFont(QFont("Inter", 13, QFont.Bold))
        lbl.setStyleSheet("color: #38bdf8; margin-bottom: 4px;")
        lay.addWidget(lbl)
        txt = QLabel(content)
        txt.setWordWrap(True)
        txt.setStyleSheet("color: #bbb; font-size: 12px; padding-left: 8px;")
        lay.addWidget(txt)
        return grp

    def _open_github(self):
        import webbrowser
        webbrowser.open("https://github.com/Amruth-ks/RepoMate")

    def _open_docs(self):
        import webbrowser
        webbrowser.open("https://github.com/repomate-git-assistant-llm/Project_RepoMate#readme")

    def _check_updates(self):
        self.main.log("[INFO] Checking for updates... (placeholder)")

    def _copy_version_info(self):
        import platform, sys
        info = (
            f"RepoMate v1.0\n"
            f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n"
            f"OS: {platform.system()} {platform.release()}"
        )
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(info)
        self.main.log("[INFO] Version info copied to clipboard")

# ================== MAIN APP CLASS ==================

class GitEaseApp(QWidget):
    def __init__(self):
        super(GitEaseApp, self).__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("RepoMate – AI Git Assistant")
        self.setMinimumSize(900, 600)
        # Set base font size to 12pt for better visibility
        font = self.font()
        font.setPointSize(12)
        self.setFont(font)
        self.git = GitManager(".") if GitManager is not None else None
        self.current_theme = "dark"
        self.current_plan_commands = None
        self._last_git_status_output = None
        self.github_owner_login = None
        self.allowed_github_org = "repomate-git-assistant-llm"
        self._status_refresh_pending = False
        self._selected_repo_path = None
        self.is_recording = False  # Add missing attribute for voice recording
        self.setStyleSheet(get_stylesheet(self.current_theme))
        l = QHBoxLayout(self); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(0)
        self.sidebar = ModernSidebar(self); l.addWidget(self.sidebar)
        r = QWidget(); rl = QVBoxLayout(r); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(0)
        self.header = ModernHeader(self); rl.addWidget(self.header)
        self.stack = QStackedWidget(); self.stack.setContentsMargins(16, 16, 16, 16)
        self.pages = {
            "Dashboard": DashboardPage(self), "Repositories": RepositoriesPage(self),
            "Commit": CommitPage(self), "Branches": BranchesPage(self),
            "History": HistoryPage(self), "Settings": SettingsPage(self),
            "About": AboutPage(self), "Tutorial": TutorialPage(self)
        }
        for p in self.pages.values():
            if p is not None:
                self.stack.addWidget(p)
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
        # Update commit page colors
        commit_page = self.pages.get("Commit")
        if commit_page and hasattr(commit_page, 'update_theme_colors'):
            commit_page.update_theme_colors(self.current_theme == "light")
        for p in self.pages.values():
            for w in p.findChildren(GlassPanel): w.update_glow(self.current_theme)

    def switch_to_page(self, name):
        if name in self.pages:
            new_widget = self.pages[name]
            # Smooth Fade Transition
            self.anim = QPropertyAnimation(new_widget, b"windowOpacity")
            self.anim.setDuration(300)
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.stack.setCurrentWidget(new_widget)
            self.anim.start()

    def log(self, msg):
        w = self.pages["Dashboard"].git_output
        try:
            text = "" if msg is None else str(msg)
        except Exception:
            text = ""

        if "\n" in text:
            for line in text.splitlines():
                w.addItem(line)
        else:
            w.addItem(text)

        w.scrollToBottom()

    def update_git_status(self):
        if self.git is None:
            return
        # Prevent multiple overlapping updates
        if hasattr(self, 'status_worker') and self.status_worker.isRunning():
            self._status_refresh_pending = True
            return
            
        # Show loading shimmer
        dash = self.pages["Dashboard"]
        dash.card_branch.show_loading()
        dash.card_status.show_loading()
        dash.card_last.show_loading()
            
        self.status_worker = GitStatusWorker(self.git)
        self.status_worker.status_updated.connect(self.on_status_ready)
        self.status_worker.branches_updated.connect(self.on_branches_ready)
        self.status_worker.log_updated.connect(self.on_history_ready)
        self.status_worker.error.connect(self.on_status_error)
        self.status_worker.finished.connect(self.on_status_worker_finished)
        self.status_worker.start()

    def on_status_worker_finished(self):
        if self._status_refresh_pending:
            self._status_refresh_pending = False
            self.update_git_status()

    def on_status_error(self, err_msg):
        dash = self.pages.get("Dashboard")
        if dash is None:
            return

        try:
            sender = self.sender()
            sender_git = getattr(sender, "git", None)
            sender_path = getattr(sender_git, "repo_path", None)
            current_path = getattr(self.git, "repo_path", None)
            if sender_path and current_path and sender_path != current_path:
                return
        except Exception:
            pass

        try:
            dash.card_branch.set_status(False, "Error")
            dash.card_status.set_status(False, "Error")
            dash.card_last.set_status(False, "Error")
        except Exception:
            pass

        self.log(f"[ERROR] Status refresh failed: {err_msg}")

    def on_status_ready(self, s):
        dash = self.pages["Dashboard"]

        try:
            sender = self.sender()
            sender_git = getattr(sender, "git", None)
            sender_path = getattr(sender_git, "repo_path", None)
            current_path = getattr(self.git, "repo_path", None)
            if sender_path and current_path and sender_path != current_path:
                return
        except Exception:
            pass

        self.sidebar.pill_git.set_state(s['initialized'])
        self.sidebar.pill_git.setText("Git Connected" if s['initialized'] else "No Repo")
        try:
            dash.txt_repo_path.setText(self._selected_repo_path or (self.git.repo_path if self.git else ""))
        except Exception:
            pass

        if s.get('initialized'):
            dash.card_branch.set_status(True, s.get('current_branch', 'Unknown'))
            dash.card_status.set_status(True, f"{s.get('pending_changes', 0)} Changes")
            dash.card_last.set_status(True, s.get('last_commit', "Unknown"))
        else:
            dash.card_branch.set_status(False, "No Repo")
            dash.card_status.set_status(False, "No Repo")
            dash.card_last.set_status(False, "No Repo")

        try:
            if s.get('initialized'):
                out, err, code = self.git.run_git(["status", "-sb"])
                status_text = out if code == 0 else (err or "")
            else:
                status_text = ""
        except Exception:
            status_text = ""

        if status_text and status_text != self._last_git_status_output:
            self._last_git_status_output = status_text
            self.log("[STATUS]\n" + status_text)
        
        try:
            self.pages["Repositories"].lbl_current.setText(self._selected_repo_path or (self.git.repo_path if self.git else ""))
        except Exception:
            pass
        # CommitPage no longer has file_list; skip updating it

    def on_branches_ready(self, branches):
        try:
            sender = self.sender()
            sender_git = getattr(sender, "git", None)
            sender_path = getattr(sender_git, "repo_path", None)
            current_path = getattr(self.git, "repo_path", None)
            if sender_path and current_path and sender_path != current_path:
                return
        except Exception:
            pass
        bp = self.pages["Branches"]; bp.branch_list.clear()
        current = self.git.get_status().get('current_branch', 'Unknown')
        for b in branches:
            bp.branch_list.addItem(f"● {b}" + (" (Current)" if b == current else ""))

    def on_history_ready(self, logs):
        try:
            sender = self.sender()
            sender_git = getattr(sender, "git", None)
            sender_path = getattr(sender_git, "repo_path", None)
            current_path = getattr(self.git, "repo_path", None)
            if sender_path and current_path and sender_path != current_path:
                return
        except Exception:
            pass
        hp = self.pages["History"]; hp.history_list.clear()
        for l in logs: hp.history_list.addItem(l)

    def populate_mics(self):
        c = self.pages["Settings"].combo_mic; c.clear()
        try:
            for i, d in enumerate(sd.query_devices()):
                if d['max_input_channels'] > 0: c.addItem(f"{i}: {d['name']}", i)
        except: pass

    def toggle_recording(self):
        try:
            dash = self.pages["Dashboard"]
            if self.is_recording:
                self.log("[INFO] Processing audio...")
                dash.btn_mic.setEnabled(False)
                dash.btn_mic.setStyleSheet("")
                dash.waveform.set_active(False)
                dash.waveform.setVisible(False)
                if hasattr(self, 'recorder') and self.recorder:
                    self.recorder.stop()
                self.is_recording = False
            else:
                # Check audio dependencies
                if sd is None:
                    self.log("[ERROR] Audio dependencies missing (sounddevice/numpy/speech_recognition)")
                    return
                idx = self.pages["Settings"].combo_mic.currentData()
                if idx is None:
                    idx = sd.default.device[0]
                self.log(f"[INFO] Listening on device {idx}... Speak clearly into the microphone.")
                dash.btn_mic.setStyleSheet("background-color: #f56565; color: white; border: 2px solid #e53e3e;")
                dash.waveform.setVisible(True)
                dash.waveform.set_active(True)
                self.recorder = AudioThread(device_index=idx)
                self.recorder.finished.connect(self.on_recording_finished)
                self.recorder.start()
                self.is_recording = True
        except Exception as e:
            self.log(f"[ERROR] Voice recording failed: {e}")
            # Reset UI state
            try:
                dash = self.pages["Dashboard"]
                dash.btn_mic.setEnabled(True)
                dash.btn_mic.setStyleSheet("")
                dash.waveform.set_active(False)
                dash.waveform.setVisible(False)
                self.is_recording = False
            except Exception:
                pass

    def on_recording_finished(self, text):
        try:
            dash = self.pages["Dashboard"]
            dash.btn_mic.setEnabled(True)
            dash.btn_mic.setStyleSheet("")
            if text and text.strip():
                dash.txt_command.setPlainText(text.strip())
                self.log(f"[AUDIO] {text.strip()}")
                self.plan_action()
            else:
                self.log("[WARN] No speech detected")
                self.log("[INFO] Speech not recognized. Type your command in the text box and click Generate Plan.")
        except Exception as e:
            self.log(f"[ERROR] Recording result handling failed: {e}")

    def plan_action(self):
        dash = self.pages["Dashboard"]; inst = dash.txt_command.toPlainText()
        if not inst: self.log("[WARN] Enter instruction"); return

        if self.git is None:
            self.log("[ERROR] Git backend not available")
            return

        try:
            initialized = bool(self.git.get_status().get('initialized'))
        except Exception:
            initialized = False
        if not initialized:
            self.log("[ERROR] Select a valid Git repository first")
            return

        if not self.is_current_repo_allowed():
            self.log("[ERROR] Selected repository is not allowed")
            return

        if processor is None or planner is None or validator is None:
            self.log("[ERROR] AI planner not configured (missing imports / OPENAI_API_KEY)")
            return

        self.log(f"[AI] Planning..."); dash.btn_plan.setEnabled(False)
        self.ai = AIWorker(inst); self.ai.finished.connect(self.on_plan_finished); self.ai.error.connect(self.on_plan_error); self.ai.start()

    def on_plan_finished(self, plan, cmds):
        dash = self.pages["Dashboard"]; dash.btn_plan.setEnabled(True); self.current_plan_commands = cmds
        dash.txt_plan_preview.setPlainText("\n".join(cmds)); dash.plan_card.setVisible(True); dash.commit_assist.setVisible(True)
        if plan and 'commit_message' in plan and plan['commit_message'] is not None:
            dash.txt_commit_msg.setText(str(plan['commit_message']))
        self.log(f"[SUCCESS] Plan ready ({len(cmds)} steps)")

    def on_plan_error(self, m): self.pages["Dashboard"].btn_plan.setEnabled(True); self.log(f"[ERROR] {m}")

    def execute_plan(self):
        if not self.current_plan_commands: self.log("[WARN] No plan"); return
        if not self.is_current_repo_allowed():
            self.log("[ERROR] Execution blocked: selected repository is not owned by the connected GitHub account")
            return
        dash = self.pages["Dashboard"]; dash.btn_confirm.setEnabled(False); dash.btn_confirm.setText("Executing...")
        if hasattr(dash, "cli_output") and dash.cli_output is not None:
            dash.cli_output.setPlainText("")
        self.worker = CommandWorker(self.git, self.current_plan_commands)
        self.worker.progress.connect(self.on_command_progress)
        self.worker.explanation.connect(self.on_command_explanation)
        self.worker.finished.connect(self.on_exec_finished); self.worker.start()

    def on_command_explanation(self, explanation):
        dash = self.pages.get("Dashboard")
        if dash is not None and hasattr(dash, "cli_explanation") and dash.cli_explanation is not None:
            try:
                dash.cli_explanation.setText(explanation)
            except Exception:
                pass

    def on_command_progress(self, msg):
        self.log(msg)
        dash = self.pages.get("Dashboard")
        if dash is not None and hasattr(dash, "cli_output") and dash.cli_output is not None:
            try:
                dash.cli_output.appendPlainText("" if msg is None else str(msg))
            except Exception:
                pass

    def on_exec_finished(self):
        dash = self.pages["Dashboard"]; dash.btn_confirm.setEnabled(True); dash.btn_confirm.setText("Confirm & Execute")
        dash.btn_confirm.trigger_success()
        dash.plan_card.setVisible(False); dash.commit_assist.setVisible(False); self.update_git_status(); self.log("[SUCCESS] Done")

    def generate_commit_ai(self):
        if not self.git:
            self.log("[ERROR] Git backend not available")
            return
        # Get staged diff
        diff = self.git.get_staged_diff()
        if not diff.strip():
            self.log("[WARN] No staged changes to analyze")
            return
        dash = self.pages["Dashboard"]
        self.log("[AI] Generating commit message from staged changes...")
        dash.txt_commit_msg.setPlaceholderText("Generating...")

        def run_ai():
            try:
                # Use OpenAI directly to generate a concise commit message from diff
                import openai
                prompt = (
                    "You are an expert developer. Write a concise, conventional commit message for the following staged diff.\n"
                    "Use the format: <type>(<scope>): <description>\n"
                    "Keep it under 72 characters. No extra text.\n\n"
                    f"Diff:\n{diff}"
                )
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                msg = response["choices"][0]["message"]["content"].strip()
                # Fallback to generic if AI fails
                return msg if msg else "Update"
            except Exception as e:
                raise e

        self.ai_worker = GenericWorker(run_ai)
        self.ai_worker.result.connect(lambda msg: (dash.txt_commit_msg.setText(msg), self.log(f"[AI] Suggested: {msg}")))
        self.ai_worker.error.connect(lambda e: self.log(f"[ERROR] {e}"))
        self.ai_worker.start()

    def select_repo(self):
        if GitManager is None:
            self.log("[ERROR] Git backend not available")
            return
        p = QFileDialog.getExistingDirectory(self, "Select Repo")
        if not p:
            return

        candidate = GitManager(p)
        if not self.is_repo_path_allowed(candidate):
            self.log("[ERROR] Selected folder is not connected to a repository owned by the connected GitHub account")
            return

        self.git = candidate
        self._selected_repo_path = self.git.repo_path

        dash = self.pages.get("Dashboard")
        if dash is not None and hasattr(dash, "txt_repo_path") and dash.txt_repo_path is not None:
            dash.txt_repo_path.setText(self.git.repo_path)
        rp = self.pages.get("Repositories")
        if rp is not None and hasattr(rp, "lbl_current") and rp.lbl_current is not None:
            rp.lbl_current.setText(self.git.repo_path)

        self.update_git_status()
        self.log(f"[INFO] Path: {p}")

    def connect_github_account(self, token):
        tok = (token or "").strip()
        if not tok:
            self.log("[WARN] Enter a GitHub token")
            return

        try:
            self.git.set_github_token(tok)
            user = self.git.github.get_authenticated_user()
            login = user.get("login") if isinstance(user, dict) else None
            if not login:
                self.github_owner_login = None
                self.log("[ERROR] GitHub token invalid or unauthorized")
            else:
                self.github_owner_login = login
                self.log(f"[SUCCESS] GitHub connected as {login}")
        except Exception as e:
            self.github_owner_login = None
            self.log(f"[ERROR] GitHub connect failed: {e}")

        sp = self.pages.get("Settings")
        if sp is not None and hasattr(sp, "lbl_gh_user"):
            sp.lbl_gh_user.setText(self.github_owner_login or "Not connected")
        # Refresh git user display
        if sp is not None and hasattr(sp, "update_current_git_user_display"):
            sp.update_current_git_user_display(self)

    def _parse_github_owner_repo(self, url):
        if not url or not isinstance(url, str):
            return None, None
        u = url.strip()

        m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", u)
        if not m:
            return None, None
        owner = m.group("owner")
        repo = m.group("repo")
        return owner, repo

    def is_remote_allowed(self, remote_url):
        owner, _ = self._parse_github_owner_repo(remote_url)
        return self.is_owner_allowed(owner)

    def is_owner_allowed(self, owner_login):
        if not owner_login:
            return False
        if owner_login == self.allowed_github_org:
            return True
        if self.github_owner_login and owner_login == self.github_owner_login:
            return True
        return False

    def is_repo_path_allowed(self, git_mgr):
        try:
            out, err, code = git_mgr.run_git(["remote", "get-url", "origin"])
            origin_url = out.strip() if code == 0 else ""
        except Exception:
            origin_url = ""
        return self.is_remote_allowed(origin_url)

    def is_current_repo_allowed(self):
        return self.is_repo_path_allowed(self.git)

    def git_stage_all(self): self.git.run_command(["add", "."]); self.update_git_status()
    def git_commit(self, m): self.git.run_command(["commit", "-m", m]); self.update_git_status(); self.log(f"[SUCCESS] Committed")
    def git_create_branch(self):
        n, ok = QInputDialog.getText(self, "New Branch", "Name:")
        if ok and n: self.git.run_command(["checkout", "-b", n]); self.update_git_status()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyle("Fusion")
    window = GitEaseApp(); window.show(); sys.exit(app.exec_())
