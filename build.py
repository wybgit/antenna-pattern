import PyInstaller.__main__
import os
import platform

def build_exe():
    # 基本参数
    params = [
        'main.py',
        '--name=天线方向图可视化工具',
        '--windowed',
        '--onefile',
        '--clean',
        '--noconfirm',
    ]
    
    # 添加图标
    if platform.system().lower() == 'windows':
        if os.path.exists('icon.ico'):
            params.append('--icon=icon.ico')
    else:
        if os.path.exists('icon.png'):
            params.append('--icon=icon.png')
    
    # 添加数据文件，根据平台使用不同的分隔符
    if platform.system().lower() == 'windows':
        params.append('--add-data=README.md;.')
    else:
        params.append('--add-data=README.md:.')
    
    # 运行打包
    PyInstaller.__main__.run(params)

if __name__ == '__main__':
    build_exe() 