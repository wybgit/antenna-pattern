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
    
    # 添加隐藏导入，确保图片处理库被包含
    hidden_imports = [
        'PIL',
        'PIL.Image',
        'PIL._imaging',
        'scipy.ndimage',
        'numpy',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_tkagg',
        'cv2'  # 可选，如果安装了opencv
    ]
    
    for imp in hidden_imports:
        params.append(f'--hidden-import={imp}')
    
    # Windows特定设置
    if platform.system().lower() == 'windows':
        # 添加更多Windows特定的隐藏导入
        win_imports = [
            'PySide6.QtCore',
            'PySide6.QtGui', 
            'PySide6.QtWidgets',
            'matplotlib.backends._backend_qt5',
        ]
        for imp in win_imports:
            params.append(f'--hidden-import={imp}')
        
        # 收集matplotlib数据
        params.append('--collect-data=matplotlib')
        
        # 收集PySide6数据
        params.append('--collect-data=PySide6')
    
    # 运行打包
    PyInstaller.__main__.run(params)

if __name__ == '__main__':
    build_exe() 