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

## 注意事项

- 确保Excel文件格式正确
- 建议使用1920x1080或更高的显示器分辨率
- 导出图片时注意选择合适的DPI值 