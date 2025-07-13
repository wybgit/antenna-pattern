import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

# 设置Qt平台
os.environ["QT_QPA_PLATFORM"] = "xcb"

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 