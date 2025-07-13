from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QPushButton, QComboBox, QFileDialog, QLabel,
                                QCheckBox, QSpinBox, QLineEdit, QMenuBar, QMenu,
                                QStatusBar, QToolBar, QStyle, QColorDialog, QMessageBox,
                                QListWidget, QSplitter, QFrame, QScrollArea, QSlider,
                                QDoubleSpinBox, QDialog, QDialogButtonBox)
from PySide6.QtCore import Qt, QSettings, QSize, QTimer
from PySide6.QtGui import QAction, QIcon, QPixmap
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from utils.excel_reader import AntennaDataReader
from utils.language import Language

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = Language()
        self.settings = QSettings('AntennaPattern', 'Visualization')
        
        # 数据存储
        self.data_reader = None
        self.current_plots = []  # Store multiple plots
        self.active_plot_index = -1  # Currently selected plot index
        self.plot_saved = True  # 标记图像是否已保存
        
        # 3D视图相关
        self.is_3d_view = False
        self.elevation = 30
        self.azimuth = 45
        self.auto_rotate = False
        self.auto_rotate_timer = QTimer()
        self.auto_rotate_timer.timeout.connect(self.rotate_3d_view)
        
        # 图片相关
        self.image_dragging = False
        self.image_resizing = False
        self.image_position = [0.5, 0.5]  # 图片中心位置 [x, y] in figure coordinates
        self.image_size = [0.4, 0.4]      # 图片大小 [width, height] in figure coordinates
        self.drag_start = None
        self.resize_corner = None
        self.resize_start_size = None
        
        self.load_settings()
        self.setup_ui()
        
        # 设置窗口属性
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        
        # 恢复上次的窗口大小和位置
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1400, 900)
        
        # 恢复上次的窗口状态（最大化/普通）
        state = self.settings.value('windowState')
        if state:
            self.restoreState(state)

    def reset_view(self):
        """重置视图"""
        if self.is_3d_view:
            self.reset_3d_view()
        else:
            # 重置2D视图
            self.ax.set_rmax(None)  # 重置半径范围
            self.ax.set_theta_zero_location('N')  # 重置0度位置
            self.ax.set_theta_direction(-1)  # 重置角度方向
            self.canvas.draw()

    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle(self.lang.get('title'))
        self.setMinimumSize(800, 600)  # 设置最小窗口大小
        
        # 创建主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setSpacing(10)  # 设置布局间距
        self.layout.setContentsMargins(10, 10, 10, 10)  # 设置布局边距
        
        # 创建左侧控制面板
        self.create_left_panel()
        
        # 创建右侧图表区域
        self.create_right_panel()
        
        # 创建菜单栏和工具栏
        self.create_menu_bar()
        self.create_tool_bar()
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu(self.lang.get('file'))
        
        open_action = QAction(self.lang.get('open'), self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.load_data)
        file_menu.addAction(open_action)
        
        save_action = QAction(self.lang.get('save'), self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_plot)
        file_menu.addAction(save_action)
        
        # 语言菜单
        lang_menu = menubar.addMenu(self.lang.get('language'))
        
        chinese_action = QAction(self.lang.get('chinese'), self)
        chinese_action.triggered.connect(lambda: self.change_language('zh'))
        lang_menu.addAction(chinese_action)
        
        english_action = QAction(self.lang.get('english'), self)
        english_action.triggered.connect(lambda: self.change_language('en'))
        lang_menu.addAction(english_action)
        
        # 主题菜单
        theme_menu = menubar.addMenu(self.lang.get('theme'))
        
        light_action = QAction(self.lang.get('light'), self)
        light_action.triggered.connect(lambda: self.change_theme('light'))
        theme_menu.addAction(light_action)
        
        dark_action = QAction(self.lang.get('dark'), self)
        dark_action.triggered.connect(lambda: self.change_theme('dark'))
        theme_menu.addAction(dark_action)
        
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        toolbar.setObjectName("mainToolBar")  # 设置工具栏的objectName
        self.addToolBar(toolbar)
        
        # 添加工具栏按钮
        open_action = toolbar.addAction(self.style().standardIcon(QStyle.SP_FileIcon),
                                      self.lang.get('open'))
        open_action.triggered.connect(self.load_data)
        
        save_action = toolbar.addAction(self.style().standardIcon(QStyle.SP_DialogSaveButton),
                                      self.lang.get('save'))
        save_action.triggered.connect(self.save_plot)
        
        toolbar.addSeparator()
        
        # 添加视图类型选择
        toolbar.addWidget(QLabel(self.lang.get('view_type')))
        self.view_combo = QComboBox()
        self.view_combo.addItems([self.lang.get('2d_view'), self.lang.get('3d_view')])
        self.view_combo.currentIndexChanged.connect(self.switch_view)
        toolbar.addWidget(self.view_combo)
        
        toolbar.addSeparator()
        
        # 添加角度编辑控件
        toolbar.addWidget(QLabel(self.lang.get('axis_direction')))
        self.axis_direction_combo = QComboBox()
        self.axis_direction_combo.addItems(['N', 'S', 'E', 'W'])
        self.axis_direction_combo.currentTextChanged.connect(self.update_axis_direction)
        toolbar.addWidget(self.axis_direction_combo)
        
        toolbar.addWidget(QLabel(self.lang.get('axis_angle')))
        self.axis_angle_spin = QDoubleSpinBox()
        self.axis_angle_spin.setRange(-360, 360)
        self.axis_angle_spin.setValue(0)
        self.axis_angle_spin.setSingleStep(15)
        self.axis_angle_spin.valueChanged.connect(self.update_axis_angle)
        toolbar.addWidget(self.axis_angle_spin)
        
        toolbar.addSeparator()
        
        # 添加图片插入按钮
        insert_image_action = toolbar.addAction(self.style().standardIcon(QStyle.SP_FileDialogStart),
                                              self.lang.get('insert_image'))
        insert_image_action.triggered.connect(self.insert_image)
        
        # 添加图片移除按钮
        remove_image_action = toolbar.addAction(self.style().standardIcon(QStyle.SP_DialogDiscardButton),
                                              self.lang.get('remove_image'))
        remove_image_action.triggered.connect(self.remove_image)
        
        toolbar.addSeparator()
        
        # 添加绘图样式控制
        toolbar.addWidget(QLabel(self.lang.get('plot_style')))
        
        toolbar.addWidget(QLabel(self.lang.get('line_style')))
        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(['-', '--', ':', '-.'])
        self.line_style_combo.currentTextChanged.connect(self.on_parameter_changed)
        toolbar.addWidget(self.line_style_combo)
        
        toolbar.addWidget(QLabel(self.lang.get('line_width')))
        self.line_width_spin = QSpinBox()
        self.line_width_spin.setRange(1, 10)
        self.line_width_spin.setValue(2)
        self.line_width_spin.valueChanged.connect(self.on_parameter_changed)
        toolbar.addWidget(self.line_width_spin)
        
        color_action = toolbar.addAction(self.lang.get('line_color'))
        color_action.triggered.connect(self.choose_color)
        self.current_color = 'blue'

    def create_left_panel(self):
        """创建左侧控制面板"""
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.StyledPanel)
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        
        # 3D视图控制区
        self.d3_controls = QFrame()
        d3_layout = QVBoxLayout(self.d3_controls)
        
        # 方位角控制
        azimuth_layout = QHBoxLayout()
        azimuth_layout.addWidget(QLabel(self.lang.get('azimuth')))
        self.azimuth_slider = QSlider(Qt.Horizontal)
        self.azimuth_slider.setRange(0, 360)
        self.azimuth_slider.setValue(45)
        self.azimuth_slider.valueChanged.connect(self.update_3d_view)
        azimuth_layout.addWidget(self.azimuth_slider)
        d3_layout.addLayout(azimuth_layout)
        
        # 仰角控制
        elevation_layout = QHBoxLayout()
        elevation_layout.addWidget(QLabel(self.lang.get('elevation')))
        self.elevation_slider = QSlider(Qt.Horizontal)
        self.elevation_slider.setRange(0, 90)
        self.elevation_slider.setValue(30)
        self.elevation_slider.valueChanged.connect(self.update_3d_view)
        elevation_layout.addWidget(self.elevation_slider)
        d3_layout.addLayout(elevation_layout)
        
        # 自动旋转控制
        auto_rotate_layout = QHBoxLayout()
        self.auto_rotate_cb = QCheckBox(self.lang.get('auto_rotate'))
        self.auto_rotate_cb.stateChanged.connect(self.toggle_auto_rotate)
        auto_rotate_layout.addWidget(self.auto_rotate_cb)
        
        # 重置视图按钮
        reset_view_btn = QPushButton(self.lang.get('reset_view'))
        reset_view_btn.clicked.connect(self.reset_3d_view)
        auto_rotate_layout.addWidget(reset_view_btn)
        
        d3_layout.addLayout(auto_rotate_layout)
        left_layout.addWidget(self.d3_controls)
        self.d3_controls.setVisible(False)
        
        # 数据控制区
        data_group = QFrame()
        data_layout = QVBoxLayout(data_group)
        
        # 曲线列表
        self.plot_list = QListWidget()
        self.plot_list.setMinimumHeight(150)
        self.plot_list.currentRowChanged.connect(self.on_plot_selected)
        data_layout.addWidget(QLabel(self.lang.get('curves')))
        data_layout.addWidget(self.plot_list)
        
        # 曲线控制按钮
        curve_btn_layout = QHBoxLayout()
        add_curve_btn = QPushButton(self.lang.get('add_plot'))
        add_curve_btn.clicked.connect(self.add_new_plot)
        remove_curve_btn = QPushButton(self.lang.get('remove_plot'))
        remove_curve_btn.clicked.connect(self.remove_current_plot)
        curve_btn_layout.addWidget(add_curve_btn)
        curve_btn_layout.addWidget(remove_curve_btn)
        data_layout.addLayout(curve_btn_layout)
        
        left_layout.addWidget(data_group)
        
        # 参数控制区
        param_group = QFrame()
        param_layout = QVBoxLayout(param_group)
        
        # 频率选择
        self.freq_combo = QComboBox()
        self.freq_combo.setMinimumHeight(30)
        self.freq_combo.currentIndexChanged.connect(self.on_parameter_changed)
        param_layout.addWidget(QLabel(self.lang.get('frequency')))
        param_layout.addWidget(self.freq_combo)
        
        # 极化选择
        self.polarization_combo = QComboBox()
        self.polarization_combo.setMinimumHeight(30)
        self.polarization_combo.currentIndexChanged.connect(self.on_parameter_changed)
        param_layout.addWidget(QLabel(self.lang.get('polarization')))
        param_layout.addWidget(self.polarization_combo)
        
        # Theta角度选择
        self.theta_combo = QComboBox()
        self.theta_combo.setMinimumHeight(30)
        self.theta_combo.currentIndexChanged.connect(self.on_parameter_changed)
        param_layout.addWidget(QLabel(self.lang.get('theta_angle')))
        param_layout.addWidget(self.theta_combo)
        
        # 归一化选择
        self.normalize_cb = QCheckBox(self.lang.get('normalize'))
        self.normalize_cb.stateChanged.connect(self.on_parameter_changed)
        param_layout.addWidget(self.normalize_cb)
        
        left_layout.addWidget(param_group)
        
        # 导出控制区
        export_group = QFrame()
        export_layout = QVBoxLayout(export_group)
        
        # 图表标题
        self.title_edit = QLineEdit()
        self.title_edit.setMinimumHeight(30)
        self.title_edit.setPlaceholderText(self.lang.get('plot_title'))
        self.title_edit.textChanged.connect(self.update_title)
        export_layout.addWidget(QLabel(self.lang.get('plot_title')))
        export_layout.addWidget(self.title_edit)
        
        # DPI设置
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setMinimumHeight(30)
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)
        export_layout.addWidget(QLabel(self.lang.get('dpi')))
        export_layout.addWidget(self.dpi_spin)
        
        left_layout.addWidget(export_group)
        
        # 添加弹性空间
        left_layout.addStretch()
        
        self.layout.addWidget(left_panel)

    def create_right_panel(self):
        """创建右侧图表区域"""
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.StyledPanel)
        right_layout = QVBoxLayout(right_panel)
        
        # 创建matplotlib画布
        self.figure = plt.figure(figsize=(10, 10))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # 连接鼠标事件
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        
        self.layout.addWidget(right_panel, stretch=1)
        
        # 初始化为2D视图
        self.ax = self.figure.add_subplot(111, projection='polar')
        self.ax.grid(True)
        self.canvas.draw()

    def on_mouse_press(self, event):
        """处理鼠标按下事件"""
        if not hasattr(self, 'image_ax') or not event.inaxes:
            return
            
        # 获取当前图片的边界
        bbox = self.image_ax.get_position()
        x, y = event.x / self.canvas.width(), event.y / self.canvas.height()
        
        # 检查是否在图片边界内
        if bbox.contains(x, y):
            if event.button == 3:  # 右键点击
                self.on_image_right_click(event)
            else:
                # 检查是否在调整大小的角落区域（右下角）
                corner_size = 0.02  # 角落区域大小
                if (x > bbox.x1 - corner_size and x < bbox.x1 and 
                    y > bbox.y0 and y < bbox.y0 + corner_size):
                    self.image_resizing = True
                    self.resize_start_size = self.image_size.copy()
                    self.resize_corner = [x, y]
                else:
                    self.image_dragging = True
                    self.drag_start = [x - self.image_position[0], y - self.image_position[1]]
        
    def on_mouse_release(self, event):
        """处理鼠标释放事件"""
        self.image_dragging = False
        self.image_resizing = False
        self.drag_start = None
        self.resize_corner = None
        self.resize_start_size = None
        
    def on_mouse_move(self, event):
        """处理鼠标移动事件"""
        if not hasattr(self, 'image_ax') or not event.inaxes:
            return
            
        x, y = event.x / self.canvas.width(), event.y / self.canvas.height()
        
        if self.image_dragging and self.drag_start:
            # 更新图片位置
            new_x = x - self.drag_start[0]
            new_y = y - self.drag_start[1]
            
            # 限制图片不超出画布范围
            new_x = max(self.image_size[0]/2, min(new_x, 1 - self.image_size[0]/2))
            new_y = max(self.image_size[1]/2, min(new_y, 1 - self.image_size[1]/2))
            
            self.image_position = [new_x, new_y]
            self.update_image_position()
            self.canvas.draw()
            
        elif self.image_resizing and self.resize_corner and self.resize_start_size:
            # 获取当前DPI和画布大小
            dpi = self.figure.dpi
            canvas_width = self.canvas.width()
            canvas_height = self.canvas.height()
            
            # 计算鼠标移动的距离（像素）
            dx = (x - self.resize_corner[0]) * canvas_width
            dy = (y - self.resize_corner[1]) * canvas_height
            
            # 计算新的大小（保持纵横比）
            original_ratio = self.resize_start_size[0] / self.resize_start_size[1]
            if abs(dx) > abs(dy):
                new_width = self.resize_start_size[0] * canvas_width + dx
                new_height = new_width / original_ratio
            else:
                new_height = self.resize_start_size[1] * canvas_height + dy
                new_width = new_height * original_ratio
            
            # 限制最小和最大大小
            min_size = 20  # 最小20像素
            max_width = canvas_width * 0.8  # 最大为画布的80%
            max_height = canvas_height * 0.8
            
            new_width = max(min_size, min(new_width, max_width))
            new_height = max(min_size, min(new_height, max_height))
            
            # 转换为相对大小
            self.image_size = [
                (new_width / dpi) / (canvas_width / dpi),
                (new_height / dpi) / (canvas_height / dpi)
            ]
            
            self.update_image_position()
            self.canvas.draw()
            
        # 更新鼠标样式
        if not self.image_dragging and not self.image_resizing:
            bbox = self.image_ax.get_position()
            corner_size = 0.02
            if (x > bbox.x1 - corner_size and x < bbox.x1 and 
                y > bbox.y0 and y < bbox.y0 + corner_size):
                self.canvas.setCursor(Qt.SizeFDiagCursor)  # 调整大小的光标
            elif bbox.contains(x, y):
                self.canvas.setCursor(Qt.OpenHandCursor)  # 拖动的光标
            else:
                self.canvas.setCursor(Qt.ArrowCursor)  # 默认光标

    def switch_view(self, index):
        """切换2D/3D视图"""
        self.is_3d_view = index == 1
        self.d3_controls.setVisible(self.is_3d_view)
        
        # 清除当前图形并创建新的子图
        self.figure.clear()
        
        if self.is_3d_view:
            self.ax = self.figure.add_subplot(111, projection='3d')
        else:
            self.ax = self.figure.add_subplot(111, projection='polar')
            self.ax.grid(True)
        
        # 如果有图片，重新创建图片子图
        if hasattr(self, 'current_image_data'):
            self.image_ax = self.figure.add_axes([0, 0, 1, 1])
            self.image_ax.patch.set_alpha(0)  # 设置背景透明
            self.image_ax.imshow(self.current_image_data, aspect='equal')
            self.image_ax.axis('off')
            self.update_image_position()
            self.image_ax.set_zorder(10)  # 确保图片在最上层
        
        self.update_plot()
        
    def update_3d_view(self):
        """更新3D视图角度"""
        if self.is_3d_view:
            self.elevation = self.elevation_slider.value()
            self.azimuth = self.azimuth_slider.value()
            self.ax.view_init(self.elevation, self.azimuth)
            self.canvas.draw()
            
    def rotate_3d_view(self):
        """自动旋转3D视图"""
        if self.is_3d_view and self.auto_rotate:
            self.azimuth = (self.azimuth + 2) % 360
            self.azimuth_slider.setValue(self.azimuth)
            
    def toggle_auto_rotate(self, state):
        """切换自动旋转状态"""
        self.auto_rotate = state == Qt.Checked
        if self.auto_rotate:
            self.auto_rotate_timer.start(50)  # 50ms interval
        else:
            self.auto_rotate_timer.stop()
            
    def reset_3d_view(self):
        """重置3D视图角度"""
        if self.is_3d_view:
            self.elevation = 30
            self.azimuth = 45
            self.elevation_slider.setValue(self.elevation)
            self.azimuth_slider.setValue(self.azimuth)
            self.ax.view_init(self.elevation, self.azimuth)
            self.canvas.draw()

    def update_plot(self):
        """更新图表"""
        if not self.data_reader:
            return
            
        if not hasattr(self, 'ax'):
            # 如果ax不存在，创建一个新的
            self.figure.clear()
            if self.is_3d_view:
                self.ax = self.figure.add_subplot(111, projection='3d')
            else:
                self.ax = self.figure.add_subplot(111, projection='polar')
                self.ax.grid(True)
        else:
            self.ax.clear()
        
        # 确保主图在最底层
        self.ax.set_zorder(1)
        self.ax.patch.set_alpha(0)  # 设置背景透明
        
        if self.is_3d_view:
            self.update_3d_plot()
        else:
            self.update_2d_plot()
            
        # 如果有图片，重新设置其位置和大小
        if hasattr(self, 'image_ax') and hasattr(self, 'current_image_data'):
            self.update_image_position()
            
        # 调整布局以确保图例不被遮挡
        self.figure.tight_layout()
        
        # 确保图例在最顶层
        if hasattr(self.ax, 'legend_') and self.ax.legend_ is not None:
            self.ax.legend_.set_zorder(10)
        
        self.canvas.draw()
        self.plot_saved = False  # 标记图像未保存

    def update_2d_plot(self):
        """更新2D极坐标图"""
        # 绘制所有曲线
        for i, plot in enumerate(self.current_plots):
            # 获取数据
            theta_angle = float(self.theta_combo.itemText(plot['theta_idx']).replace('°', ''))
            phi_angles = self.data_reader.get_phi_angles()
            gains = self.data_reader.get_gain_data(plot['freq_idx'], theta_angle, plot['polarization'])
            
            if gains is None:
                continue
                
            # 归一化处理
            if plot['normalized']:
                gains = self.data_reader.normalize_data(gains)
                
            # 转换角度为弧度
            phi_rad = self.data_reader.get_angles_in_radians(phi_angles)
            
            # 绘制方向图
            freq_text = self.freq_combo.itemText(plot['freq_idx'])
            label = f"{freq_text}, {plot['polarization']}, θ={theta_angle}°"
            self.ax.plot(phi_rad, gains,
                        linestyle=plot['line_style'],
                        linewidth=plot['line_width'],
                        color=plot['color'],
                        label=label,
                        zorder=5)  # 确保曲线在图片上方
                        
        self.ax.set_theta_zero_location('N')  # 设置0度在北方向
        self.ax.set_theta_direction(-1)  # 设置角度顺时针方向
        self.ax.grid(True)
        
        # 设置刻度标签
        self.ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
        self.ax.set_xticklabels(['0°', '45°', '90°', '135°', '180°', '225°', '270°', '315°'])
        
        # 添加图例并设置位置
        if self.current_plots:
            legend = self.ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
            legend.set_zorder(10)  # 确保图例在最顶层

    def update_3d_plot(self):
        """更新3D方向图"""
        if not self.current_plots:
            return
            
        # 设置3D图的基本属性
        self.ax.set_box_aspect([1,1,1])
        self.ax.grid(True)
        
        # 获取颜色范围
        if self.auto_range_cb.isChecked():
            vmin = None
            vmax = None
        else:
            vmin = self.min_db_spin.value()
            vmax = self.max_db_spin.value()
        
        # 绘制参考球面网格
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        x = 0.3 * np.outer(np.cos(u), np.sin(v))
        y = 0.3 * np.outer(np.sin(u), np.sin(v))
        z = 0.3 * np.outer(np.ones(np.size(u)), np.cos(v))
        self.ax.plot_surface(x, y, z, color='gray', alpha=0.1)
        
        # 绘制坐标轴
        max_val = 0
        
        # 清除之前的颜色条
        if hasattr(self, 'colorbar'):
            self.colorbar.remove()
        
        # 绘制每个方向图
        for i, plot in enumerate(self.current_plots):
            # 获取数据
            phi_angles = np.array(self.data_reader.get_phi_angles())
            theta_angles = np.array(self.data_reader.get_theta_angles())
            
            # 创建完整的角度网格
            phi = np.deg2rad(phi_angles)
            theta = np.deg2rad(theta_angles)
            PHI, THETA = np.meshgrid(phi, theta)
            
            # 获取所有theta角度的增益数据
            gains = np.zeros((len(theta_angles), len(phi_angles)))
            for j, theta_angle in enumerate(theta_angles):
                gain_data = self.data_reader.get_gain_data(plot['freq_idx'], theta_angle, plot['polarization'])
                if gain_data is not None:
                    gains[j] = gain_data
            
            # 归一化处理
            if plot['normalized']:
                gains = self.data_reader.normalize_data(gains)
            
            # 将dB转换为线性值
            r = np.power(10, gains/20.0)
            
            # 转换为笛卡尔坐标
            X = r * np.sin(THETA) * np.cos(PHI)
            Y = r * np.sin(THETA) * np.sin(PHI)
            Z = r * np.cos(THETA)
            
            # 更新最大值
            max_val = max(max_val, np.max(r))
            
            # 绘制3D表面
            freq_text = self.freq_combo.itemText(plot['freq_idx'])
            surf = self.ax.plot_surface(X, Y, Z, 
                                      cmap='viridis',
                                      alpha=0.8 if i == self.active_plot_index else 0.3,
                                      label=f"{freq_text}, {plot['polarization']}",
                                      vmin=vmin,
                                      vmax=vmax)
            
            # 为当前选中的曲线添加特殊标记
            if i == self.active_plot_index:
                # 找到最大值点
                max_idx = np.unravel_index(np.argmax(r), r.shape)
                x_max = X[max_idx]
                y_max = Y[max_idx]
                z_max = Z[max_idx]
                
                # 添加最大值点标记
                self.ax.scatter(x_max, y_max, z_max,
                              color='red', s=100, marker='*',
                              label='Maximum')
                
                # 添加主瓣方向线
                self.ax.plot([0, x_max], [0, y_max], [0, z_max],
                           color='red', linestyle='--', linewidth=2)
                
                # 添加最大值标注
                max_gain = gains[max_idx]
                self.ax.text(x_max, y_max, z_max, 
                           f'{max_gain:.1f} dB',
                           color='red')
                
                # 添加颜色条
                self.colorbar = self.figure.colorbar(surf, ax=self.ax, label='Gain (dB)')
        
        # 设置坐标轴
        axis_length = max(max_val * 1.2, 0.5)
        self.ax.set_xlim([-axis_length, axis_length])
        self.ax.set_ylim([-axis_length, axis_length])
        self.ax.set_zlim([-axis_length, axis_length])
        
        # 添加坐标轴标签
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
        # 设置视角
        self.ax.view_init(self.elevation, self.azimuth)
        
        # 添加图例
        if self.current_plots:
            self.ax.legend()
            
    def load_data(self):
        """加载数据文件"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            self.lang.get('open'),
            "",
            self.lang.get('file_filter')
        )
        
        if file_name:
            try:
                self.data_reader = AntennaDataReader(file_name)
                self.update_combo_boxes()
                self.current_plots = []  # 清空现有曲线
                self.plot_list.clear()  # 清空曲线列表
                self.statusBar.showMessage(f"Loaded: {file_name}")
                self.plot_saved = True  # 重置保存状态
                
                # 自动添加第一条曲线
                self.add_new_plot()
            except Exception as e:
                QMessageBox.critical(self, self.lang.get('error'),
                                   f"{self.lang.get('file_error')}: {str(e)}")
                
    def update_combo_boxes(self):
        """更新下拉框选项"""
        if not self.data_reader:
            return
            
        # 更新频率选项
        self.freq_combo.clear()
        frequencies = self.data_reader.get_frequencies()
        self.freq_combo.addItems([f"{f} MHz" for f in frequencies])
        
        # 更新极化选项
        self.polarization_combo.clear()
        polarizations = self.data_reader.get_polarizations()
        self.polarization_combo.addItems(polarizations)
        
        # 更新Theta角度选项
        self.theta_combo.clear()
        theta_angles = self.data_reader.get_theta_angles()
        self.theta_combo.addItems([f"{t}°" for t in theta_angles])
        
    def update_title(self):
        """更新图表标题"""
        self.ax.set_title(self.title_edit.text())
        self.canvas.draw()
        
    def save_plot(self):
        """保存图表"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self.lang.get('save'),
            "",
            self.lang.get('image_filter')
        )
        
        if file_name:
            self.figure.savefig(file_name,
                              dpi=self.dpi_spin.value(),
                              bbox_inches='tight')
            self.statusBar.showMessage(f"Saved: {file_name}")
            self.plot_saved = True  # 标记图像已保存
            
    def on_parameter_changed(self):
        """当参数改变时实时更新图表"""
        if self.active_plot_index >= 0 and self.active_plot_index < len(self.current_plots):
            plot = self.current_plots[self.active_plot_index]
            plot.update({
                'freq_idx': self.freq_combo.currentIndex(),
                'polarization': self.polarization_combo.currentText(),
                'theta_idx': self.theta_combo.currentIndex(),
                'line_style': self.line_style_combo.currentText(),
                'line_width': self.line_width_spin.value(),
                'normalized': self.normalize_cb.isChecked()
            })
            self.update_plot()

    def choose_color(self):
        """选择线条颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            if self.active_plot_index >= 0:
                self.current_plots[self.active_plot_index]['color'] = self.current_color
                self.update_plot()
            
    def change_language(self, lang):
        """切换语言"""
        if self.lang.set_language(lang):
            self.settings.setValue('language', lang)
            QMessageBox.information(self, 'Info',
                                  'Please restart the application to apply language changes.')
            
    def change_theme(self, theme):
        """切换主题"""
        self.settings.setValue('theme', theme)
        self.apply_theme(theme)
        
    def apply_theme(self, theme):
        """应用主题"""
        if theme == 'dark':
            plt.style.use('dark_background')
        else:
            plt.style.use('default')
        self.update_plot()
        
    def load_settings(self):
        """加载设置"""
        lang = self.settings.value('language', 'zh')
        self.lang.set_language(lang)
        
        theme = self.settings.value('theme', 'light')
        self.apply_theme(theme) 

    def add_new_plot(self):
        """添加新的曲线"""
        if not self.data_reader:
            return
            
        plot_info = {
            'freq_idx': self.freq_combo.currentIndex(),
            'polarization': self.polarization_combo.currentText(),
            'theta_idx': self.theta_combo.currentIndex(),
            'line_style': self.line_style_combo.currentText(),
            'line_width': self.line_width_spin.value(),
            'color': self.current_color,
            'normalized': self.normalize_cb.isChecked()
        }
        
        self.current_plots.append(plot_info)
        self.plot_list.addItem(f"Plot {len(self.current_plots)}")
        self.plot_list.setCurrentRow(len(self.current_plots) - 1)
        self.update_plot()
        
    def remove_current_plot(self):
        """删除当前选中的曲线"""
        if self.active_plot_index >= 0:
            self.current_plots.pop(self.active_plot_index)
            self.plot_list.takeItem(self.active_plot_index)
            self.update_plot()
            
    def on_plot_selected(self, index):
        """当选择不同曲线时更新控件状态"""
        self.active_plot_index = index
        if index >= 0 and index < len(self.current_plots):
            plot = self.current_plots[index]
            self.freq_combo.setCurrentIndex(plot['freq_idx'])
            self.polarization_combo.setCurrentText(plot['polarization'])
            self.theta_combo.setCurrentIndex(plot['theta_idx'])
            self.line_style_combo.setCurrentText(plot['line_style'])
            self.line_width_spin.setValue(plot['line_width'])
            self.current_color = plot['color']
            self.normalize_cb.setChecked(plot['normalized'])
            self.update_plot() 

    def toggle_db_range(self, state):
        """切换dB范围控制"""
        is_auto = state == Qt.Checked
        self.min_db_spin.setEnabled(not is_auto)
        self.max_db_spin.setEnabled(not is_auto)
        self.update_plot()

    def update_axis_direction(self, direction):
        """更新坐标轴方向"""
        direction_map = {
            'N': 'N',  # 北向上
            'S': 'S',  # 南向上
            'E': 'E',  # 东向上
            'W': 'W'   # 西向上
        }
        if not self.is_3d_view:
            self.ax.set_theta_zero_location(direction_map[direction])
            self.canvas.draw()
            
    def update_axis_angle(self, angle):
        """更新坐标轴角度"""
        if not self.is_3d_view:
            self.ax.set_theta_direction(-1 if angle >= 0 else 1)
            self.ax.set_theta_offset(np.deg2rad(angle))
            self.canvas.draw()
            
    def insert_image(self):
        """插入图片"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            self.lang.get('select_image'),
            "",
            self.lang.get('image_filter_all')
        )
        
        if file_name:
            try:
                # 读取图片
                img = plt.imread(file_name)
                
                # 计算图片的宽高比
                img_ratio = img.shape[1] / img.shape[0]  # width / height
                
                # 设置固定大小为200像素
                target_size = 200  # 像素
                
                # 获取画布的实际像素大小和DPI
                canvas_width = self.canvas.width()
                canvas_height = self.canvas.height()
                dpi = self.figure.dpi
                
                # 计算画布的英寸大小
                canvas_width_inches = canvas_width / dpi
                canvas_height_inches = canvas_height / dpi
                
                # 计算目标大小（英寸）
                if img_ratio > 1:  # 宽图
                    target_width_inches = target_size / dpi
                    target_height_inches = target_width_inches / img_ratio
                else:  # 高图
                    target_height_inches = target_size / dpi
                    target_width_inches = target_height_inches * img_ratio
                
                # 转换为相对大小
                self.image_size = [
                    target_width_inches / canvas_width_inches,
                    target_height_inches / canvas_height_inches
                ]
                
                # 将图片位置设置在画布中央
                self.image_position = [0.5, 0.5]
                
                # 创建或更新图片子图
                if hasattr(self, 'image_ax'):
                    self.figure.delaxes(self.image_ax)
                
                # 创建新的图片子图，设置初始位置和大小
                x = self.image_position[0] - self.image_size[0] / 2
                y = self.image_position[1] - self.image_size[1] / 2
                self.image_ax = self.figure.add_axes([x, y, self.image_size[0], self.image_size[1]])
                self.image_ax.patch.set_alpha(0)  # 设置背景透明
                
                # 连接右键菜单事件
                self.canvas.mpl_connect('button_press_event', self.on_image_right_click)
                
                # 清除并显示图片
                self.image_ax.clear()
                self.image_ax.imshow(img, aspect='equal')  # 使用equal保持原始比例
                self.image_ax.axis('off')
                
                # 保存图片文件路径和数据
                self.current_image = file_name
                self.current_image_data = img
                
                # 将图片子图置于顶层，但在图例之下
                self.image_ax.set_zorder(9)  # 设置较低的zorder
                
                # 更新主图
                self.update_plot()  # 重新绘制主图以确保正确的层级关系
                
            except Exception as e:
                QMessageBox.critical(self, self.lang.get('error'),
                                   f"{self.lang.get('image_error')}: {str(e)}")

    def on_image_right_click(self, event):
        """处理图片右键点击事件"""
        if not hasattr(self, 'image_ax') or not event.inaxes or event.button != 3:  # 3表示右键
            return
            
        # 检查点击是否在图片区域内
        bbox = self.image_ax.get_position()
        x, y = event.x / self.canvas.width(), event.y / self.canvas.height()
        
        if bbox.contains(x, y):
            # 创建右键菜单
            menu = QMenu(self)
            
            # 添加修改大小的动作
            size_action = menu.addAction(self.lang.get('modify_size'))
            size_action.triggered.connect(self.modify_image_size)
            
            # 添加修改位置的动作
            position_action = menu.addAction(self.lang.get('modify_position'))
            position_action.triggered.connect(self.modify_image_position)
            
            # 显示菜单
            menu.exec_(self.canvas.mapToGlobal(event.guiEvent.pos()))

    def modify_image_size(self):
        """修改图片大小"""
        if not hasattr(self, 'image_ax'):
            return
            
        # 获取画布的实际像素大小和DPI
        canvas_width = self.canvas.width()
        canvas_height = self.canvas.height()
        dpi = self.figure.dpi
        
        # 计算当前图片的像素大小
        current_width = self.image_size[0] * canvas_width
        current_height = self.image_size[1] * canvas_height
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lang.get('modify_size'))
        layout = QVBoxLayout(dialog)
        
        # 添加宽度输入
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel(self.lang.get('width')))
        width_spin = QSpinBox()
        width_spin.setRange(10, int(canvas_width * 0.8))  # 限制最大宽度为画布的80%
        width_spin.setValue(int(current_width))
        width_layout.addWidget(width_spin)
        width_layout.addWidget(QLabel('px'))
        layout.addLayout(width_layout)
        
        # 添加高度输入
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel(self.lang.get('height')))
        height_spin = QSpinBox()
        height_spin.setRange(10, int(canvas_height * 0.8))  # 限制最大高度为画布的80%
        height_spin.setValue(int(current_height))
        height_layout.addWidget(height_spin)
        height_layout.addWidget(QLabel('px'))
        layout.addLayout(height_layout)
        
        # 添加保持纵横比的复选框
        aspect_cb = QCheckBox(self.lang.get('keep_aspect_ratio'))
        aspect_cb.setChecked(True)
        layout.addWidget(aspect_cb)
        
        # 计算原始纵横比
        original_ratio = current_width / current_height if current_height > 0 else 1
        
        # 当宽度改变时更新高度（如果保持纵横比）
        def on_width_changed(value):
            if aspect_cb.isChecked():
                height_spin.setValue(int(value / original_ratio))
                
        # 当高度改变时更新宽度（如果保持纵横比）
        def on_height_changed(value):
            if aspect_cb.isChecked():
                width_spin.setValue(int(value * original_ratio))
        
        width_spin.valueChanged.connect(on_width_changed)
        height_spin.valueChanged.connect(on_height_changed)
        
        # 添加确定和取消按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            # 获取新的像素大小
            new_width_pixels = width_spin.value()
            new_height_pixels = height_spin.value()
            
            # 计算画布的英寸大小
            canvas_width_inches = canvas_width / dpi
            canvas_height_inches = canvas_height / dpi
            
            # 将像素转换为英寸
            new_width_inches = new_width_pixels / dpi
            new_height_inches = new_height_pixels / dpi
            
            # 更新相对大小
            self.image_size = [
                new_width_inches / canvas_width_inches,
                new_height_inches / canvas_height_inches
            ]
            
            self.update_image_position()
            self.canvas.draw()

    def modify_image_position(self):
        """修改图片位置"""
        if not hasattr(self, 'image_ax'):
            return
            
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lang.get('modify_position'))
        layout = QVBoxLayout(dialog)
        
        # 添加X坐标输入
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel('X (0-100%):'))
        x_spin = QSpinBox()
        x_spin.setRange(0, 100)
        x_spin.setValue(int(self.image_position[0] * 100))
        x_layout.addWidget(x_spin)
        layout.addLayout(x_layout)
        
        # 添加Y坐标输入
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel('Y (0-100%):'))
        y_spin = QSpinBox()
        y_spin.setRange(0, 100)
        y_spin.setValue(int(self.image_position[1] * 100))
        y_layout.addWidget(y_spin)
        layout.addLayout(y_layout)
        
        # 添加确定和取消按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            # 更新位置
            self.image_position = [x_spin.value() / 100, y_spin.value() / 100]
            self.update_image_position()
            self.canvas.draw()

    def update_image_position(self):
        """更新图片位置和大小"""
        if hasattr(self, 'image_ax') and hasattr(self, 'current_image_data'):
            # 计算图片边界框的坐标
            x = self.image_position[0] - self.image_size[0] / 2
            y = self.image_position[1] - self.image_size[1] / 2
            
            # 设置子图的位置和大小
            self.image_ax.set_position([x, y, self.image_size[0], self.image_size[1]])
            
            # 确保图片在正确的层级
            self.image_ax.set_zorder(9)  # 在曲线下方，在主图上方

    def remove_image(self):
        """移除图片"""
        if hasattr(self, 'image_ax'):
            # 移除图片子图
            self.figure.delaxes(self.image_ax)
            delattr(self, 'image_ax')
            if hasattr(self, 'current_image'):
                delattr(self, 'current_image')
            if hasattr(self, 'current_image_data'):
                delattr(self, 'current_image_data')
            
            # 更新图表
            self.canvas.draw()

    def resizeEvent(self, event):
        """处理窗口大小改变事件"""
        super().resizeEvent(event)
        # 更新图表布局
        if hasattr(self, 'figure'):
            self.figure.tight_layout()
            self.canvas.draw()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 保存窗口大小和位置
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        
        if not self.plot_saved and self.data_reader:  # 只有在有数据且未保存时才提示
            reply = QMessageBox.question(
                self,
                self.lang.get('save'),
                self.lang.get('save_confirm'),
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_plot()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept() 