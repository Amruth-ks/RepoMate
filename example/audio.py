import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class GitEaseMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI-Assisted Desktop Version Control System (GIT EASE)")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Header Section
        header_layout = QHBoxLayout()
        self.title_label = QLabel("AI-Assisted Desktop Version Control System (GIT EASE)")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.repo_path_label = QLabel("No repository selected")
        self.branch_label = QLabel("No branch")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("Repo:"))
        header_layout.addWidget(self.repo_path_label)
        header_layout.addSpacing(20)
        header_layout.addWidget(QLabel("Branch:"))
        header_layout.addWidget(self.branch_label)
        main_layout.addLayout(header_layout)
        
        # Main Splitter: Left (Repo) + Right (AI)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        
        # Left: Repository & Status Panel
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(10)
        
        self.select_repo_btn = QPushButton("Select Repository")
        self.select_repo_btn.clicked.connect(self.select_repo)
        left_layout.addWidget(self.select_repo_btn)
        
        # Status Labels
        status_group = QGroupBox("Repository Status")
        status_layout = QVBoxLayout(status_group)
        self.repo_status_label = QLabel("Repository: None")
        self.remote_status_label = QLabel("Remote: None")
        self.working_tree_label = QLabel("Working Tree: Clean")
        status_layout.addWidget(self.repo_status_label)
        status_layout.addWidget(self.remote_status_label)
        status_layout.addWidget(self.working_tree_label)
        left_layout.addWidget(status_group)
        
        # File Status List
        files_group = QGroupBox("File Status")
        files_layout = QVBoxLayout(files_group)
        files_layout.addWidget(QLabel("Staged | Modified | Untracked"))
        self.file_list = QListWidget()
        # Example items (color-coded in full impl)
        self.file_list.addItems(["staged: file1.py (green)", "modified: main.py (yellow)", "untracked: new.txt (red)"])
        files_layout.addWidget(self.file_list)
        left_layout.addWidget(files_group)
        
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        splitter.setStretchFactor(0, 1)  # Left narrower
        
        # Right: AI Command & Execution Panel
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)
        
        # Natural Language Input
        self.nl_input = QTextEdit()
        self.nl_input.setPlaceholderText("Enter natural language command, e.g., 'commit my changes', 'pull latest changes'")
        self.nl_input.setMaximumHeight(100)
        right_layout.addWidget(QLabel("Natural Language Input:"))
        right_layout.addWidget(self.nl_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.plan_btn = QPushButton("Plan Action")
        self.plan_btn.clicked.connect(self.plan_action)
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setEnabled(False)  # Enable after plan
        self.execute_btn.clicked.connect(self.execute_plan)
        buttons_layout.addWidget(self.plan_btn)
        buttons_layout.addWidget(self.execute_btn)
        buttons_layout.addStretch()
        right_layout.addLayout(buttons_layout)
        
        # Plan Display
        self.plan_display = QTextEdit()
        self.plan_display.setReadOnly(True)
        self.plan_display.setMaximumHeight(150)
        right_layout.addWidget(QLabel("Planned Actions:"))
        right_layout.addWidget(self.plan_display)
        
        right_layout.addStretch()
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 2)  # Right wider
        
        main_layout.addWidget(splitter, 1)
        
        # Bottom: Logs & Output Panel
        logs_group = QGroupBox("Logs & Output")
        logs_layout = QVBoxLayout(logs_group)
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        logs_layout.addWidget(self.logs)
        main_layout.addWidget(logs_group)
        
        self.log("GIT EASE started. Select a repository to begin.")
    
    def log(self, message):
        timestamp = QTime.currentTime().toString("hh:mm:ss")
        self.logs.append(f"[{timestamp}] {message}")
        self.logs.verticalScrollBar().setValue(self.logs.verticalScrollBar().maximum())
    
    def select_repo(self):
        path = QFileDialog.getExistingDirectory(self, "Select Git Repository")
        if path:
            self.repo_path_label.setText(path)
            self.branch_label.setText("main")  # TODO: git rev-parse --abbrev-ref HEAD
            self.repo_status_label.setText("Repository: Valid")
            self.log(f"Repository selected: {path}")
            # TODO: Check .git, init if needed, parse git status
    
    def plan_action(self):
        text = self.nl_input.toPlainText().strip()
        if text:
            plan = f"""AI Planned Actions for "{text}":
1. git add . (stage all changes)
2. git commit -m "AI-assisted commit: {text}"
3. git push origin main"""
            self.plan_display.setText(plan)
            self.execute_btn.setEnabled(True)
            self.log("Action plan generated by AI.")
        else:
            self.log("Enter a command first.")
    
    def execute_plan(self):
        self.log("Executing plan with safety checks...")
        self.log("✓ Repo valid")
        self.log("✓ Remote configured")
        self.log("Executing: git add .")
        self.log("Executing: git commit -m '...'")
        self.log("Executing: git push")
        self.log("✅ All actions completed successfully.")
        # TODO: subprocess.run git commands, error handling, AI fixes

def main():
    app = QApplication(sys.argv)
    
    # Nord Dark Theme (developer-friendly)
    app.setStyle('Fusion')
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(46, 52, 64))      # nord0
    palette.setColor(QPalette.WindowText, QColor(216, 222, 233)) # nord4
    palette.setColor(QPalette.Base, QColor(59, 66, 82))         # nord1
    palette.setColor(QPalette.AlternateBase, QColor(46, 52, 64))
    palette.setColor(QPalette.Text, QColor(216, 222, 233))
    palette.setColor(QPalette.Button, QColor(67, 76, 94))       # nord2
    palette.setColor(QPalette.ButtonText, QColor(216, 222, 233))
    palette.setColor(QPalette.Highlight, QColor(136, 192, 208)) # nord8
    app.setPalette(palette)
    
    # Additional stylesheet for better contrast
    app.setStyleSheet("""
        QGroupBox { font-weight: bold; border: 1px solid #4C566A; border-radius: 5px; margin-top: 1ex; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        QPushButton { background-color: #5E81AC; border-radius: 4px; padding: 8px; }
        QPushButton:hover { background-color: #81A1C1; }
        QPushButton:disabled { background-color: #3B4252; }
        QListWidget::item:selected { background-color: #88C0D0; }
    """)
    
    window = GitEaseMainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
