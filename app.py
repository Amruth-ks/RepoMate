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
    QStackedWidget, QInputDialog, QFileDialog, QStyle, QStyleOptionButton
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QPropertyAnimation, QEasingCurve, pyqtSlot, pyqtProperty, QPoint
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette, QLinearGradient, QBrush, QPainter, QPen, QRadialGradient, QPainterPath, QPixmap

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
        "bg": "#06080c", # Ultra dark for maximum contrast
        "surface": "rgba(20, 30, 45, 220)",
        "surface_hover": "rgba(40, 60, 90, 240)",
        "card_bg": "rgba(10, 15, 25, 240)",
        "border": "rgba(255, 255, 255, 0.15)",
        "text_primary": "#FFFFFF", # Absolute white
        "text_secondary": "#E2E8F0", # Bright slate for high legibility
        "accent": "#00BAFF",
        "accent_glow": "rgba(0, 186, 255, 0.3)",
        "success": "#22C55E",
        "error": "#EF4444",
        "sidebar_bg": "#020617",
        "input_bg": "rgba(2, 6, 23, 200)",
        "glow": "0 8px 32px 0 rgba(0, 0, 0, 0.7)"
    },
    "light": {
        "bg": "#e2e8f0", # Slightly darker slate for better card contrast
        "surface": "#ffffff", 
        "surface_hover": "#f1f5f9",
        "card_bg": "#ffffff",
        "border": "#94a3b8", # Darker border for clear separation
        "text_primary": "#0f172a", # Deep navy
        "text_secondary": "#334155", # High-contrast slate
        "accent": "#0ea5e9",
        "accent_glow": "rgba(14, 165, 233, 0.2)",
        "success": "#15803d",
        "error": "#b91c1c",
        "sidebar_bg": "#f1f5f9",
        "input_bg": "#ffffff",
        "glow": "0 2px 10px rgba(0, 0, 0, 0.1)"
    }
}

def get_stylesheet(theme_name="dark"):
    t = THEMES[theme_name]
    return f"""
    QWidget {{
        background-color: transparent;
        color: {t['text_primary']};
        font-family: 'Inter', 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
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
        border-radius: 20px;
    }}
    
    QLabel#Title {{
        font-size: 24px;
        font-weight: 800;
        color: {t['text_primary']};
        letter-spacing: -1px;
    }}
    
    QLabel#SectionLabel {{
        font-size: 12px;
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
    }}
    QListWidget::item {{
        padding: 10px;
        border-radius: 8px;
        margin: 2px 4px;
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
        if self.objectName() == "PrimaryBtn" and not self.underMouse():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
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
        self.title_label.setFont(QFont("Inter", 24, QFont.ExtraBold))
        self.title_label.setFixedWidth(260)
        
        if logo_lbl: layout.addWidget(logo_lbl)
        if hasattr(self, 'title_label'): layout.addWidget(self.title_label)
        layout.addStretch()
        
        # Desktop Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search commands or files... (Ctrl+F)")
        self.search_bar.setFixedWidth(300)
        self.search_bar.setStyleSheet("""
            background-color: rgba(255, 255, 255, 10);
            border: 1px solid rgba(255, 255, 255, 20);
            font-size: 13px;
        """)
        layout.addWidget(self.search_bar)
        layout.addSpacing(20)
        
        self.btn_theme = PremiumButton("☀️" if main_app.current_theme == "dark" else "🌙")
        self.btn_theme.setFixedSize(40, 40)
        self.btn_theme.clicked.connect(main_app.toggle_theme)
        layout.addWidget(self.btn_theme)
        btn_sett = PremiumButton("⚙️")
        btn_sett.setFixedSize(40, 40)
        layout.addWidget(btn_sett)

class ModernSidebar(QFrame):
    def __init__(self, main_app):
        super(ModernSidebar, self).__init__(main_app)
        self.setObjectName("Sidebar")
        self.setFixedWidth(240)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 30, 15, 30)
        layout.setSpacing(8)
        self.nav_items = []
        nav_config = [
            ("Dashboard", "󰕷"), ("Repositories", "󰓼"), ("Commit", "󰄲"), 
            ("Branches", "󰘬"), ("History", "󰄉"), ("Settings", "󰒓")
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
    def __init__(self, title, subtitle, main_app):
        super(BasePage, self).__init__(main_app)
        self.main = main_app
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        header_container = QWidget()
        header = QVBoxLayout(header_container)
        header.setContentsMargins(0, 0, 0, 0)
        
        t = QLabel(title)
        t.setObjectName("Title")
        header.addWidget(t)
        
        s = QLabel(subtitle)
        s.setStyleSheet(f"color: {THEMES['dark']['text_secondary']}; font-size: 13px; font-weight: 500;")
        header.addWidget(s)
        
        self.layout.addWidget(header_container)
        self.layout.addSpacing(20)
        self.content_layout = QVBoxLayout()
        self.layout.addLayout(self.content_layout)
        self.layout.addStretch()

class DashboardPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "Dashboard", "Welcome to REPOMATE – AI Git Assistant", main_app)
        panel = GlassPanel(self)
        p_lay = QVBoxLayout(panel)
        p_lay.addWidget(QLabel("Repository Path").setObjectName("SectionLabel"))
        row = QHBoxLayout()
        self.txt_repo_path = QLineEdit(); self.txt_repo_path.setReadOnly(True)
        btn_br = PremiumButton("Browse"); btn_br.clicked.connect(main_app.select_repo)
        row.addWidget(self.txt_repo_path); row.addWidget(btn_br)
        p_lay.addLayout(row)
        self.content_layout.addWidget(panel)
        grid = QHBoxLayout(); grid.setSpacing(32)
        grid.setContentsMargins(10, 10, 10, 10)
        left = QVBoxLayout(); left.setSpacing(24)
        cmd_p = GlassPanel(); cmd_lay = QVBoxLayout(cmd_p)
        cmd_lay.addWidget(QLabel("AI Command").setObjectName("SectionLabel"))
        self.txt_command = QTextEdit(); self.txt_command.setPlaceholderText("Enter command..."); self.txt_command.setFixedHeight(80)
        cmd_lay.addWidget(self.txt_command)
        ctrl = QHBoxLayout()
        self.btn_mic = PulsingButton("🎤"); self.btn_mic.setFixedSize(40, 40); self.btn_mic.clicked.connect(main_app.toggle_recording)
        self.btn_plan = PulsingButton("Generate Plan"); self.btn_plan.setObjectName("PrimaryBtn"); self.btn_plan.clicked.connect(main_app.plan_action)
        ctrl.addWidget(self.btn_mic); ctrl.addWidget(self.btn_plan)
        cmd_lay.addLayout(ctrl)
        left.addWidget(cmd_p)
        self.waveform = WaveformWidget(main_app); self.waveform.setVisible(False); left.addWidget(self.waveform)
        self.plan_card = GlassPanel(); self.plan_card.setVisible(False); plan_lay = QVBoxLayout(self.plan_card)
        plan_lay.addWidget(QLabel("Suggested Plan").setObjectName("SectionLabel"))
        self.txt_plan_preview = QPlainTextEdit(); self.txt_plan_preview.setReadOnly(True); self.txt_plan_preview.setStyleSheet("font-family: monospace;")
        plan_lay.addWidget(self.txt_plan_preview)
        self.btn_confirm = PulsingButton("Confirm & Execute"); self.btn_confirm.setObjectName("PrimaryBtn"); self.btn_confirm.clicked.connect(main_app.execute_plan)
        plan_lay.addWidget(self.btn_confirm)
        left.addWidget(self.plan_card)
        self.commit_assist = GlassPanel(); self.commit_assist.setVisible(False); ca_lay = QVBoxLayout(self.commit_assist)
        ca_lay.addWidget(QLabel("Commit Message").setObjectName("SectionLabel"))
        c_row = QHBoxLayout(); self.txt_commit_msg = QLineEdit(); btn_ai = PremiumButton("AI Gen"); btn_ai.clicked.connect(main_app.generate_commit_ai)
        c_row.addWidget(self.txt_commit_msg); c_row.addWidget(btn_ai)
        ca_lay.addLayout(c_row); left.addWidget(self.commit_assist); left.addStretch()
        right = QVBoxLayout(); right.setSpacing(20)
        out_p = GlassPanel(); out_lay = QVBoxLayout(out_p); out_lay.addWidget(QLabel("Git Output").setObjectName("SectionLabel"))
        self.git_output = QListWidget(); out_lay.addWidget(self.git_output); right.addWidget(out_p)
        st_p = GlassPanel(); st_lay = QVBoxLayout(st_p); st_lay.addWidget(QLabel("Real-time Status").setObjectName("SectionLabel"))
        self.card_branch = StatusCard("Active Branch", "󰘬"); self.card_status = StatusCard("Working Tree", "󱇬"); self.card_last = StatusCard("Latest Activity", "🕒")
        st_lay.addWidget(self.card_branch)
        st_lay.addWidget(self.card_status)
        st_lay.addWidget(self.card_last)
        right.addWidget(st_p)
        right.addStretch()
        grid.addLayout(left, 3)
        grid.addLayout(right, 2)
        self.content_layout.addLayout(grid)

class RepositoriesPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "Repositories", "Manage workspace", main_app)
        p = GlassPanel(); l = QVBoxLayout(p); l.addWidget(QLabel("Active Repo").setObjectName("SectionLabel"))
        self.lbl_current = QLabel("None"); self.lbl_current.setStyleSheet("font-size: 16px; font-weight: bold;"); l.addWidget(self.lbl_current)
        b = PulsingButton("Select Folder"); b.setObjectName("PrimaryBtn"); b.clicked.connect(main_app.select_repo); l.addWidget(b)
        self.content_layout.addWidget(p)
        
        # GitHub Search Section
        gh_p = GlassPanel(); gh_l = QVBoxLayout(gh_p)
        gh_l.addWidget(QLabel("GitHub Repositories").setObjectName("SectionLabel"))
        
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
        for r in repos:
            it = QListWidgetItem(f"{r['full_name']} (Stars: {r['stargazers_count']})")
            it.setData(Qt.UserRole, r['clone_url'])
            self.gh_list.addItem(it)
        self.main.log(f"[SUCCESS] Loaded {len(repos)} repositories")

    def clone_selected(self):
        it = self.gh_list.currentItem()
        if not it:
            self.main.log("[WARN] Select a repo to clone")
            return
        
        url = it.data(Qt.UserRole)
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

class CommitPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "Commit", "Review and finalize", main_app)
        split = QHBoxLayout(); s_p = GlassPanel(); s_l = QVBoxLayout(s_p); s_l.addWidget(QLabel("Pending Files").setObjectName("SectionLabel"))
        self.file_list = QListWidget(); s_l.addWidget(self.file_list)
        b_s = PremiumButton("Stage All"); b_s.clicked.connect(main_app.git_stage_all); s_l.addWidget(b_s); split.addWidget(s_p)
        c_p = GlassPanel(); c_l = QVBoxLayout(c_p); c_l.addWidget(QLabel("Message").setObjectName("SectionLabel"))
        self.txt_msg = QTextEdit(); c_l.addWidget(self.txt_msg)
        b_c = PremiumButton("Commit"); b_c.setObjectName("PrimaryBtn"); b_c.clicked.connect(self.commit_manual); c_l.addWidget(b_c); split.addWidget(c_p)
        self.content_layout.addLayout(split)
    def commit_manual(self):
        m = self.txt_msg.toPlainText()
        if m: self.main.git_commit(m); self.txt_msg.clear()

class BranchesPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "Branches", "Local branch management", main_app)
        p = GlassPanel(); l = QVBoxLayout(p); l.addWidget(QLabel("Branches").setObjectName("SectionLabel"))
        self.branch_list = QListWidget(); l.addWidget(self.branch_list)
        b = PremiumButton("New Branch"); b.setObjectName("PrimaryBtn"); b.clicked.connect(main_app.git_create_branch); l.addWidget(b)
        self.content_layout.addWidget(p); self.content_layout.addStretch()

class HistoryPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "History", "Commit timeline", main_app)
        p = GlassPanel(); l = QVBoxLayout(p); l.addWidget(QLabel("Recent Log").setObjectName("SectionLabel"))
        self.history_list = QListWidget(); self.history_list.setStyleSheet("font-family: monospace;"); l.addWidget(self.history_list)
        self.content_layout.addWidget(p)

class SettingsPage(BasePage):
    def __init__(self, main_app):
        BasePage.__init__(self, "Settings", "Configure preferences", main_app)
        p = GlassPanel(); l = QVBoxLayout(p); l.addWidget(QLabel("Microphone").setObjectName("SectionLabel"))
        self.combo_mic = QComboBox(); l.addWidget(self.combo_mic)
        l.addSpacing(20); l.addWidget(QLabel("AI Model").setObjectName("SectionLabel"))
        self.combo_model = QComboBox(); self.combo_model.addItems(["GPT-4", "GPT-3.5", "Local"]); l.addWidget(self.combo_model)
        self.content_layout.addWidget(p); self.content_layout.addStretch()

# ================== MAIN APP CLASS ==================

class GitEaseApp(QWidget):
    def __init__(self):
        super(GitEaseApp, self).__init__()
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
        self.pages["Dashboard"].git_output.addItem(msg)
        self.pages["Dashboard"].git_output.scrollToBottom()

    def update_git_status(self):
        # Prevent multiple overlapping updates
        if hasattr(self, 'status_worker') and self.status_worker.isRunning():
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
        self.status_worker.start()

    def on_status_ready(self, s):
        dash = self.pages["Dashboard"]
        self.sidebar.pill_git.set_state(s['initialized'])
        self.sidebar.pill_git.setText("Git Connected" if s['initialized'] else "No Repo")
        dash.txt_repo_path.setText(self.git.repo_path)
        dash.card_branch.set_status(s['initialized'], s['current_branch'])
        dash.card_status.set_status(s['initialized'], f"{s['pending_changes']} Changes")
        dash.card_last.set_status(s['initialized'], s.get('last_commit', "Unknown"))
        
        self.pages["Repositories"].lbl_current.setText(self.git.repo_path)
        cp = self.pages["Commit"]; cp.file_list.clear()
        for f in s['files']:
            it = QListWidgetItem(cp.file_list)
            w = FileRowWidget(f['name'], f['status'], f['color'])
            it.setSizeHint(w.sizeHint())
            cp.file_list.setItemWidget(it, w)

    def on_branches_ready(self, branches):
        bp = self.pages["Branches"]; bp.branch_list.clear()
        current = self.git.get_status().get('current_branch', 'Unknown')
        for b in branches:
            bp.branch_list.addItem(f"● {b}" + (" (Current)" if b == current else ""))

    def on_history_ready(self, logs):
        hp = self.pages["History"]; hp.history_list.clear()
        for l in logs: hp.history_list.addItem(l)

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
        dash.btn_confirm.trigger_success()
        dash.plan_card.setVisible(False); dash.commit_assist.setVisible(False); self.update_git_status(); self.log("[SUCCESS] Done")

    def generate_commit_ai(self):
        dash = self.pages["Dashboard"]; inst = dash.txt_command.toPlainText() or "current changes"
        self.log("[AI] Generating commit message..."); dash.txt_commit_msg.setPlaceholderText("Generating...")
        
        def run_ai():
            try:
                p = planner.generate_plan(f"Suggest commit message: {inst}")
                return p.get('commit_message', "Update")
            except Exception as e:
                raise e

        self.ai_worker = GenericWorker(run_ai)
        self.ai_worker.result.connect(lambda msg: (dash.txt_commit_msg.setText(msg), self.log(f"[AI] Suggested: {msg}")))
        self.ai_worker.error.connect(lambda e: self.log(f"[ERROR] {e}"))
        self.ai_worker.start()

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
