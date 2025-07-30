# 天线方向图可视化工具

这是一个用于可视化天线方向图的工具，可以读取Excel格式的测量数据并生成极坐标方向图。

## 功能特点

- 支持读取Excel格式的天线测量数据
- 可以选择不同频率点和切面
- 支持数据归一化显示
- 可以自定义图表标题
- 支持调整输出图片分辨率
- 可以导出高质量图片
- 支持多个方向图的叠加显示

## 使用说明

1. 运行程序后，点击"选择Excel文件"按钮选择数据文件
2. 在下拉菜单中选择要显示的频率点和切面
3. 可以选择是否对数据进行归一化处理
4. 在标题输入框中输入图表标题
5. 调整DPI值以设置输出图片的分辨率
6. 点击"保存图片"按钮导出图片

## Excel文件格式要求

Excel文件应包含以下内容：
- 第一列：角度数据（0-360度）
- 其他列：不同频率点的测量数据

## 安装说明

### 从源码运行

1. 安装Python 3.7或更高版本
2. 安装依赖包：
```bash
pip install -r requirements.txt
```
3. 运行程序：
```bash
python main.py
```

### 使用可执行文件

直接运行打包好的exe文件即可。

## 编译打包说明

### Windows平台打包

1. 安装PyInstaller：
```bash
pip install pyinstaller
```

2. 基础打包命令（推荐）：
```bash
pyinstaller --onefile --name "antenna-pattern" --windowed --optimize=2 main.py
```

3. 带图标的打包命令（如果有icon.ico文件）：
```bash
pyinstaller --onefile --name "antenna-pattern" --icon "icon.ico" --windowed --optimize=2 main.py
```

4. 小体积优化打包命令（谨慎使用）：
```bash
pyinstaller --onefile --name "antenna-pattern" --windowed --optimize=2 --exclude-module tkinter --exclude-module unittest main.py
```

5. 如果遇到模块冲突错误，使用最简单的打包命令：
```bash
pyinstaller --onefile --name "antenna-pattern" --windowed main.py
```

6. 打包完成后，可执行文件将在 `dist` 目录下生成为 `antenna-pattern.exe`

### 打包参数说明

- `--onefile`: 打包成单个exe文件
- `--name "antenna-pattern"`: 指定生成的exe文件名
- `--icon "icon.ico"`: 设置程序图标
- `--windowed`: 不显示控制台窗口（GUI程序）
- `--optimize=2`: 启用Python字节码优化，减小文件大小
- `--exclude-module`: 排除不需要的模块，进一步减小文件大小（可能导致兼容性问题）

### 打包故障排除

如果打包过程中遇到错误：

1. **模块冲突错误**：使用最简单的打包命令，不添加 `--exclude-module` 参数
2. **缺少图标文件**：去掉 `--icon` 参数或确保 `icon.ico` 文件存在
3. **依赖库问题**：确保所有依赖都已正确安装：`pip install -r requirements.txt`
4. **路径问题**：确保在项目根目录下执行打包命令

### Linux平台打包

1. 安装PyInstaller：
```bash
pip install pyinstaller
```

2. 执行打包命令：
```bash
pyinstaller --onefile --name "antenna-pattern" --icon "icon.ico" --optimize=2 --strip main.py
```

## 代码修改指南

### 项目结构

```
antenna-pattern-kiro/
├── main.py              # 主程序入口
├── ui/                  # UI相关代码
│   ├── main_window.py   # 主窗口
│   └── widgets/        # 自定义控件
├── core/               # 核心功能模块
│   ├── data_loader.py  # 数据加载
│   └── plotter.py      # 绘图功能
└── assets/            # 资源文件
    └── icon.ico       # 程序图标
```

### 添加新功能模块

1. 在适当的目录下创建新的Python模块文件
2. 遵循现有的代码结构和命名规范
3. 在主程序中导入并集成新模块
4. 更新UI以支持新功能

示例：添加新的数据处理模块

```python
# core/data_processor.py
class DataProcessor:
    def __init__(self):
        pass
    
    def process_data(self, data):
        # 实现数据处理逻辑
        pass
```

### 修改现有功能

1. 定位要修改的模块和函数
2. 确保修改不会影响其他功能
3. 更新相关的单元测试
4. 在提交前进行完整的功能测试

### 代码规范

- 使用PEP 8 Python代码风格规范
- 为所有函数和类添加文档字符串
- 使用有意义的变量和函数名
- 保持代码的模块化和可维护性

## 注意事项

- 确保Excel文件格式正确
- 建议使用1920x1080或更高的显示器分辨率
- 导出图片时注意选择合适的DPI值
- 修改代码后请进行充分测试
- 提交代码前请确保所有测试通过 