import PyInstaller.__main__
import os

def build_exe():
    PyInstaller.__main__.run([
        'main.py',
        '--name=天线方向图可视化工具',
        '--windowed',
        '--onefile',
        '--icon=icon.ico',  # 如果有图标文件的话
        '--add-data=README.md;.',  # 如果有README文件的话
        '--clean',
        '--noconfirm',
    ])

if __name__ == '__main__':
    build_exe() 