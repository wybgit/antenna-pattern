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

2. 执行打包命令：
```bash
### 打包

我们使用 PyInstaller 进行打包。由于不同环境下库的兼容性问题，推荐以下多步打包流程以确保成功：

1.  **生成 `.spec` 文件**:
    首先，运行以下指令生成一个 `.spec` 配置文件。这一步可能会因为环境问题报错，但没有关系，我们只需要生成 `main.spec` 文件。

    ```sh
    pyinstaller --noconfirm main.py
    ```

2.  **修改 `.spec` 文件**:
    打开新生成的 `main.spec` 文件，找到 `Analysis` 部分的 `excludes` 列表，在其中加入 `'PySide6.QtNetwork'`。修改后应如下所示：

    ```python
    a = Analysis(
        ['main.py'],
        ...
        excludes=['PySide6.QtNetwork'],
        ...
    )
    ```

3.  **执行打包**:
    最后，使用修改后的 `.spec` 文件来执行打包。

    ```sh
    pyinstaller --noconfirm --onefile --windowed --name "antenna-pattern" --icon "icon.ico" --add-data "icon.ico:." --add-data "utils/language.py:utils" main.spec
    ```

    > **注意**: 直接通过命令行打包可能会因为 SSL 库的冲突而失败。通过修改 `.spec` 文件排除有问题的模块是目前最可靠的打包方式。
    
### 运行

打包完成后，在 `dist` 文件夹中找到 `antenna-pattern.exe` 并运行。

```

3. 打包完成后，可执行文件将在 `dist` 目录下生成

### Linux平台打包

1. 安装PyInstaller：
```bash
pip install pyinstaller
```

2. 执行打包命令：
```bash
pyinstaller --onefile --name "antenna-pattern" --icon "icon.ico" --windowed main.py
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