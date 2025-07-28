# 定制化指南

本指南提供了关于如何修改天线方向图可视化工具的说明，包括项目结构概述和添加新UI元素的分步指南。

## 项目结构

项目主要由以下几个关键模块组成：

- **`main.py`**: 应用程序的主入口点。它负责初始化应用程序和主窗口。
- **`ui/main_window.py`**: 这是应用程序的核心，包含了所有的界面逻辑。它处理用户交互、绘图和数据显示。
- **`utils/excel_reader.py`**: 一个数据读取类，负责从Excel和CSV文件中解析天线数据。
- **`utils/language.py`**: 管理应用程序的语言设置，方便进行本地化。

## 如何添加新的界面功能

本示例将演示如何在“视图设置”选项卡中添加一个新按钮。

### 第一步：添加UI元素

首先，打开 `ui/main_window.py` 文件并找到 `create_view_settings_tab` 方法。在此方法内部，您可以添加新的控件。例如，要添加一个新按钮，可以插入以下代码：

```python
# 在 create_view_settings_tab 方法内部
# ... 现有代码 ...

# 添加一个新按钮
my_new_button = QPushButton("我的新按钮")
my_new_button.clicked.connect(self.on_my_new_button_clicked)
view_layout.addWidget(my_new_button)

# ... 现有代码 ...
```

### 第二步：实现按钮功能

接下来，您需要创建当按钮被点击时将调用的方法。将以下方法添加到 `ui/main_window.py` 的 `MainWindow` 类中：

```python
# 在 MainWindow 类内部
def on_my_new_button_clicked(self):
    """处理新按钮的点击事件。"""
    print("我的新按钮被点击了！")
    # 在这里添加任何自定义逻辑，例如显示一个消息框
    QMessageBox.information(self, "新功能", "您已成功添加一个新按钮！")
```

### 第三步：运行应用程序

保存更改后，运行应用程序，您将在“视图设置”选项卡中看到您的新按钮。点击它将会在控制台打印一条消息并显示一个信息框。

您可以遵循同样的过程来添加其他控件，如复选框、滑块或文本输入框。请记得将它们的信号（例如 `stateChanged`、`valueChanged`）连接到相应的处理方法。