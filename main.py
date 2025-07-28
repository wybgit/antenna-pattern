import sys
import os
import platform
import PySide6
import argparse
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

# 设置 PySide6 的包路径
dirname = os.path.dirname(PySide6.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

# 根据操作系统设置合适的Qt平台
system = platform.system().lower()
if system == "linux":
    os.environ["QT_QPA_PLATFORM"] = "xcb"
elif system == "windows":
    # Windows下不需要特别设置平台，会自动使用windows平台插件
    pass
elif system == "darwin":
    # macOS下使用cocoa平台
    os.environ["QT_QPA_PLATFORM"] = "cocoa"

def main():
    parser = argparse.ArgumentParser(description="Antenna Pattern Visualization Tool")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = MainWindow(debug=args.debug)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 