import sys
from PyQt5.QtWidgets import QApplication,QWidget,QLabel,QPushButton,QVBoxLayout,QLineEdit

app=QApplication(sys.argv)


window =QWidget()

window.setWindowTitle("UI DEMO")
window.resize(400,400)

label=QLabel("Who are you?")
button=QPushButton("POKE")

layout=QVBoxLayout()
layout.addWidget(label)
layout.addWidget(button)

window.setLayout(layout)


def button_clicked():
    label.setText(" BATMAN ")
button.clicked.connect(button_clicked)




window.show()
sys.exit(app.exec_())