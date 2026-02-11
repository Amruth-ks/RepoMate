import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget,
    QLabel, QLineEdit,
    QPushButton, QVBoxLayout
)

class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Input Example")
        self.resize(300, 200)

        # 1️⃣ Label
        self.label = QLabel("Enter your name:")

        # 2️⃣ Input box
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type here...")

        # 3️⃣ Button
        self.button = QPushButton("Submit")
        self.button.clicked.connect(self.show_name)

        # 4️⃣ Output label
        self.output = QLabel("")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.input_box)
        layout.addWidget(self.button)
        layout.addWidget(self.output)

        self.setLayout(layout)

    def show_name(self):
        name = self.input_box.text()
        self.output.setText(f"Hello, {name}!")

app = QApplication(sys.argv)
window = MyApp()
window.show()
sys.exit(app.exec_())
