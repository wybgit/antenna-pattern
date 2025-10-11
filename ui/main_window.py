from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QPushButton, QComboBox, QFileDialog, QLabel,
                                QCheckBox, QSpinBox, QLineEdit, QMenuBar, QMenu,
                                QStatusBar, QToolBar, QStyle, QColorDialog, QMessageBox,
                                QListWidget, QSplitter, QFrame, QScrollArea, QSlider,
                                QDoubleSpinBox, QDialog, QDialogButtonBox, QTabWidget,
                                QGroupBox, QInputDialog)
from PySide6.QtCore import Qt, QSettings, QSize, QTimer
from PySide6.QtGui import QAction, QIcon, QPixmap
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from utils.excel_reader import AntennaDataReader
from utils.language import Language

class MainWindow(QMainWindow):
    def __init__(self, debug=False):
        super().__init__()
        self.lang = Language()
        self.settings = QSettings('AntennaPattern', 'Visualization')
        self.debug_mode = debug
        
        # 数据存储
        self.data_reader = None
        self.current_plots = []  # Store multiple plots
        self.active_plot_index = -1  # Currently selected plot index
        self.plot_saved = True  # 标记图像是否已保存
        
        # 移除3D视图相关功能
        
        # 图片相关
        self.image_dragging = False
        self.image_resizing = False
        self.image_position = [0.5, 0.5]  # 图片中心位置 [x, y] in figure coordinates
        self.image_size = [0.4, 0.4]      # 图片大小 [width, height] in figure coordinates
        self.image_rotation = 0           # 图片旋转角度
        self.drag_start = None
        self.resize_corner = None
        self.resize_start_size = None
        
        # 图表显示设置
        self.show_title = 'show'          # 标题显示: 'show', 'hide'
        self.show_legend = 'show'         # 图例显示: 'show', 'hide'
        self.title_position = 'bottom'    # 标题位置: 'top', 'bottom'
        self.polar_grid_interval = 30     # 极坐标网格间隔: 15, 30, 45
        self.title_size = 12              # 标题字体大小
        self.legend_size = 10             # 图例字体大小
        self.plot_title_text = ''         # 图表标题文本
        
        # 默认颜色和线型列表 - 使用更易区分的颜色
        self.default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
                              '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5']
        self.default_line_styles = ['-', '--', '-.', ':']
        self.plot_counter = 0             # 用于分配默认颜色和线型
        
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
        # 重置2D视图
        self.ax.set_rmax(None)  # 重置半径范围
        self.ax.set_theta_zero_location('S')  # 设置0度位置在南方（下方）
        self.ax.set_theta_direction(-1)  # 设置角度方向为顺时针
        # S方向本身就是0度在下方，180度在上方，无需偏移
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
        
        # 不创建菜单栏和工具栏
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
    # 移除菜单栏和工具栏创建函数

    def create_left_panel(self):
        """创建左侧控制面板"""
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.StyledPanel)
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        
        # 创建各个标签页
        self.create_view_settings_tab()
        self.create_curve_settings_tab()
        self.create_export_settings_tab()
        
        left_layout.addWidget(self.tab_widget)
        self.layout.addWidget(left_panel)
    
    def create_view_settings_tab(self):
        """创建视图设置标签页"""
        view_tab = QWidget()
        view_layout = QVBoxLayout(view_tab)
        
        # 数据导入组
        import_group = QGroupBox(self.lang.get('data_import'))
        import_layout = QVBoxLayout(import_group)
        
        # 导入数据按钮
        import_data_btn = QPushButton(self.lang.get('import_data'))
        import_data_btn.clicked.connect(self.load_data)
        import_layout.addWidget(import_data_btn)
        
        # 导入图片按钮
        import_image_btn = QPushButton(self.lang.get('import_image'))
        import_image_btn.clicked.connect(self.insert_image)
        import_layout.addWidget(import_image_btn)
        
        view_layout.addWidget(import_group)
        
        # 移除视图类型选择组（只保留2D视图）
        
        # 坐标轴设置组
        axis_group = QGroupBox(self.lang.get('axis_settings'))
        axis_layout = QVBoxLayout(axis_group)
        
        # 坐标轴方向
        axis_direction_layout = QHBoxLayout()
        axis_direction_layout.addWidget(QLabel(self.lang.get('axis_direction')))
        self.axis_direction_combo = QComboBox()
        self.axis_direction_combo.addItems(['N', 'S', 'E', 'W'])
        self.axis_direction_combo.setCurrentText('S')
        self.axis_direction_combo.currentTextChanged.connect(self.update_axis_direction)
        axis_direction_layout.addWidget(self.axis_direction_combo)
        axis_layout.addLayout(axis_direction_layout)
        
        # 坐标轴角度
        axis_angle_layout = QHBoxLayout()
        axis_angle_layout.addWidget(QLabel(self.lang.get('axis_angle')))
        self.axis_angle_spin = QDoubleSpinBox()
        self.axis_angle_spin.setRange(-360, 360)
        self.axis_angle_spin.setValue(0)
        self.axis_angle_spin.setSingleStep(15)
        self.axis_angle_spin.valueChanged.connect(self.update_axis_angle)
        axis_angle_layout.addWidget(self.axis_angle_spin)
        axis_layout.addLayout(axis_angle_layout)
        
        view_layout.addWidget(axis_group)
        
        # 2D增益范围控制组
        self.gain_control_group = QGroupBox(self.lang.get('gain_range_2d'))
        gain_control_layout = QVBoxLayout(self.gain_control_group)

        self.auto_gain_cb = QCheckBox(self.lang.get('auto_range'))
        self.auto_gain_cb.setChecked(True)
        self.auto_gain_cb.stateChanged.connect(self.toggle_2d_gain_range)
        gain_control_layout.addWidget(self.auto_gain_cb)

        gain_range_layout = QHBoxLayout()
        self.min_gain_spin = QDoubleSpinBox()
        self.min_gain_spin.setRange(-100, 100)
        self.min_gain_spin.setValue(-40)
        self.min_gain_spin.setEnabled(False)
        self.min_gain_spin.valueChanged.connect(self.update_plot)
        gain_range_layout.addWidget(QLabel("Min:"))
        gain_range_layout.addWidget(self.min_gain_spin)

        self.max_gain_spin = QDoubleSpinBox()
        self.max_gain_spin.setRange(-100, 100)
        self.max_gain_spin.setValue(10)
        self.max_gain_spin.setEnabled(False)
        self.max_gain_spin.valueChanged.connect(self.update_plot)
        gain_range_layout.addWidget(QLabel("Max:"))
        gain_range_layout.addWidget(self.max_gain_spin)
        gain_control_layout.addLayout(gain_range_layout)

        gain_steps_layout = QHBoxLayout()
        gain_steps_layout.addWidget(QLabel(self.lang.get('gain_steps')))
        self.gain_steps_spin = QSpinBox()
        self.gain_steps_spin.setRange(2, 20)
        self.gain_steps_spin.setValue(5)
        self.gain_steps_spin.setEnabled(False)
        self.gain_steps_spin.valueChanged.connect(self.update_plot)
        gain_steps_layout.addWidget(self.gain_steps_spin)
        gain_control_layout.addLayout(gain_steps_layout)

        # 2D增益刻度位置控制
        gain_label_angle_layout = QHBoxLayout()
        gain_label_angle_layout.addWidget(QLabel(self.lang.get('gain_label_angle')))
        self.gain_label_angle_spin = QDoubleSpinBox()
        self.gain_label_angle_spin.setRange(-360, 360)
        self.gain_label_angle_spin.setValue(0)
        self.gain_label_angle_spin.setSingleStep(15)
        self.gain_label_angle_spin.valueChanged.connect(self.update_gain_label_angle)
        gain_label_angle_layout.addWidget(self.gain_label_angle_spin)
        gain_control_layout.addLayout(gain_label_angle_layout)
        
        view_layout.addWidget(self.gain_control_group)
        
        # 显示设置组
        display_group = QGroupBox(self.lang.get('display_settings'))
        display_layout = QVBoxLayout(display_group)
        
        # 图表标题设置
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel(self.lang.get('plot_title')))
        self.title_edit = QLineEdit()
        self.title_edit.setMinimumHeight(30)
        self.title_edit.setPlaceholderText(self.lang.get('plot_title'))
        self.title_edit.textChanged.connect(self.update_title_text)
        title_layout.addWidget(self.title_edit)
        display_layout.addLayout(title_layout)
        
        # 标题显示控制
        title_show_layout = QHBoxLayout()
        title_show_layout.addWidget(QLabel(self.lang.get('show_title')))
        self.show_title_combo = QComboBox()
        self.show_title_combo.addItems([self.lang.get('show'), self.lang.get('hide')])
        self.show_title_combo.currentTextChanged.connect(self.toggle_title_display)
        title_show_layout.addWidget(self.show_title_combo)
        display_layout.addLayout(title_show_layout)
        
        # 标题位置控制
        title_pos_layout = QHBoxLayout()
        title_pos_layout.addWidget(QLabel(self.lang.get('title_position')))
        self.title_position_combo = QComboBox()
        self.title_position_combo.addItems([self.lang.get('bottom'), self.lang.get('top')])
        self.title_position_combo.currentTextChanged.connect(self.change_title_position)
        title_pos_layout.addWidget(self.title_position_combo)
        display_layout.addLayout(title_pos_layout)
        
        # 标题大小控制
        title_size_layout = QHBoxLayout()
        title_size_layout.addWidget(QLabel(self.lang.get('title_size')))
        self.title_size_spin = QSpinBox()
        self.title_size_spin.setRange(8, 24)
        self.title_size_spin.setValue(12)
        self.title_size_spin.valueChanged.connect(self.change_title_size)
        title_size_layout.addWidget(self.title_size_spin)
        display_layout.addLayout(title_size_layout)
        
        # 图例显示控制
        legend_show_layout = QHBoxLayout()
        legend_show_layout.addWidget(QLabel(self.lang.get('show_legend')))
        self.show_legend_combo = QComboBox()
        self.show_legend_combo.addItems([self.lang.get('show'), self.lang.get('hide')])
        self.show_legend_combo.currentTextChanged.connect(self.toggle_legend_display)
        legend_show_layout.addWidget(self.show_legend_combo)
        display_layout.addLayout(legend_show_layout)
        
        # 图例大小控制
        legend_size_layout = QHBoxLayout()
        legend_size_layout.addWidget(QLabel(self.lang.get('legend_size')))
        self.legend_size_spin = QSpinBox()
        self.legend_size_spin.setRange(6, 18)
        self.legend_size_spin.setValue(10)
        self.legend_size_spin.valueChanged.connect(self.change_legend_size)
        legend_size_layout.addWidget(self.legend_size_spin)
        display_layout.addLayout(legend_size_layout)
        
        # 极坐标网格间隔控制
        grid_interval_layout = QHBoxLayout()
        grid_interval_layout.addWidget(QLabel(self.lang.get('polar_grid_interval')))
        self.grid_interval_combo = QComboBox()
        self.grid_interval_combo.addItems([self.lang.get('degrees_15'), self.lang.get('degrees_30'), self.lang.get('degrees_45')])
        self.grid_interval_combo.setCurrentText(self.lang.get('degrees_30'))
        self.grid_interval_combo.currentTextChanged.connect(self.change_grid_interval)
        grid_interval_layout.addWidget(self.grid_interval_combo)
        display_layout.addLayout(grid_interval_layout)
        
        view_layout.addWidget(display_group)
        
        # 添加弹性空间
        view_layout.addStretch()
        
        self.tab_widget.addTab(view_tab, self.lang.get('view_settings'))
    
    def create_curve_settings_tab(self):
        """创建曲线添加和设置标签页"""
        curve_tab = QWidget()
        curve_layout = QVBoxLayout(curve_tab)
        
        # 曲线列表组
        curve_list_group = QGroupBox(self.lang.get('curves'))
        curve_list_layout = QVBoxLayout(curve_list_group)
        
        self.plot_list = QListWidget()
        self.plot_list.setMinimumHeight(150)
        self.plot_list.currentRowChanged.connect(self.on_plot_selected)
        curve_list_layout.addWidget(self.plot_list)
        
        # 曲线控制按钮
        curve_btn_layout = QHBoxLayout()
        add_curve_btn = QPushButton(self.lang.get('add_plot'))
        add_curve_btn.clicked.connect(self.add_new_plot)
        remove_curve_btn = QPushButton(self.lang.get('remove_plot'))
        remove_curve_btn.clicked.connect(self.remove_current_plot)
        curve_btn_layout.addWidget(add_curve_btn)
        curve_btn_layout.addWidget(remove_curve_btn)
        curve_list_layout.addLayout(curve_btn_layout)
        
        curve_layout.addWidget(curve_list_group)
        
        # 数据参数组
        param_group = QGroupBox(self.lang.get('data_parameters'))
        param_layout = QVBoxLayout(param_group)
        
        # 频率选择
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel(self.lang.get('frequency')))
        self.freq_combo = QComboBox()
        self.freq_combo.setMinimumHeight(30)
        self.freq_combo.currentIndexChanged.connect(self.on_parameter_changed)
        freq_layout.addWidget(self.freq_combo)
        param_layout.addLayout(freq_layout)
        
        # 极化选择
        pol_layout = QHBoxLayout()
        pol_layout.addWidget(QLabel(self.lang.get('polarization')))
        self.polarization_combo = QComboBox()
        self.polarization_combo.setMinimumHeight(30)
        self.polarization_combo.currentIndexChanged.connect(self.on_parameter_changed)
        pol_layout.addWidget(self.polarization_combo)
        param_layout.addLayout(pol_layout)
        
        # 切面类型选择
        plane_type_layout = QHBoxLayout()
        plane_type_layout.addWidget(QLabel(self.lang.get('plane_type')))
        self.plane_type_combo = QComboBox()
        self.plane_type_combo.setMinimumHeight(30)
        self.plane_type_combo.addItems(['垂直(Phi)', '水平(Theta)'])
        self.plane_type_combo.setCurrentIndex(0)  # 默认选择垂直(Phi)
        self.plane_type_combo.currentIndexChanged.connect(self.on_plane_type_changed)
        plane_type_layout.addWidget(self.plane_type_combo)
        param_layout.addLayout(plane_type_layout)
        
        # 切面角度选择
        plane_angle_layout = QHBoxLayout()
        plane_angle_layout.addWidget(QLabel(self.lang.get('plane_angle')))
        self.plane_angle_combo = QComboBox()
        self.plane_angle_combo.setMinimumHeight(30)
        angles = [str(i) for i in range(0, 180, 5)]  # 0到175度，步进5度
        self.plane_angle_combo.addItems(angles)
        self.plane_angle_combo.currentIndexChanged.connect(self.on_parameter_changed)
        plane_angle_layout.addWidget(self.plane_angle_combo)
        param_layout.addLayout(plane_angle_layout)
        
        # 归一化选择
        self.normalize_cb = QCheckBox(self.lang.get('normalize'))
        self.normalize_cb.stateChanged.connect(self.on_parameter_changed)
        param_layout.addWidget(self.normalize_cb)
        
        curve_layout.addWidget(param_group)
        
        # 曲线样式组
        style_group = QGroupBox(self.lang.get('curve_style'))
        style_layout = QVBoxLayout(style_group)
        
        # 线型选择
        line_style_layout = QHBoxLayout()
        line_style_layout.addWidget(QLabel(self.lang.get('line_style')))
        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(['-', '--', ':', '-.'])
        self.line_style_combo.currentTextChanged.connect(self.on_parameter_changed)
        line_style_layout.addWidget(self.line_style_combo)
        style_layout.addLayout(line_style_layout)
        
        # 线宽选择
        line_width_layout = QHBoxLayout()
        line_width_layout.addWidget(QLabel(self.lang.get('line_width')))
        self.line_width_spin = QSpinBox()
        self.line_width_spin.setRange(1, 10)
        self.line_width_spin.setValue(2)
        self.line_width_spin.valueChanged.connect(self.on_parameter_changed)
        line_width_layout.addWidget(self.line_width_spin)
        style_layout.addLayout(line_width_layout)
        
        # 颜色选择
        color_btn = QPushButton(self.lang.get('line_color'))
        color_btn.clicked.connect(self.choose_color)
        style_layout.addWidget(color_btn)
        self.current_color = 'blue'
        
        curve_layout.addWidget(style_group)
        
        # Show Data button
        self.show_data_btn = QPushButton(self.lang.get('show_data'))
        self.show_data_btn.clicked.connect(self.show_data_table)
        curve_layout.addWidget(self.show_data_btn)
        
        # 添加弹性空间
        curve_layout.addStretch()
        
        self.tab_widget.addTab(curve_tab, self.lang.get('curve_settings'))
    
    def create_export_settings_tab(self):
        """创建图片导出设置标签页"""
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        
        # 导出设置组
        export_settings_group = QGroupBox(self.lang.get('export_settings'))
        export_settings_layout = QVBoxLayout(export_settings_group)
        
        # DPI设置
        dpi_layout = QHBoxLayout()
        dpi_layout.addWidget(QLabel(self.lang.get('dpi')))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setMinimumHeight(30)
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)
        dpi_layout.addWidget(self.dpi_spin)
        export_settings_layout.addLayout(dpi_layout)
        
        # 保存按钮
        save_btn = QPushButton(self.lang.get('save_plot'))
        save_btn.clicked.connect(self.save_plot)
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        export_settings_layout.addWidget(save_btn)
        
        export_layout.addWidget(export_settings_group)
        
        # 添加弹性空间
        export_layout.addStretch()
        
        self.tab_widget.addTab(export_tab, self.lang.get('export_settings'))

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
        
        # 连接键盘事件
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # 设置画布可以接收焦点和键盘事件
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        
        self.layout.addWidget(right_panel, stretch=1)
        
        # 初始化为2D极坐标视图
        self.ax = self.figure.add_subplot(111, projection='polar')
        self.ax.set_theta_zero_location('S')  # 设置0度位置在南方（下方）
        self.ax.set_theta_direction(-1)  # 设置角度方向为顺时针
        # S方向本身就是0度在下方，180度在上方，无需偏移
        self.ax.grid(True)
        self.canvas.draw()

    def on_mouse_press(self, event):
        """处理鼠标按下事件"""
        # 设置画布焦点以接收键盘事件
        self.canvas.setFocus()
        
        if not hasattr(self, 'image_ax') or not hasattr(self, 'current_image_data'):
            if self.debug_mode:
                print("DEBUG: No image_ax or current_image_data.")
            return
            
        # 获取鼠标在Figure坐标系中的位置
        x_fig, y_fig = self.figure.transFigure.inverted().transform((event.x, event.y))
        
        # 获取当前图片的边界（Figure坐标系）
        bbox_fig = self.image_ax.get_position()
        
        if self.debug_mode:
            print(f"DEBUG: Mouse Press - x_fig={x_fig:.4f}, y_fig={y_fig:.4f}, button={event.button}, inaxes={event.inaxes}")
            print(f"DEBUG: Image BBox (Figure) - x0={bbox_fig.x0:.4f}, y0={bbox_fig.y0:.4f}, x1={bbox_fig.x1:.4f}, y1={bbox_fig.y1:.4f}")

        # 检查是否在图片边界��
        if bbox_fig.contains(x_fig, y_fig):
            if self.debug_mode:
                print("DEBUG: Mouse press is within image bbox.")
            # 计算调整大小角落的大小（像素转换为Figure坐标）
            corner_pixel_size = 15  # 像素
            pixel_to_figure_transform = self.figure.transFigure.inverted()
            p0_fig = pixel_to_figure_transform.transform((0, 0))
            p_corner_fig = pixel_to_figure_transform.transform((corner_pixel_size, corner_pixel_size))
            corner_size_x = p_corner_fig[0] - p0_fig[0]
            corner_size_y = p_corner_fig[1] - p0_fig[1]

            # 检查是否在右下角调整大小区域
            is_in_resize_corner = (x_fig > bbox_fig.x1 - corner_size_x and 
                                   y_fig < bbox_fig.y0 + corner_size_y)
            if self.debug_mode:
                print(f"DEBUG: Is in resize corner: {is_in_resize_corner}")

            if event.button == 1:  # 左键点击
                if is_in_resize_corner:
                    self.image_resizing = True
                    self.resize_start_size = self.image_size.copy()
                    self.resize_corner = [x_fig, y_fig]
                    self.canvas.setCursor(Qt.SizeFDiagCursor)
                    if self.debug_mode:
                        print("DEBUG: Started image resizing.")
                else:
                    self.image_dragging = True
                    self.drag_start = [x_fig - self.image_position[0], y_fig - self.image_position[1]]
                    self.canvas.setCursor(Qt.ClosedHandCursor)
                    if self.debug_mode:
                        print("DEBUG: Started image dragging.")
            elif event.button == 3:  # 右键点击
                self.on_image_right_click(event)
                if self.debug_mode:
                    print("DEBUG: Right-clicked on image.")
        else:
            if self.debug_mode:
                print("DEBUG: Mouse press is OUTSIDE image bbox.")
        
    def on_mouse_release(self, event):
        """处理鼠标释放事件"""
        self.image_dragging = False
        self.image_resizing = False
        self.drag_start = None
        self.resize_corner = None
        self.resize_start_size = None
        self.canvas.setCursor(Qt.ArrowCursor)  # 恢复默认光标
        
    def on_key_press(self, event):
        """处理键盘按键事件"""
        pass
            
    def on_image_right_click(self, event):
        """处理图片上的右键点击事件，显示上下文菜单"""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QCursor
        
        # 创建右键菜单
        menu = QMenu(self)
        
        # 添加修改大小的动作
        size_action = menu.addAction(self.lang.get('modify_size'))
        size_action.triggered.connect(self.modify_image_size)
        
        # 添加修改位置的动作
        position_action = menu.addAction(self.lang.get('modify_position'))
        position_action.triggered.connect(self.modify_image_position)
        
        # 添加旋转图片的动作
        rotate_action = menu.addAction(self.lang.get('rotate_image'))
        rotate_action.triggered.connect(self.rotate_image_90)
        
        # 添加分隔线
        menu.addSeparator()
        
        # 添加删除图片的动作
        delete_action = menu.addAction(self.lang.get('delete_image'))
        delete_action.triggered.connect(self.remove_image)
        
        # 显示菜单
        menu.exec_(QCursor.pos())
        
    def on_mouse_move(self, event):
        """处理鼠标移动事件"""
        if not hasattr(self, 'image_ax') or not hasattr(self, 'current_image_data'):
            if self.debug_mode:
                print("DEBUG: Mouse Move - No image_ax or current_image_data.")
            return
            
        # 获取鼠标在Figure坐标系中的位置
        if event.x is None or event.y is None:
            return
        x_fig, y_fig = self.figure.transFigure.inverted().transform((event.x, event.y))
        if self.debug_mode:
            print(f"DEBUG: Mouse Move - x_fig={x_fig:.4f}, y_fig={y_fig:.4f}, dragging={self.image_dragging}, resizing={self.image_resizing}")

        if self.image_dragging and self.drag_start:
            # 更新图片位置
            new_x = x_fig - self.drag_start[0]
            new_y = y_fig - self.drag_start[1]
            
            # 限制图片不超出画布范围 (Figure coordinates are 0-1)
            new_x = max(self.image_size[0]/2, min(new_x, 1 - self.image_size[0]/2))
            new_y = max(self.image_size[1]/2, min(new_y, 1 - self.image_size[1]/2))
            
            self.image_position = [new_x, new_y]
            self.update_image_position()
            self.canvas.draw()
            if self.debug_mode:
                print(f"DEBUG: Image dragged to position: {self.image_position}")
            
        elif self.image_resizing and self.resize_corner and self.resize_start_size:
            # 计算鼠标移动的距离
            dx = x_fig - self.resize_corner[0]
            dy = y_fig - self.resize_corner[1]
            
            # 保持原始宽高比
            original_ratio = self.resize_start_size[0] / self.resize_start_size[1]
            
            # 根据鼠标移动距离计算新尺寸
            # 使用较大的移动距离来确定缩放
            scale_factor = 1.0 + max(dx, -dy) * 2  # 向右或向上拖拽增大，向左或向下拖拽缩小
            
            new_width_fig = self.resize_start_size[0] * scale_factor
            new_height_fig = self.resize_start_size[1] * scale_factor
            
            # 设置最小和最大尺寸限制
            pixel_to_figure_transform = self.figure.transFigure.inverted()
            p0_fig = pixel_to_figure_transform.transform((0, 0))
            
            # 最小尺寸：50像素
            min_size_pixels = 50
            p_min_size_fig = pixel_to_figure_transform.transform((min_size_pixels, min_size_pixels))
            min_size_fig_x = p_min_size_fig[0] - p0_fig[0]
            min_size_fig_y = p_min_size_fig[1] - p0_fig[1]

            # 最大尺寸：画布的70%
            max_width_fig = 0.7
            max_height_fig = 0.7
            
            # 应用尺寸限制
            new_width_fig = max(min_size_fig_x, min(new_width_fig, max_width_fig))
            new_height_fig = max(min_size_fig_y, min(new_height_fig, max_height_fig))
            
            # 确保保持宽高比
            if new_width_fig / original_ratio > new_height_fig:
                new_width_fig = new_height_fig * original_ratio
            else:
                new_height_fig = new_width_fig / original_ratio
            
            self.image_size = [new_width_fig, new_height_fig]
            
            self.update_image_position()
            self.canvas.draw()
            if self.debug_mode:
                print(f"DEBUG: Image resized to: {self.image_size}")
            
        # 更新鼠标样式
        if not self.image_dragging and not self.image_resizing and hasattr(self, 'image_ax'):
            bbox_fig = self.image_ax.get_position()
            # 计算调整大小角落的大小
            corner_pixel_size = 15  # 像素
            pixel_to_figure_transform = self.figure.transFigure.inverted()
            p0_fig = pixel_to_figure_transform.transform((0, 0))
            p_corner_fig = pixel_to_figure_transform.transform((corner_pixel_size, corner_pixel_size))
            corner_size_x = p_corner_fig[0] - p0_fig[0]
            corner_size_y = p_corner_fig[1] - p0_fig[1]

            if bbox_fig.contains(x_fig, y_fig):
                # 检查是否在右下角调整大小区域
                if (x_fig > bbox_fig.x1 - corner_size_x and 
                    y_fig < bbox_fig.y0 + corner_size_y):
                    self.canvas.setCursor(Qt.SizeFDiagCursor)  # 调整大小的光标
                else:
                    self.canvas.setCursor(Qt.OpenHandCursor)  # 拖动的光标
            else:
                self.canvas.setCursor(Qt.ArrowCursor)  # 默认光标

    def switch_view(self, index):
        """切换2D/3D视图"""
        self.is_3d_view = index == 1
        self.d3_controls.setVisible(self.is_3d_view)
        self.d3_data_range_group.setVisible(self.is_3d_view)
        # 2D增益范围控制组始终可见
        
        # 清除当前图形并创建新的子图
        self.figure.clear()
        
        if self.is_3d_view:
            self.ax = self.figure.add_subplot(111, projection='3d')
        else:
            self.ax = self.figure.add_subplot(111, projection='polar')
            self.ax.set_theta_zero_location('S')  # 设置0度位置在南方（下方）
            self.ax.set_theta_direction(-1)  # 设置角度方向为顺时针
            # S方向本身就是0度在下方，180度在上方，无需偏移
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
        
    # 移除所有3D视图相关方法

    def update_plot(self):
        """更新图表"""
        if not self.data_reader:
            return
            
        if not hasattr(self, 'ax'):
            # 如果ax不存在，创建一个新的
            self.figure.clear()
            self.ax = self.figure.add_subplot(111, projection='polar')
            self.ax.set_theta_zero_location('S')  # 设置0度位置在南方（下方）
            self.ax.set_theta_direction(-1)  # 设置角度方向为顺时针
            # S方向本身就是0度在下方，180度在上方，无需偏移
            self.ax.grid(True)
        else:
            self.ax.clear()
        
        # 确保主图在最底层
        self.ax.set_zorder(1)
        self.ax.patch.set_alpha(0)  # 设置背景透明
        
        # 只使用2D视图
        self.update_2d_plot()
            
        # 如果有图片，重新设置其位置和大小
        if hasattr(self, 'image_ax') and hasattr(self, 'current_image_data'):
            self.update_image_position()
            
        # 更新标题
        self.update_title()
        
        # 确保图例在最顶层
        if hasattr(self.ax, 'legend_') and self.ax.legend_ is not None:
            self.ax.legend_.set_zorder(10)
        
        self.canvas.draw()
        self.plot_saved = False  # 标记图像未保存

    def update_2d_plot(self):
        """更新2D极坐标图"""
        all_gains = []
        # 绘制所有曲线
        for i, plot in enumerate(self.current_plots):
            # 使用每条曲线自己的参数，而不是当前UI控件的值
            plane_type = plot['plane_type']
            plane_angle = plot['plane_angle']
            
            if plane_type == '水平(Theta)':
                # Theta切面：固定phi角度，theta从-180到180度
                phi_angle = plane_angle
                theta_angles = np.array(self.data_reader.get_theta_angles())
                gains = self.data_reader.get_gain_data_theta_cut(plot['freq_idx'], phi_angle, plot['polarization'])
            else:
                # Phi切面：固定theta角度，phi从0到360度
                theta_angle = plane_angle
                phi_angles = np.array(self.data_reader.get_phi_angles())
                gains = self.data_reader.get_gain_data_phi_cut(plot['freq_idx'], theta_angle, plot['polarization'])
            
            if gains is None:
                continue
                
            # 归一化处理
            if plot['normalized']:
                gains = self.data_reader.normalize_data(gains)

            # 创建完整的360度数据
            if plane_type == '水平(Theta)':
                # 检查数据格式
                if hasattr(self.data_reader, 'file_format') and self.data_reader.file_format == 'matrix':
                    # 矩阵格式：数据已经是完整的360度范围
                    full_angles = theta_angles
                    full_gains = gains
                    
                    # 按角度排序（如果需要）
                    sort_idx = np.argsort(full_angles)
                    full_angles = full_angles[sort_idx]
                    full_gains = full_gains[sort_idx]
                else:
                    # 传统格式：get_gain_data_theta_cut已经返回了拼接后的数据
                    # 需要创建对应的角度数组
                    full_gains = gains
                    full_angles = np.concatenate([theta_angles, theta_angles + 180])
                    
                    # 确保角度在-180到180度范围内
                    full_angles = np.where(full_angles > 180, full_angles - 360, full_angles)
                    full_angles = np.where(full_angles < -180, full_angles + 360, full_angles)
                    
                    # 按角度排序
                    sort_idx = np.argsort(full_angles)
                    full_angles = full_angles[sort_idx]
                    full_gains = full_gains[sort_idx]
                
                # 转换角度为弧度
                angles_rad = self.data_reader.get_angles_in_radians(full_angles)
                label = f"{plot['freq_text']}, {plot['polarization']}, φ={int(round(plane_angle))}°"
            else:
                # Phi切面处理
                if hasattr(self.data_reader, 'file_format') and self.data_reader.file_format == 'matrix':
                    # 矩阵格式：扩展phi数据到360度（镜像对称）
                    full_angles = np.concatenate([phi_angles, phi_angles + 180])
                    full_gains = np.concatenate([gains, gains])
                else:
                    # 传统格式：已经是完整数据
                    full_angles = phi_angles
                    full_gains = gains
                
                # 转换角度为弧度
                angles_rad = self.data_reader.get_angles_in_radians(full_angles)
                label = f"{plot['freq_text']}, {plot['polarization']}, θ={int(round(plane_angle))}°"
            
            # 为了闭合图形，将第一个点追加到末尾
            angles_rad = np.append(angles_rad, angles_rad[0])
            full_gains = np.append(full_gains, full_gains[0])

            all_gains.append(full_gains)

            # 绘制方向图
            self.ax.plot(angles_rad, full_gains,
                        linestyle=plot['line_style'],
                        linewidth=plot['line_width'],
                        color=plot['color'],
                        label=label,
                        zorder=5)  # 确保曲线在图片上方
                        
        # 应用坐标轴设置 - 默认180度朝上，0度朝下
        self.ax.set_theta_zero_location('S')  # 设置0度位置在南方（下方）
        self.ax.set_theta_direction(-1)  # 设置角度方向为顺时针
        # S方向本身就是0度在下方，180度在上方，无需偏移
        self.ax.grid(True)
        
        # 设置刻度标签（根据网格间隔设置）
        if self.polar_grid_interval == 15:
            tick_angles = np.arange(0, 360, 15)
        elif self.polar_grid_interval == 30:
            tick_angles = np.arange(0, 360, 30)
        elif self.polar_grid_interval == 45:
            tick_angles = np.arange(0, 360, 45)
        else:
            tick_angles = np.arange(0, 360, 30)  # 默认30度
            
        self.ax.set_xticks(np.deg2rad(tick_angles))
        self.ax.set_xticklabels([f'{int(angle)}°' for angle in tick_angles])
        
        # 添加图例并设置位置（如果启用）
        if self.current_plots and self.show_legend == 'show':
            # 根据曲线数量和图例大小动态调整图例位置
            num_curves = len(self.current_plots)
            
            # 计算最佳图例位置
            if num_curves <= 3:
                # 少量曲线时放在右上角
                bbox_x = 1.02 + self.legend_size * 0.01
                bbox_y = 1.0
                loc = 'upper left'
            else:
                # 多条曲线时放在右侧中间位置
                bbox_x = 1.02 + self.legend_size * 0.01
                bbox_y = 0.5
                loc = 'center left'
            
            # 确保图例不会超出画布范围
            bbox_x = min(bbox_x, 1.4)
            
            legend = self.ax.legend(loc=loc, bbox_to_anchor=(bbox_x, bbox_y), 
                                  fontsize=self.legend_size, frameon=True, 
                                  fancybox=True, shadow=True)
            legend.set_zorder(10)  # 确保图例在最顶层
            
            # 动态调整子图右边距以适应图例
            legend_width = 0.15 + self.legend_size * 0.01 + num_curves * 0.02
            self.figure.subplots_adjust(right=1.0 - legend_width)
        else:
            # 没有图例时恢复默认右边距
            self.figure.subplots_adjust(right=0.95)

        # 设置增益刻度
        if not self.auto_gain_cb.isChecked():
            # 手动范围模式
            min_gain = self.min_gain_spin.value()
            max_gain = self.max_gain_spin.value()
            steps = self.gain_steps_spin.value()
            self.ax.set_rlim(min_gain, max_gain)
            self.ax.set_rticks(np.linspace(min_gain, max_gain, steps))
        else:
            # 自动范围模式
            if all_gains:
                combined_gains = np.concatenate(all_gains)
                global_min_gain = np.nanmin(combined_gains)
                global_max_gain = np.nanmax(combined_gains)

                if np.isfinite(global_min_gain) and np.isfinite(global_max_gain):
                    # 将范围近似到5的倍数
                    nice_min = np.floor(global_min_gain / 5) * 5
                    nice_max = np.ceil(global_max_gain / 5) * 5

                    if nice_min == nice_max:
                        nice_max += 5 # 如果最大最小值相等，则增加一点范围

                    # 设置刻度步长
                    step = 5
                    num_ticks = (nice_max - nice_min) / step
                    if num_ticks > 15: # 避免刻度过于密集
                        step = 10
                    elif num_ticks > 30:
                        step = 20
                    
                    ticks = np.arange(nice_min, nice_max + 1, step)
                    
                    self.ax.set_rlim(nice_min, nice_max)
                    self.ax.set_rticks(ticks)
        
        # 更新增益刻度标签位置
        self.update_gain_label_angle()

    def update_gain_label_angle(self, angle=None):
        """更新2D视图增益刻度标签的角度"""
        if hasattr(self, 'ax'):
            if angle is None:
                angle = self.gain_label_angle_spin.value()
            self.ax.set_rlabel_position(angle)
            self.canvas.draw()

    # 移除update_3d_plot方法
        
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
                sheet_to_load = None
                # 检查是否为Excel文件并获取工作表名称
                if file_name.lower().endswith(('.xls', '.xlsx')):
                    import pandas as pd
                    xls = pd.ExcelFile(file_name)
                    sheet_names = xls.sheet_names
                    
                    if len(sheet_names) > 1:
                        # 弹出对话框让用户选择
                        sheet_name, ok = QInputDialog.getItem(self, 
                            self.lang.get('select_sheet'), 
                            self.lang.get('which_sheet_to_load'), 
                            sheet_names, 0, False)
                        
                        if ok and sheet_name:
                            sheet_to_load = sheet_name
                        else:
                            # 如果用户取消选择，则中止加��
                            self.statusBar.showMessage("Data loading cancelled.")
                            return
                    elif len(sheet_names) == 1:
                        # 如果只有一个sheet，则直接加载
                        sheet_to_load = sheet_names[0]

                # 使用选定的工作表初始化DataReader
                self.data_reader = AntennaDataReader(file_name, debug=True, sheet_name=sheet_to_load)
                
                self.update_combo_boxes()
                self.current_plots = []  # 清空现有曲线
                self.plot_list.clear()  # 清空曲线列表
                self.statusBar.showMessage(f"Loaded: {file_name} (Sheet: {sheet_to_load or 'Default'})")
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
        
        # 更新切面角度选项
        self.update_plane_angle_options()
        
    def on_plane_type_changed(self):
        """当切面类型改变时更新切面角度选项"""
        self.update_plane_angle_options()
        self.on_parameter_changed()
        
    def update_plane_angle_options(self):
        """根据切面类型和数据更新切面角度选项"""
        if not self.data_reader:
            return
            
        # 保存当前选择的角度
        current_angle = self.plane_angle_combo.currentText()
        
        # 临时断开信号连接以避免递归
        self.plane_angle_combo.currentIndexChanged.disconnect()
        
        try:
            # 清空现有选项
            self.plane_angle_combo.clear()
            
            plane_type = self.plane_type_combo.currentText()
            
            if plane_type == '水平(Theta)':
                # 当切面类型为Theta时，切面角度的档位和Phi的取值一致
                phi_angles = self.data_reader.get_phi_angles()
                # 只取大于等于0的值
                valid_angles = [angle for angle in phi_angles if angle >= 0]
                angle_options = [str(int(round(angle))) for angle in sorted(valid_angles)]
            else:  # plane_type == '垂直(Phi)'
                # 当切面类型为Phi时，切面角度和Theta取值一致
                theta_angles = self.data_reader.get_theta_angles()
                # 只取大于等于0的值
                valid_angles = [angle for angle in theta_angles if angle >= 0]
                angle_options = [str(int(round(angle))) for angle in sorted(valid_angles)]
            
            # 添加选项到下拉框
            if angle_options:
                self.plane_angle_combo.addItems(angle_options)
                
                # 尝试恢复之前的选择
                if current_angle in angle_options:
                    self.plane_angle_combo.setCurrentText(current_angle)
                else:
                    # 如果之前的选择不在新选项中，选择第一个
                    self.plane_angle_combo.setCurrentIndex(0)
            else:
                # 如果没有有效角度，添加默认选项
                self.plane_angle_combo.addItems(['15', '30', '45', '60', '90'])
                
        except Exception as e:
            # 如果出错，使用默认角度选项
            default_angles = [str(i) for i in range(5, 180, 5)]  # 5到175度，步进5度，排除0
            self.plane_angle_combo.addItems(default_angles)
    
    def update_plane_angle_options_for_curve(self, target_angle):
        """为特定曲线更新切面角度选项，确保目标角度始终可用"""
        if not self.data_reader:
            return
            
        # 临时断开信号连接以避免递归
        try:
            self.plane_angle_combo.currentIndexChanged.disconnect()
        except:
            pass
        
        try:
            # 清空现有选项
            self.plane_angle_combo.clear()
            
            plane_type = self.plane_type_combo.currentText()
            
            if plane_type == '水平(Theta)':
                # 当切面类型为Theta时，切面角度的档位和Phi的取值一致
                phi_angles = self.data_reader.get_phi_angles()
                # 只取大于等于0的值
                valid_angles = [angle for angle in phi_angles if angle >= 0]
                angle_options = [str(int(round(angle))) for angle in sorted(valid_angles)]
            else:  # plane_type == '垂直(Phi)'
                # 当切面类型为Phi时，切面角度和Theta取值一致
                theta_angles = self.data_reader.get_theta_angles()
                # 只取大于等于0的值
                valid_angles = [angle for angle in theta_angles if angle >= 0]
                angle_options = [str(int(round(angle))) for angle in sorted(valid_angles)]
            
            # 确保目标角度在选项中
            target_angle_str = str(int(target_angle))
            if target_angle_str not in angle_options:
                angle_options.append(target_angle_str)
                # 重新排序
                angle_options = sorted(angle_options, key=lambda x: int(x))
            
            # 添加选项到下拉框
            if angle_options:
                self.plane_angle_combo.addItems(angle_options)
                # 设置为目标角度
                self.plane_angle_combo.setCurrentText(target_angle_str)
            else:
                # 如果没有有效角度，添加默认选项包括目标角度
                default_angles = ['15', '30', '45', '60', '90']
                if target_angle_str not in default_angles:
                    default_angles.append(target_angle_str)
                    default_angles = sorted(default_angles, key=lambda x: int(x))
                self.plane_angle_combo.addItems(default_angles)
                self.plane_angle_combo.setCurrentText(target_angle_str)
                
        except Exception as e:
            # 如果出错，使用默认角度选项，但确保包含目标角度
            default_angles = [str(i) for i in range(5, 180, 5)]  # 5到175度，步进5度，排除0
            target_angle_str = str(int(target_angle))
            if target_angle_str not in default_angles:
                default_angles.append(target_angle_str)
                default_angles = sorted(default_angles, key=lambda x: int(x))
            self.plane_angle_combo.addItems(default_angles)
            self.plane_angle_combo.setCurrentText(target_angle_str)
        finally:
            # 重新连接信号
            try:
                self.plane_angle_combo.currentIndexChanged.connect(self.on_parameter_changed)
            except:
                pass
        
    def update_title(self):
        """更新图表标题"""
        if self.show_title == 'show' and self.title_edit.text():
            if self.title_position == 'bottom':
                # 在底部显示标题
                self.ax.set_title('')  # 清除顶部标题
                # 根据标题大小动态调整位置
                title_y_pos = max(0.02, 0.08 - self.title_size * 0.003)
                self.figure.suptitle(self.title_edit.text(), y=title_y_pos, fontsize=self.title_size)
                # 动态调整子图位置以适应标题
                self.figure.subplots_adjust(bottom=0.15 + self.title_size * 0.005)
            else:
                # 在顶部显示标题
                self.figure.suptitle('')  # 清除底部标题
                # 根据标题大小动态调整pad值
                title_pad = max(10, self.title_size * 1.5)
                self.ax.set_title(self.title_edit.text(), fontsize=self.title_size, pad=title_pad)
                # 动态调整子图位置以适应标题
                self.figure.subplots_adjust(top=0.9 - self.title_size * 0.005)
        else:
            # 不显示标题时恢复默认布局
            self.ax.set_title('')
            self.figure.suptitle('')
            self.figure.subplots_adjust(top=0.95, bottom=0.1)
        
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
        """当参数改变时只更新当前选中的曲线"""
        # 只有在有选中曲线时才处理参数变化
        if self.active_plot_index < 0 or self.active_plot_index >= len(self.current_plots):
            return
            
        # 当频率改变时，更新数据读取器的当前频率
        if self.data_reader:
            current_freq_idx = self.freq_combo.currentIndex()
            # 只为当前操作设置频率，不影响全局状态
            
            # 频率改变时需要重新更新切面角度选项
            self.update_plane_angle_options()
        
        # 只更新当前选中的曲线参数
        plot = self.current_plots[self.active_plot_index]
        
        # 确保切面角度值有效
        try:
            plane_angle = float(self.plane_angle_combo.currentText())
        except (ValueError, TypeError):
            plane_angle = 0.0
            if self.plane_angle_combo.count() > 0:
                try:
                    plane_angle = float(self.plane_angle_combo.itemText(0))
                except:
                    plane_angle = 0.0
        
        # 只更新当前选中曲线的参数，不影响其他曲线
        plot.update({
            'freq_idx': self.freq_combo.currentIndex(),
            'freq_text': self.freq_combo.currentText(),
            'polarization': self.polarization_combo.currentText(),
            'plane_type': self.plane_type_combo.currentText(),
            'plane_angle': plane_angle,
            'line_style': self.line_style_combo.currentText(),
            'line_width': self.line_width_spin.value(),
            'color': self.current_color,  # 确保颜色也被更新
            'normalized': self.normalize_cb.isChecked()
        })
        
        # 更新曲线列表中的显示名称，包含更详细的信息
        plane_type_text = "θ切面" if plot['plane_type'] == '水平(Theta)' else "φ切面"
        curve_name = f"曲线{self.active_plot_index + 1}: {plot['freq_text']}, {plot['polarization']}, {plane_type_text}, {int(plot['plane_angle'])}°"
        self.plot_list.item(self.active_plot_index).setText(curve_name)
        
        self.update_plot()

    def choose_color(self):
        """选择线条颜色"""
        if self.active_plot_index < 0 or self.active_plot_index >= len(self.current_plots):
            QMessageBox.warning(self, "警告", "请先选择一条曲线")
            return
            
        # 获取当前颜色作为默认值
        current_color_name = self.current_plots[self.active_plot_index]['color']
        try:
            from PySide6.QtGui import QColor
            current_color = QColor(current_color_name)
        except:
            current_color = QColor('blue')
            
        color = QColorDialog.getColor(current_color, self, "选择曲线颜色")
        if color.isValid():
            # 只更新当前选中曲线的颜色
            self.current_plots[self.active_plot_index]['color'] = color.name()
            self.current_color = color.name()
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
        
        # 自动分配默认颜色和线型，确保每条曲线都不同
        color_index = len(self.current_plots) % len(self.default_colors)
        line_style_index = len(self.current_plots) % len(self.default_line_styles)
        
        default_color = self.default_colors[color_index]
        default_line_style = self.default_line_styles[line_style_index]
        
        # 确保切面角度值有效
        try:
            plane_angle = float(self.plane_angle_combo.currentText())
        except (ValueError, TypeError):
            plane_angle = 0.0
            if self.plane_angle_combo.count() > 0:
                try:
                    plane_angle = float(self.plane_angle_combo.itemText(0))
                except:
                    plane_angle = 0.0
        
        plot_info = {
            'freq_idx': self.freq_combo.currentIndex(),
            'freq_text': self.freq_combo.currentText(),
            'polarization': self.polarization_combo.currentText(),
            'plane_type': self.plane_type_combo.currentText(),
            'plane_angle': plane_angle,
            'line_style': default_line_style,
            'line_width': 2,  # 默认线宽
            'color': default_color,
            'normalized': self.normalize_cb.isChecked()
        }
        
        self.current_plots.append(plot_info)
        
        # 更新曲线列表显示，包含更详细的信息
        plane_type_text = "θ切面" if plot_info['plane_type'] == '水平(Theta)' else "φ切面"
        curve_name = f"曲线{len(self.current_plots)}: {plot_info['freq_text']}, {plot_info['polarization']}, {plane_type_text}, {int(plot_info['plane_angle'])}°"
        self.plot_list.addItem(curve_name)
        self.plot_list.setCurrentRow(len(self.current_plots) - 1)
        
        # 更新控件显示当前曲线的设置
        self.update_curve_controls()
        self.update_plot()
        
    def remove_current_plot(self):
        """删除当前选中的曲线"""
        if self.active_plot_index >= 0 and self.active_plot_index < len(self.current_plots):
            # 删除曲线
            self.current_plots.pop(self.active_plot_index)
            self.plot_list.takeItem(self.active_plot_index)
            
            # 更新曲线列表中的显示名称（重新编号），包含更详细的信息
            for i in range(len(self.current_plots)):
                plot = self.current_plots[i]
                plane_type_text = "θ切面" if plot['plane_type'] == '水平(Theta)' else "φ切面"
                curve_name = f"曲线{i + 1}: {plot['freq_text']}, {plot['polarization']}, {plane_type_text}, {int(plot['plane_angle'])}°"
                self.plot_list.item(i).setText(curve_name)
            
            # 调整活动索引
            if len(self.current_plots) == 0:
                self.active_plot_index = -1
            elif self.active_plot_index >= len(self.current_plots):
                self.active_plot_index = len(self.current_plots) - 1
                self.plot_list.setCurrentRow(self.active_plot_index)
            
            # 更新控件显示
            if self.active_plot_index >= 0:
                self.update_curve_controls()
            
            self.update_plot()
            
    def on_plot_selected(self, index):
        """当选择不同曲线时更新控件状态，不重复刷新图表"""
        if index >= 0 and index < len(self.current_plots):
            # 只有当选择的曲线真正改变时才更新
            if self.active_plot_index != index:
                self.active_plot_index = index
                self.update_curve_controls()
                # 不调用 update_plot()，避免重复刷新
        else:
            self.active_plot_index = -1
    
    def update_curve_controls(self):
        """更新曲线控件显示当前选中曲线的参数"""
        if self.active_plot_index >= 0 and self.active_plot_index < len(self.current_plots):
            plot = self.current_plots[self.active_plot_index]
            
            # 暂时断开信号连接，避免触发参数改变事件
            self.disconnect_curve_signals()
            
            try:
                # 更新控件值
                self.freq_combo.setCurrentIndex(plot['freq_idx'])
                self.polarization_combo.setCurrentText(plot['polarization'])
                self.plane_type_combo.setCurrentText(plot['plane_type'])
                
                # 保存当前曲线的切面角度，确保不会被重置
                target_angle = plot['plane_angle']
                
                # 更新切面角度选项（基于当前选择的切面类型）
                self.update_plane_angle_options_for_curve(target_angle)
                
                # 设置切面角度 - 使用保存的目标角度
                angle_text = str(int(target_angle))
                if self.plane_angle_combo.findText(angle_text) >= 0:
                    self.plane_angle_combo.setCurrentText(angle_text)
                else:
                    # 如果找不到精确匹配，添加这个角度选项
                    self.plane_angle_combo.addItem(angle_text)
                    self.plane_angle_combo.setCurrentText(angle_text)
                
                self.line_style_combo.setCurrentText(plot['line_style'])
                self.line_width_spin.setValue(plot['line_width'])
                self.current_color = plot['color']
                self.normalize_cb.setChecked(plot['normalized'])
                
            except Exception as e:
                print(f"Error updating curve controls: {e}")
            finally:
                # 重新连接信号
                self.connect_curve_signals()
    
    def disconnect_curve_signals(self):
        """断开曲线参数控件的信号连接"""
        try:
            self.freq_combo.currentIndexChanged.disconnect()
            self.polarization_combo.currentIndexChanged.disconnect()
            self.plane_type_combo.currentIndexChanged.disconnect()
            self.plane_angle_combo.currentIndexChanged.disconnect()
            self.line_style_combo.currentTextChanged.disconnect()
            self.line_width_spin.valueChanged.disconnect()
            self.normalize_cb.stateChanged.disconnect()
        except:
            pass  # 如果信号未连接，忽略错误
    
    def connect_curve_signals(self):
        """重新连接曲线参数控件的信号"""
        self.freq_combo.currentIndexChanged.connect(self.on_parameter_changed)
        self.polarization_combo.currentIndexChanged.connect(self.on_parameter_changed)
        self.plane_type_combo.currentIndexChanged.connect(self.on_parameter_changed)
        self.plane_angle_combo.currentIndexChanged.connect(self.on_parameter_changed)
        self.line_style_combo.currentTextChanged.connect(self.on_parameter_changed)
        self.line_width_spin.valueChanged.connect(self.on_parameter_changed)
        self.normalize_cb.stateChanged.connect(self.on_parameter_changed)

    def toggle_3d_gain_range(self, state):
        """切换3D数据范围控制"""
        is_auto = state == Qt.Checked
        self.d3_min_gain_spin.setEnabled(not is_auto)
        self.d3_max_gain_spin.setEnabled(not is_auto)
        self.update_plot()

    def toggle_2d_gain_range(self, state):
        """切换2D增益范围控制"""
        is_auto = state == Qt.Checked
        self.min_gain_spin.setEnabled(not is_auto)
        self.max_gain_spin.setEnabled(not is_auto)
        self.gain_steps_spin.setEnabled(not is_auto)
        self.update_plot()

    def update_axis_direction(self, direction):
        """更新坐标轴方向"""
        direction_map = {
            'N': 'N',  # 北向上
            'S': 'S',  # 南向上
            'E': 'E',  # 东向上
            'W': 'W'   # 西向上
        }
        if hasattr(self, 'ax') and self.ax is not None:
            self.ax.set_theta_zero_location(direction_map[direction])
            self.canvas.draw()
            
    def update_axis_angle(self, angle):
        """更新坐标轴角度"""
        if hasattr(self, 'ax') and self.ax is not None:
            # 设置角度偏移
            self.ax.set_theta_offset(np.deg2rad(angle))
            self.canvas.draw()
            
    def insert_image(self):
        """插入图片"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            self.lang.get('import_image'),
            "",
            self.lang.get('image_filter_all')
        )
        
        if file_name:
            try:
                # 读取图片 - 使用多种方法确保兼容性
                img = None
                try:
                    # 首先尝试使用matplotlib读取
                    img = plt.imread(file_name)
                except Exception:
                    try:
                        # 如果失败，尝试使用PIL读取
                        from PIL import Image
                        import numpy as np
                        pil_img = Image.open(file_name)
                        # 转换为RGB模式（如果是RGBA或其他模式）
                        if pil_img.mode != 'RGB':
                            pil_img = pil_img.convert('RGB')
                        img = np.array(pil_img) / 255.0  # 归一化到0-1范围
                    except Exception:
                        # 最后尝试使用opencv读取
                        import cv2
                        img_bgr = cv2.imread(file_name)
                        if img_bgr is not None:
                            img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB) / 255.0
                
                if img is None:
                    raise ValueError("无法读取图片文件")
                
                # 确保图片数据格式正确
                if img.dtype != np.float32 and img.dtype != np.float64:
                    img = img.astype(np.float32)
                
                # 确保值在0-1范围内
                if img.max() > 1.0:
                    img = img / 255.0
                
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
                
                # 清除并显示图片
                self.image_ax.clear()
                # 强制设置alpha=1.0并禁用任何透明度
                self.image_ax.imshow(img, aspect='equal', alpha=1.0, interpolation='bilinear')
                self.image_ax.axis('off')
                
                # 保存图片文件路径和数据
                self.current_image = file_name
                self.current_image_data = img
                
                # 将图片子图置于顶层，但在图例之下
                self.image_ax.set_zorder(9)  # 设置较低的zorder
                
                # 更新主图
                self.update_plot()  # 重新绘制主图以确保正确的层级关系
                
                # 强制刷新画布
                self.canvas.draw_idle()
                
            except Exception as e:
                QMessageBox.critical(self, self.lang.get('error'),
                                   f"{self.lang.get('image_error')}: {str(e)}")

    

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
            
            # 添加调整大小的视觉指示器
            self.add_resize_indicator()

    def add_resize_indicator(self):
        """在图片右下角添加调整大小的视觉指示器"""
        if not hasattr(self, 'image_ax'):
            return
            
        # 移除之前的指示器（如果存在）
        if hasattr(self, 'resize_indicator'):
            try:
                self.resize_indicator.remove()
            except:
                pass
        
        # 在图片坐标系中添加一个小三角形作为调整大小的指示器
        from matplotlib.patches import Polygon
        import numpy as np
        
        # 创建一个小三角形在右下角
        triangle_size = 0.1  # 相对于图片大小
        triangle = np.array([
            [1-triangle_size, 1],
            [1, 1],
            [1, 1-triangle_size]
        ])
        
        # 创建三角形补丁
        self.resize_indicator = Polygon(triangle, closed=True, 
                                      facecolor='white', edgecolor='gray', 
                                      alpha=0.7, linewidth=1, zorder=15)
        self.image_ax.add_patch(self.resize_indicator)

    def remove_image(self):
        """移除图片"""
        if hasattr(self, 'image_ax'):
            # 移除调整大小指示器
            if hasattr(self, 'resize_indicator'):
                try:
                    self.resize_indicator.remove()
                    delattr(self, 'resize_indicator')
                except:
                    pass
            
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

    def show_data_table(self):
        """显示一个包含当前2D视图数据的表格对话框"""
        if self.is_3d_view or not self.current_plots or self.active_plot_index < 0:
            return

        plot = self.current_plots[self.active_plot_index]
        freq_idx = plot['freq_idx']
        plane_type = plot['plane_type']
        plane_angle = plot['plane_angle']
        
        headers = [
            self.lang.get('display_angle'),
            self.lang.get('source_angle'),
            self.lang.get('gain_value')
        ]
        table_data = []

        if plane_type == '水平(Theta)':
            # Recreate the logic from excel_reader's debug log for Theta cut
            phi_angles = self.data_reader.phi_angles_map[self.data_reader.frequencies[freq_idx]]
            theta_angles = self.data_reader.theta_angles_map[self.data_reader.frequencies[freq_idx]]
            
            primary_phi_idx = min(range(len(phi_angles)), key=lambda i: abs(phi_angles[i] - plane_angle))
            opposite_phi_angle_req = -plane_angle
            opposite_phi_idx = min(range(len(phi_angles)), key=lambda i: abs(phi_angles[i] - opposite_phi_angle_req))

            # These variables are named primary_theta_val/opposite_theta_val in the log in excel_reader.py
            # to represent the Phi angle for the cut, so we replicate that here for consistency.
            primary_theta_val_for_table = phi_angles[primary_phi_idx]
            opposite_theta_val_for_table = phi_angles[opposite_phi_idx]

            gains_primary_phi = self.data_reader.gains[self.data_reader.frequencies[freq_idx]][:, primary_phi_idx]
            gains_opposite_phi = self.data_reader.gains[self.data_reader.frequencies[freq_idx]][:, opposite_phi_idx]

            # Normalization: Combine, normalize, then split
            if plot['normalized']:
                combined_gains_for_norm = np.concatenate((gains_primary_phi, gains_opposite_phi))
                normalized_combined_gains = self.data_reader.normalize_data(combined_gains_for_norm)
                gains_primary_phi_normalized = normalized_combined_gains[:len(gains_primary_phi)]
                gains_opposite_phi_normalized = normalized_combined_gains[len(gains_primary_phi):]
            else:
                gains_primary_phi_normalized = np.array(gains_primary_phi)
                gains_opposite_phi_normalized = np.array(gains_opposite_phi)

            # Populate table for the first half (Primary Phi)
            for i, gain in enumerate(gains_primary_phi_normalized):
                display_angle_for_table = i # Match log's Display Angle
                table_data.append([display_angle_for_table, f"({primary_theta_val_for_table}, {theta_angles[i]})", f"{gain:.2f}"])
            
            # Populate table for the second half (Opposite Phi - NOT reversed)
            for i, gain in enumerate(gains_opposite_phi_normalized):
                display_angle_for_table = len(gains_primary_phi_normalized) + i # Match log's Display Angle
                table_data.append([display_angle_for_table, f"({opposite_theta_val_for_table}, {theta_angles[i]})", f"{gain:.2f}"])

        else: # Phi cut
            theta_idx = min(range(len(self.data_reader.theta_angles)), key=lambda i: abs(self.data_reader.theta_angles[i] - plane_angle))
            gains = self.data_reader.gains[self.data_reader.frequencies[freq_idx]][theta_idx, :]
            if plot['normalized']:
                gains = self.data_reader.normalize_data(gains)
            
            for i, gain in enumerate(gains):
                display_angle = self.data_reader.phi_angles[i]
                source_angle = f"({self.data_reader.theta_angles[theta_idx]}, {self.data_reader.phi_angles[i]})"
                table_data.append([display_angle, source_angle, f"{gain:.2f}"])

        dialog = DataViewerDialog(table_data, headers, title=self.lang.get('data_table'), parent=self)
        dialog.exec()

    def rotate_image_dialog(self):
        """显示图片旋转对话框"""
        if not hasattr(self, 'image_ax'):
            return
            
        angle, ok = QInputDialog.getDouble(
            self, 
            self.lang.get('rotate_image'), 
            self.lang.get('rotation_angle') + ' (0-360°):', 
            self.image_rotation, 
            0, 
            360, 
            1
        )
        
        if ok:
            self.image_rotation = angle
            self.update_image_rotation()
            self.canvas.draw()

    def update_image_rotation(self):
        """更新图片旋转"""
        if hasattr(self, 'image_ax') and hasattr(self, 'current_image_data'):
            # 清除当前图片
            self.image_ax.clear()
            
            # 重新显示旋转后的图片
            try:
                from scipy.ndimage import rotate
                rotated_image = rotate(self.current_image_data, self.image_rotation, reshape=False)
            except ImportError:
                # 如果scipy不可用，使用PIL进行旋转
                from PIL import Image
                import numpy as np
                
                # 转换为PIL图像
                if self.current_image_data.max() <= 1.0:
                    pil_img = Image.fromarray((self.current_image_data * 255).astype(np.uint8))
                else:
                    pil_img = Image.fromarray(self.current_image_data.astype(np.uint8))
                
                # 旋转图像
                rotated_pil = pil_img.rotate(-self.image_rotation, expand=False)
                rotated_image = np.array(rotated_pil) / 255.0
            
            # 强制设置alpha=1.0并禁用任何透明度
            self.image_ax.imshow(rotated_image, alpha=1.0, interpolation='bilinear')
            self.image_ax.axis('off')
            
            # 强制刷新
            self.canvas.draw_idle()

    def toggle_title_display(self, text):
        """切换标题显示"""
        self.show_title = 'show' if text == self.lang.get('show') else 'hide'
        self.update_plot()

    def toggle_legend_display(self, text):
        """切换图例显示"""
        self.show_legend = 'show' if text == self.lang.get('show') else 'hide'
        self.update_plot()

    def change_title_position(self, position_text):
        """改变标题位置"""
        if position_text == self.lang.get('bottom'):
            self.title_position = 'bottom'
        else:
            self.title_position = 'top'
        self.update_plot()

    def change_title_size(self, size):
        """改变标题大小"""
        self.title_size = size
        self.update_plot()

    def change_legend_size(self, size):
        """改变图例大小"""
        self.legend_size = size
        self.update_plot()

    def change_grid_interval(self, interval_text):
        """改变极坐标网格间隔"""
        if interval_text == self.lang.get('degrees_15'):
            self.polar_grid_interval = 15
        elif interval_text == self.lang.get('degrees_30'):
            self.polar_grid_interval = 30
        elif interval_text == self.lang.get('degrees_45'):
            self.polar_grid_interval = 45
        self.update_plot()

    def rotate_image_90(self):
        """逆时针旋转图片90度"""
        if hasattr(self, 'image_ax') and hasattr(self, 'current_image_data'):
            self.image_rotation = (self.image_rotation + 90) % 360
            self.update_image_rotation()
            self.canvas.draw()

    def update_title_text(self, text):
        """更新标题文本"""
        self.plot_title_text = text
        self.update_plot()
    
    def toggle_title_display(self, text):
        """切换标题显示"""
        self.show_title = 'show' if text == self.lang.get('show') else 'hide'
        self.update_plot()
    
    def change_title_position(self, text):
        """改变标题位置"""
        self.title_position = 'bottom' if text == self.lang.get('bottom') else 'top'
        self.update_plot()

    def update_title(self):
        """更新图表标题"""
        if hasattr(self, 'ax'):
            if self.show_title == 'show' and self.plot_title_text:
                # 设置标题，支持中文显示
                plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
                plt.rcParams['axes.unicode_minus'] = False
                
                if self.title_position == 'bottom':
                    # 在底部显示标题，使用figure的suptitle
                    self.ax.set_title('')  # 清除顶部标题
                    self.figure.suptitle(self.plot_title_text, y=0.02, fontsize=self.title_size)
                else:
                    # 在顶部显示标题，使用较小的pad避免图表过度缩小
                    self.figure.suptitle('')  # 清除底部标题
                    self.ax.set_title(self.plot_title_text, fontsize=self.title_size, pad=15)
            else:
                # 不显示标题
                self.ax.set_title('')
                self.figure.suptitle('')
    
    def check_title_image_overlap(self):
        """检测标题和图片是否重叠，如果重叠则调整图表大小"""
        if not hasattr(self, 'image_ax') or not hasattr(self, 'current_image_data'):
            return
            
        # 获取标题的边界框
        title = self.ax.title
        if not title.get_text():
            return
            
        # 强制渲染以获取准确的边界框
        self.canvas.draw()
        
        # 获取标题在Figure坐标系中的边界框
        title_bbox = title.get_window_extent(renderer=self.canvas.get_renderer())
        title_bbox_fig = title_bbox.transformed(self.figure.transFigure.inverted())
        
        # 获取图片在Figure坐标系中的边界框
        image_bbox_fig = self.image_ax.get_position()
        
        # 检测是否重叠
        overlap = self.check_bbox_overlap(title_bbox_fig, image_bbox_fig)
        
        if overlap:
            # 如果重叠，调整主图的大小和位置
            self.adjust_plot_for_title_overlap(title_bbox_fig, image_bbox_fig)
    
    def check_bbox_overlap(self, bbox1, bbox2):
        """检查两个边界框是否重叠"""
        # bbox1 和 bbox2 都是 matplotlib.transforms.Bbox 对象
        return not (bbox1.x1 < bbox2.x0 or bbox2.x1 < bbox1.x0 or 
                   bbox1.y1 < bbox2.y0 or bbox2.y1 < bbox1.y0)
    
    def adjust_plot_for_title_overlap(self, title_bbox, image_bbox):
        """调整图表大小以避免标题和图片重叠"""
        # 获取当前主图的位置
        ax_pos = self.ax.get_position()
        
        # 计算需要调整的量
        if self.title_position == 'top':
            # 标题在顶部，如果与图片重叠，缩小主图并向下移动
            if title_bbox.y0 < image_bbox.y1:
                # 计算重叠的高度
                overlap_height = image_bbox.y1 - title_bbox.y0 + 0.05  # 添加一些边距
                
                # 调整主图位置和大小
                new_height = ax_pos.height - overlap_height
                new_y = ax_pos.y0 + overlap_height
                
                if new_height > 0.3:  # 确保图表不会太小
                    self.ax.set_position([ax_pos.x0, new_y, ax_pos.width, new_height])
        else:
            # 标题在底部，如果与图片重叠，缩小主图并向上移动
            if title_bbox.y1 > image_bbox.y0:
                # 计算重叠的高度
                overlap_height = title_bbox.y1 - image_bbox.y0 + 0.05  # 添加一些边距
                
                # 调整主图位置和大小
                new_height = ax_pos.height - overlap_height
                
                if new_height > 0.3:  # 确保图表不会太小
                    self.ax.set_position([ax_pos.x0, ax_pos.y0, ax_pos.width, new_height])

    def adjust_plot_for_title_size(self):
        """根据标题大小调整图表大小以避免重叠"""
        if not hasattr(self, 'ax') or not self.plot_title_text or self.show_title != 'show':
            # 如果没有标题，恢复默认图表大小
            self.ax.set_position([0.1, 0.1, 0.8, 0.8])
            return
            
        # 根据标题字体大小计算需要的空间
        title_space_ratio = self.title_size / 100.0  # 将字体大小转换为比例
        
        # 获取当前主图的默认位置
        default_pos = [0.1, 0.1, 0.8, 0.8]  # [left, bottom, width, height]
        
        if self.title_position == 'top':
            # 标题在顶部，减少图表高度并向下移动
            title_space = min(title_space_ratio, 0.15)  # 最大占用15%的空间
            new_height = default_pos[3] - title_space
            new_bottom = default_pos[1]
            new_position = [default_pos[0], new_bottom, default_pos[2], new_height]
        else:
            # 标题在底部，减少图表高度并向上移动
            title_space = min(title_space_ratio, 0.15)  # 最大占用15%的空间
            new_height = default_pos[3] - title_space
            new_bottom = default_pos[1] + title_space
            new_position = [default_pos[0], new_bottom, default_pos[2], new_height]
        
        # 确保图表不会太小
        if new_position[3] > 0.4:  # 高度至少保持40%
            self.ax.set_position(new_position)

    def toggle_2d_gain_range(self, state):
        """切换2D增益范围自动/手动模式"""
        auto_mode = state == Qt.Checked
        self.min_gain_spin.setEnabled(not auto_mode)
        self.max_gain_spin.setEnabled(not auto_mode)
        self.gain_steps_spin.setEnabled(not auto_mode)
        self.update_plot()

    def update_image_rotation(self):
        """更新图片旋转"""
        if hasattr(self, 'image_ax') and hasattr(self, 'current_image_data'):
            # 清除当前图片
            self.image_ax.clear()
            
            # 重新显示旋转后的图片
            try:
                import numpy as np
                from scipy.ndimage import rotate
                rotated_image = rotate(self.current_image_data, self.image_rotation, reshape=False)
            except ImportError:
                # 如果scipy不可用，使用PIL进行旋转
                from PIL import Image
                import numpy as np
                
                # 转换为PIL图像
                if self.current_image_data.max() <= 1.0:
                    pil_img = Image.fromarray((self.current_image_data * 255).astype(np.uint8))
                else:
                    pil_img = Image.fromarray(self.current_image_data.astype(np.uint8))
                
                # 旋转图像
                rotated_pil = pil_img.rotate(-self.image_rotation, expand=False)
                rotated_image = np.array(rotated_pil) / 255.0
            
            # 强制设置alpha=1.0并禁用任何透明度
            self.image_ax.imshow(rotated_image, alpha=1.0, interpolation='bilinear')
            self.image_ax.axis('off')
            self.update_image_position()
            
            # 强制刷新
            self.canvas.draw_idle()

    def update_image_position(self):
        """更新图片位置和大小"""
        if hasattr(self, 'image_ax'):
            # 计算图片在Figure坐标系中的位置
            left = self.image_position[0] - self.image_size[0] / 2
            bottom = self.image_position[1] - self.image_size[1] / 2
            width = self.image_size[0]
            height = self.image_size[1]
            
            # 设置图片子图的位置
            self.image_ax.set_position([left, bottom, width, height])

    def modify_image_size(self):
        """修改图片大小对话框"""
        if not hasattr(self, 'image_ax'):
            return
            
        width, ok1 = QInputDialog.getDouble(
            self, 
            self.lang.get('modify_size'), 
            self.lang.get('width') + ' (0.1-1.0):', 
            self.image_size[0], 
            0.1, 
            1.0, 
            2
        )
        
        if ok1:
            height, ok2 = QInputDialog.getDouble(
                self, 
                self.lang.get('modify_size'), 
                self.lang.get('height') + ' (0.1-1.0):', 
                self.image_size[1], 
                0.1, 
                1.0, 
                2
            )
            
            if ok2:
                self.image_size = [width, height]
                self.update_image_position()
                self.canvas.draw()

    def modify_image_position(self):
        """修改图片位置对话框"""
        if not hasattr(self, 'image_ax'):
            return
            
        x, ok1 = QInputDialog.getDouble(
            self, 
            self.lang.get('modify_position'), 
            'X (0.0-1.0):', 
            self.image_position[0], 
            0.0, 
            1.0, 
            2
        )
        
        if ok1:
            y, ok2 = QInputDialog.getDouble(
                self, 
                self.lang.get('modify_position'), 
                'Y (0.0-1.0):', 
                self.image_position[1], 
                0.0, 
                1.0, 
                2
            )
            
            if ok2:
                self.image_position = [x, y]
                self.update_image_position()
                self.canvas.draw()

    def remove_image(self):
        """删除图片"""
        if hasattr(self, 'image_ax'):
            self.image_ax.remove()
            delattr(self, 'image_ax')
        if hasattr(self, 'current_image_data'):
            delattr(self, 'current_image_data')
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
                from PIL import Image
                import numpy as np
                
                # 加载图片
                image = Image.open(file_name)
                self.current_image_data = np.array(image)
                
                # 创建图片子图
                self.image_ax = self.figure.add_axes([0, 0, 1, 1])
                self.image_ax.patch.set_alpha(0)  # 设置背景透明
                self.image_ax.imshow(self.current_image_data, alpha=1.0)  # 设置alpha=1.0确保不透明
                self.image_ax.axis('off')
                self.update_image_position()
                self.image_ax.set_zorder(10)  # 确保图片在最上层
                
                self.canvas.draw()
                
            except Exception as e:
                QMessageBox.critical(self, self.lang.get('error'),
                                   f"{self.lang.get('image_error')}: {str(e)}")

    def load_settings(self):
        """加载设置"""
        # 从QSettings加载设置
        pass

    def save_settings(self):
        """保存设置"""
        # 保存设置到QSettings
        pass

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
class DataViewerDialog(QDialog):
    def __init__(self, data, headers, title="Data", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setLayout(QVBoxLayout())
        self.resize(400, 600)

        self.table = QTableWidget(len(data), len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))
        
        self.table.resizeColumnsToContents()
        self.layout().addWidget(self.table)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        self.layout().addWidget(buttons) 