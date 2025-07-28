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
from mpl_toolkits.mplot3d import Axes3D
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
            self.ax.set_theta_zero_location('S')  # 重置0度位置
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
        """创建简化的工具栏"""
        toolbar = QToolBar()
        toolbar.setObjectName("mainToolBar")
        self.addToolBar(toolbar)
        
        # 工具栏现在只保留基本的视图控制功能
        # 数据导入和保存功能已移至页签中

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
        
        # 视图类型选择组
        view_type_group = QGroupBox(self.lang.get('view_type'))
        view_type_layout = QVBoxLayout(view_type_group)
        
        self.view_combo = QComboBox()
        self.view_combo.addItems([self.lang.get('2d_view'), self.lang.get('3d_view')])
        self.view_combo.currentIndexChanged.connect(self.switch_view)
        view_type_layout.addWidget(self.view_combo)
        view_layout.addWidget(view_type_group)
        
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
        
        # 3D视图控制组
        self.d3_controls = QGroupBox(self.lang.get('3d_view_controls'))
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

        view_layout.addWidget(self.d3_controls)
        self.d3_controls.setVisible(False)
        
        # 3D视图数据范围控制组
        self.d3_data_range_group = QGroupBox(self.lang.get('data_range_3d'))
        d3_range_layout = QVBoxLayout(self.d3_data_range_group)

        self.d3_auto_gain_cb = QCheckBox(self.lang.get('auto_range'))
        self.d3_auto_gain_cb.setChecked(True)
        self.d3_auto_gain_cb.stateChanged.connect(self.toggle_3d_gain_range)
        d3_range_layout.addWidget(self.d3_auto_gain_cb)

        d3_gain_range_layout = QHBoxLayout()
        self.d3_min_gain_spin = QDoubleSpinBox()
        self.d3_min_gain_spin.setRange(-100, 100)
        self.d3_min_gain_spin.setValue(-30)
        self.d3_min_gain_spin.setEnabled(False)
        self.d3_min_gain_spin.valueChanged.connect(self.update_plot)
        d3_gain_range_layout.addWidget(QLabel("Min:"))
        d3_gain_range_layout.addWidget(self.d3_min_gain_spin)

        self.d3_max_gain_spin = QDoubleSpinBox()
        self.d3_max_gain_spin.setRange(-100, 100)
        self.d3_max_gain_spin.setValue(10)
        self.d3_max_gain_spin.setEnabled(False)
        self.d3_max_gain_spin.valueChanged.connect(self.update_plot)
        d3_gain_range_layout.addWidget(QLabel("Max:"))
        d3_gain_range_layout.addWidget(self.d3_max_gain_spin)
        d3_range_layout.addLayout(d3_gain_range_layout)
        
        view_layout.addWidget(self.d3_data_range_group)
        self.d3_data_range_group.setVisible(False)
        
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
        
        view_layout.addWidget(self.gain_control_group)
        
        
        
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
        self.plane_type_combo.addItems(['Theta', 'Phi'])
        self.plane_type_combo.currentIndexChanged.connect(self.on_parameter_changed)
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
        
        # 图表设置组
        chart_group = QGroupBox(self.lang.get('chart_settings'))
        chart_layout = QVBoxLayout(chart_group)
        
        # 图表标题
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel(self.lang.get('plot_title')))
        self.title_edit = QLineEdit()
        self.title_edit.setMinimumHeight(30)
        self.title_edit.setPlaceholderText(self.lang.get('plot_title'))
        self.title_edit.textChanged.connect(self.update_title)
        title_layout.addWidget(self.title_edit)
        chart_layout.addLayout(title_layout)
        
        export_layout.addWidget(chart_group)
        
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
        
        # 初始化为2D视图
        self.ax = self.figure.add_subplot(111, projection='polar')
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
            # Calculate corner size in figure coordinates based on pixels
            corner_pixel_size = 20  # pixels
            # Convert pixel size to figure coordinates
            corner_size_x = corner_pixel_size / self.canvas.width() * self.figure.get_figwidth() / self.figure.get_figwidth() # This is effectively corner_pixel_size / self.canvas.width()
            corner_size_y = corner_pixel_size / self.canvas.height() * self.figure.get_figheight() / self.figure.get_figheight() # This is effectively corner_pixel_size / self.canvas.height()
            
            # A more robust way to convert pixel to figure coordinates for corner size
            # Get the transform from pixels to figure coordinates
            pixel_to_figure_transform = self.figure.transFigure.inverted()
            # Calculate the size of 20 pixels in figure coordinates
            # We need to transform a vector, not a point, so we transform (0,0) and (20,20) and take the difference
            p0_fig = pixel_to_figure_transform.transform((0, 0))
            p20_fig = pixel_to_figure_transform.transform((corner_pixel_size, corner_pixel_size))
            corner_size_x = p20_fig[0] - p0_fig[0]
            corner_size_y = p20_fig[1] - p0_fig[1]


            is_in_resize_corner = (x_fig > bbox_fig.x1 - corner_size_x and x_fig < bbox_fig.x1 and
                                   y_fig > bbox_fig.y0 and y_fig < bbox_fig.y0 + corner_size_y)
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
        
        # 添加��改位置的动作
        position_action = menu.addAction(self.lang.get('modify_position'))
        position_action.triggered.connect(self.modify_image_position)
        
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
            # dx and dy are already in figure coordinates
            dx = (x_fig - self.resize_corner[0])
            dy = (y_fig - self.resize_corner[1])
            
            # Calculate new size (maintaining aspect ratio)
            original_ratio = self.resize_start_size[0] / self.resize_start_size[1]
            
            # Calculate new width/height in figure coordinates
            if abs(dx) > abs(dy):
                new_width_fig = self.resize_start_size[0] + dx
                new_height_fig = new_width_fig / original_ratio
            else:
                # For bottom-right corner, dragging down (dy negative) should increase height
                new_height_fig = self.resize_start_size[1] - dy  # Invert dy
                new_width_fig = new_height_fig * original_ratio
            
            # Convert pixel-based min/max sizes to figure coordinates for limits
            pixel_to_figure_transform = self.figure.transFigure.inverted()
            p0_fig = pixel_to_figure_transform.transform((0, 0))
            
            min_size_pixels = 20
            p_min_size_fig = pixel_to_figure_transform.transform((min_size_pixels, min_size_pixels))
            min_size_fig_x = p_min_size_fig[0] - p0_fig[0]
            min_size_fig_y = p_min_size_fig[1] - p0_fig[1]

            # Max size as 80% of figure size (which is 1.0 in figure coordinates)
            max_width_fig = 0.8
            max_height_fig = 0.8
            
            new_width_fig = max(min_size_fig_x, min(new_width_fig, max_width_fig))
            new_height_fig = max(min_size_fig_y, min(new_height_fig, max_height_fig))
            
            self.image_size = [new_width_fig, new_height_fig]
            
            self.update_image_position()
            self.canvas.draw()
            if self.debug_mode:
                print(f"DEBUG: Image resized to: {self.image_size}")
            
        # 更新鼠标样式
        if not self.image_dragging and not self.image_resizing and hasattr(self, 'image_ax'):
            bbox_fig = self.image_ax.get_position()
            # Convert pixel size to figure coordinates for corner detection
            corner_pixel_size = 20  # pixels
            pixel_to_figure_transform = self.figure.transFigure.inverted()
            p0_fig = pixel_to_figure_transform.transform((0, 0))
            p20_fig = pixel_to_figure_transform.transform((corner_pixel_size, corner_pixel_size))
            corner_size_x = p20_fig[0] - p0_fig[0]
            corner_size_y = p20_fig[1] - p0_fig[1]

            if bbox_fig.contains(x_fig, y_fig):
                if (x_fig > bbox_fig.x1 - corner_size_x and x_fig < bbox_fig.x1 and 
                    y_fig > bbox_fig.y0 and y_fig < bbox_fig.y0 + corner_size_y):
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
        self.gain_control_group.setVisible(not self.is_3d_view)
        self.show_data_btn.setVisible(not self.is_3d_view)
        
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
            # If in 3D view, safely remove the colorbar before clearing the main axes
            if self.is_3d_view and hasattr(self, 'colorbar'):
                try:
                    self.colorbar.remove()
                except (AttributeError, KeyError):
                    # This can happen if the colorbar's axes are already detached
                    pass
                finally:
                    if hasattr(self, 'colorbar'):
                        delattr(self, 'colorbar')
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
            plane_type = self.plane_type_combo.currentText()
            plane_angle = float(self.plane_angle_combo.currentText())
            
            if plane_type == 'Theta':
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
            if plane_type == 'Theta':
                # 复制角度和增益数据
                full_angles = np.concatenate([theta_angles, theta_angles + 180])
                full_gains = np.concatenate([gains, gains])
                
                # 确保角度在-180到180度范围内
                full_angles = np.where(full_angles > 180, full_angles - 360, full_angles)
                full_angles = np.where(full_angles < -180, full_angles + 360, full_angles)
                
                # 按角度排序
                sort_idx = np.argsort(full_angles)
                full_angles = full_angles[sort_idx]
                full_gains = full_gains[sort_idx]
                
                # 转换角度为弧度
                angles_rad = self.data_reader.get_angles_in_radians(full_angles)
                label = f"{plot['freq_text']}, {plot['polarization']}, φ={plane_angle}°"
            else:
                # Phi切面已经是完整的360度数据
                angles_rad = self.data_reader.get_angles_in_radians(phi_angles)
                full_gains = gains
                label = f"{plot['freq_text']}, {plot['polarization']}, θ={plane_angle}°"
            
            # 绘制方向图
            self.ax.plot(angles_rad, full_gains,
                        linestyle=plot['line_style'],
                        linewidth=plot['line_width'],
                        color=plot['color'],
                        label=label,
                        zorder=5)  # 确保曲线在图片上方
                        
        self.ax.set_theta_zero_location(self.axis_direction_combo.currentText())
        self.ax.set_theta_direction(-1)  # 设置角度顺时针方向
        self.ax.grid(True)
        
        # 设置刻度标签
        self.ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
        self.ax.set_xticklabels(['0°', '45°', '90°', '135°', '180°', '225°', '270°', '315°'])
        
        # 添加图例并设置位置
        if self.current_plots:
            legend = self.ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
            legend.set_zorder(10)  # 确保图例在最顶层

        # 如果不是自动范围，则设置范围和刻度
        if not self.auto_gain_cb.isChecked():
            min_gain = self.min_gain_spin.value()
            max_gain = self.max_gain_spin.value()
            steps = self.gain_steps_spin.value()
            self.ax.set_rlim(min_gain, max_gain)
            self.ax.set_rticks(np.linspace(min_gain, max_gain, steps))

    def update_3d_plot(self):
        """更新3D方向图，使用带有切面示意图的球坐标样式"""
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        if not self.current_plots:
            return
            
        plot = self.current_plots[0]
        freq_idx = plot['freq_idx']
        
        # 获取数据
        phi_angles = np.array(self.data_reader.get_phi_angles())
        theta_angles = np.array(self.data_reader.get_theta_angles())
        gains = self.data_reader.gains.get(self.data_reader.frequencies[freq_idx])
        
        if gains is None:
            self.ax.text2D(0.5, 0.5, "No data available", transform=self.ax.transAxes, ha='center')
            self.canvas.draw()
            return

        if plot['normalized']:
            gains = self.data_reader.normalize_data(gains)
        
        # 创建角度网格
        phi_rad = np.deg2rad(phi_angles)
        theta_rad = np.deg2rad(theta_angles)
        PHI, THETA = np.meshgrid(phi_rad, theta_rad)
        
        # 转换坐标
        R = gains
        X = R * np.sin(THETA) * np.cos(PHI)
        Y = R * np.sin(THETA) * np.sin(PHI)
        Z = R * np.cos(THETA)
        
        # --- 自定义坐标��样式 ---
        self.ax.set_axis_off() # 关闭所有默认坐标轴元素
        self.ax.grid(False)

        # 获取数据
        phi_angles_orig = np.array(self.data_reader.get_phi_angles())
        theta_angles_orig = np.array(self.data_reader.get_theta_angles())
        gains_orig = self.data_reader.gains.get(self.data_reader.frequencies[freq_idx])
        
        if self.debug_mode:
            print(f"DEBUG 3D: Original Theta angles range: [{theta_angles_orig.min()}, {theta_angles_orig.max()}]")
            print(f"DEBUG 3D: Original Phi angles range: [{phi_angles_orig.min()}, {phi_angles_orig.max()}]")

        if gains_orig is None:
            self.ax.text2D(0.5, 0.5, "No data available", transform=self.ax.transAxes, ha='center')
            self.canvas.draw()
            return

        if plot['normalized']:
            gains_orig = self.data_reader.normalize_data(gains_orig)
        
        # --- Handle Theta Angle Extension for Full Sphere (0-180 degrees) ---
        theta_angles = theta_angles_orig
        gains_processed_theta = gains_orig

        if theta_angles_orig.max() < 179: # Use 179 to account for floating point inaccuracies
            if self.debug_mode:
                print(f"DEBUG 3D: Extending theta angles. Original max: {theta_angles_orig.max()}")
            
            theta_step = theta_angles_orig[1] - theta_angles_orig[0] if len(theta_angles_orig) > 1 else 10
            theta_angles_extended = np.arange(0, 180 + theta_step, theta_step)
            
            extended_gains_theta = np.zeros((len(theta_angles_extended), gains_orig.shape[1]))
            
            for i, theta_val in enumerate(theta_angles_extended):
                if theta_val <= theta_angles_orig.max():
                    orig_theta_idx = np.argmin(np.abs(theta_angles_orig - theta_val))
                    extended_gains_theta[i, :] = gains_orig[orig_theta_idx, :]
                else:
                    mirror_theta_val = 180 - theta_val
                    if mirror_theta_val >= theta_angles_orig.min():
                        orig_theta_idx = np.argmin(np.abs(theta_angles_orig - mirror_theta_val))
                        extended_gains_theta[i, :] = gains_orig[orig_theta_idx, :]
                    else:
                        extended_gains_theta[i, :] = gains_orig[0, :] # Fallback to theta=0 gain
            theta_angles = theta_angles_extended
            gains_processed_theta = extended_gains_theta

        # --- Handle Phi Angle Extension for Full 360 degrees ---
        phi_angles = phi_angles_orig
        gains_final = gains_processed_theta

        if phi_angles_orig.max() < 359: # Check if phi angles cover full 360 degrees
            if self.debug_mode:
                print(f"DEBUG 3D: Extending phi angles. Original max: {phi_angles_orig.max()}")

            phi_step = phi_angles_orig[1] - phi_angles_orig[0] if len(phi_angles_orig) > 1 else 10
            phi_angles_extended = np.arange(0, 360 + phi_step, phi_step)

            extended_gains_phi = np.zeros((gains_processed_theta.shape[0], len(phi_angles_extended)))

            for j, phi_val in enumerate(phi_angles_extended):
                if phi_val <= phi_angles_orig.max():
                    orig_phi_idx = np.argmin(np.abs(phi_angles_orig - phi_val))
                    extended_gains_phi[:, j] = gains_processed_theta[:, orig_phi_idx]
                else:
                    mirror_phi_val = 360 - phi_val
                    if mirror_phi_val >= phi_angles_orig.min():
                        orig_phi_idx = np.argmin(np.abs(phi_angles_orig - mirror_phi_val))
                        extended_gains_phi[:, j] = gains_processed_theta[:, orig_phi_idx]
                    else:
                        extended_gains_phi[:, j] = gains_processed_theta[:, 0] # Fallback to phi=0 gain

            phi_angles = phi_angles_extended
            gains_final = extended_gains_phi

        # Convert angles to radians
        phi_rad = np.deg2rad(phi_angles)
        theta_rad = np.deg2rad(theta_angles)
        PHI, THETA = np.meshgrid(phi_rad, theta_rad)
        
        # Convert to Cartesian coordinates
        R = gains_final
        X = R * np.sin(THETA) * np.cos(PHI)
        Y = R * np.sin(THETA) * np.sin(PHI)
        Z = R * np.cos(THETA)
        
        # --- Custom Axis Style ---
        self.ax.set_axis_off() # Turn off all default axis elements
        self.ax.grid(False)

        # Plot 3D surface
        surf = self.ax.plot_surface(X, Y, Z, cmap='viridis', linewidth=0.5, alpha=0.9, rstride=1, cstride=1, zorder=5)
        
        # Update color range based on settings
        if not self.d3_auto_gain_cb.isChecked():
            surf.set_clim(self.d3_min_gain_spin.value(), self.d3_max_gain_spin.value())

        # --- Draw Custom Reference Axes and Illustrative Planes ---
        max_r = np.nanmax(np.abs(R)) * 1.2 # Find max radius for axis and plane size
        if np.isnan(max_r) or max_r == 0: max_r = 10 # Fallback if R is all NaN or zero

        # Draw illustrative planes (existing code)
        circle_pts = np.linspace(0, 2 * np.pi, 100)
        
        # Theta=90 (XY plane)
        xy_plane_x = max_r * np.cos(circle_pts)
        xy_plane_y = max_r * np.sin(circle_pts)
        xy_plane_z = np.zeros_like(xy_plane_x)
        self.ax.add_collection3d(Poly3DCollection([list(zip(xy_plane_x, xy_plane_y, xy_plane_z))], color='lightcyan', alpha=0.1, zorder=1))
        self.ax.text(0, max_r, 0, "θ=90° Plane", color='darkcyan', ha='center')

        # Phi=0 (YZ plane)
        yz_plane_y = max_r * np.cos(circle_pts)
        yz_plane_z = max_r * np.sin(circle_pts)
        yz_plane_x = np.zeros_like(yz_plane_y)
        self.ax.add_collection3d(Poly3DCollection([list(zip(yz_plane_x, yz_plane_y, yz_plane_z))], color='thistle', alpha=0.1, zorder=1))
        self.ax.text(0, 0, max_r, "φ=0°/180° Plane", color='purple', ha='center')

        # Phi=90 (XZ plane)
        xz_plane_x = max_r * np.cos(circle_pts)
        xz_plane_z = max_r * np.sin(circle_pts)
        xz_plane_y = np.zeros_like(xz_plane_x)
        self.ax.add_collection3d(Poly3DCollection([list(zip(xz_plane_x, xz_plane_y, xz_plane_z))], color='lightgoldenrodyellow', alpha=0.1, zorder=1))
        self.ax.text(max_r, 0, 0, "φ=90°/270° Plane", color='olive', ha='center')

        # Draw coordinate axes with arrows
        axis_len = max_r * 1.1
        arrow_len = max_r * 0.05 # Length of the arrowhead
        arrow_width = max_r * 0.02 # Width of the arrowhead base

        # Z-axis (θ=0°)
        self.ax.plot([0, 0], [0, 0], [0, axis_len], color='gray', linestyle='-', zorder=2)
        self.ax.text(0, 0, axis_len * 1.05, "Z (θ=0°)", color='black', ha='center')
        # Z-axis arrowhead (simple cone approximation)
        self.ax.plot([0, 0], [0, 0], [axis_len - arrow_len, axis_len], color='gray', linestyle='-', linewidth=2, zorder=2)
        self.ax.plot([-arrow_width, arrow_width], [0, 0], [axis_len - arrow_len, axis_len - arrow_len], color='gray', linestyle='-', linewidth=2, zorder=2)
        self.ax.plot([0, 0], [-arrow_width, arrow_width], [axis_len - arrow_len, axis_len - arrow_len], color='gray', linestyle='-', linewidth=2, zorder=2)


        # X-axis (φ=0°)
        self.ax.plot([0, axis_len], [0, 0], [0, 0], color='gray', linestyle='-', zorder=2)
        self.ax.text(axis_len * 1.05, 0, 0, "X (φ=0°)", color='black', ha='center')
        # X-axis arrowhead
        self.ax.plot([axis_len - arrow_len, axis_len], [0, 0], [0, 0], color='gray', linestyle='-', linewidth=2, zorder=2)
        self.ax.plot([axis_len - arrow_len, axis_len - arrow_len], [-arrow_width, arrow_width], [0, 0], color='gray', linestyle='-', linewidth=2, zorder=2)
        self.ax.plot([axis_len - arrow_len, axis_len - arrow_len], [0, 0], [-arrow_width, arrow_width], color='gray', linestyle='-', linewidth=2, zorder=2)


        # Y-axis (φ=90°)
        self.ax.plot([0, 0], [0, axis_len], [0, 0], color='gray', linestyle='-', zorder=2)
        self.ax.text(0, axis_len * 1.05, 0, "Y (φ=90°)", color='black', ha='center')
        # Y-axis arrowhead
        self.ax.plot([0, 0], [axis_len - arrow_len, axis_len], [0, 0], color='gray', linestyle='-', linewidth=2, zorder=2)
        self.ax.plot([-arrow_width, arrow_width], [axis_len - arrow_len, axis_len - arrow_len], [0, 0], color='gray', linestyle='-', linewidth=2, zorder=2)
        self.ax.plot([0, 0], [axis_len - arrow_len, axis_len - arrow_len], [-arrow_width, arrow_width], color='gray', linestyle='-', linewidth=2, zorder=2)


        # Add color bar
        if hasattr(self, 'colorbar') and self.colorbar.ax is not None:
            self.colorbar.update_normal(surf)
        else:
            self.colorbar = self.figure.colorbar(surf, ax=self.ax, shrink=0.6, aspect=10)
            self.colorbar.set_label('Gain (dB)')

        # Set view angle and title
        self.ax.view_init(elev=self.elevation, azim=self.azimuth)
        self.ax.set_title(f"3D Pattern @ {plot['freq_text']}")
        
        # Set axis limits
        self.ax.set_box_aspect([1, 1, 1])
        lim = (-max_r, max_r)
        self.ax.set_xlim(lim)
        self.ax.set_ylim(lim)
        self.ax.set_zlim(lim)
        
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
                'freq_text': self.freq_combo.currentText(),
                'polarization': self.polarization_combo.currentText(),
                'plane_type': self.plane_type_combo.currentText(),
                'plane_angle': float(self.plane_angle_combo.currentText()),
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
            'freq_text': self.freq_combo.currentText(),
            'polarization': self.polarization_combo.currentText(),
            'plane_type': self.plane_type_combo.currentText(),
            'plane_angle': float(self.plane_angle_combo.currentText()),
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
            self.plane_type_combo.setCurrentText(plot['plane_type'])
            self.plane_angle_combo.setCurrentText(str(int(plot['plane_angle'])))
            self.line_style_combo.setCurrentText(plot['line_style'])
            self.line_width_spin.setValue(plot['line_width'])
            self.current_color = plot['color']
            self.normalize_cb.setChecked(plot['normalized'])
            self.update_plot()

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
            self.lang.get('import_image'),
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

        if plane_type == 'Theta':
            # Recreate the logic from excel_reader's debug log for Theta cut
            phi_angles = self.data_reader.phi_angles_map[self.data_reader.frequencies[freq_idx]]
            theta_angles = self.data_reader.theta_angles_map[self.data_reader.frequencies[freq_idx]]
            
            primary_phi_idx = min(range(len(phi_angles)), key=lambda i: abs(phi_angles[i] - plane_angle))
            opposite_phi_angle_req = plane_angle + 180
            search_phi_angle = opposite_phi_angle_req - 360 if opposite_phi_angle_req > 180 else opposite_phi_angle_req
            opposite_phi_idx = min(range(len(phi_angles)), key=lambda i: abs(phi_angles[i] - search_phi_angle))

            gains_0_to_180 = self.data_reader.gains[self.data_reader.frequencies[freq_idx]][:, primary_phi_idx]
            gains_181_to_360 = self.data_reader.gains[self.data_reader.frequencies[freq_idx]][:, opposite_phi_idx][::-1]

            if plot['normalized']:
                # To normalize correctly, we must combine, normalize, then split back.
                combined_gains = np.concatenate((gains_0_to_180, gains_181_to_360))
                normalized_gains = self.data_reader.normalize_data(combined_gains)
                gains_0_to_180 = normalized_gains[:len(gains_0_to_180)]
                gains_181_to_360 = normalized_gains[len(gains_0_to_180):]
            else:
                # Ensure gains are numpy arrays for consistency
                gains_0_to_180 = np.array(gains_0_to_180)
                gains_181_to_360 = np.array(gains_181_to_360)


            for i, gain in enumerate(gains_0_to_180):
                display_angle = theta_angles[i]
                table_data.append([display_angle, f"({theta_angles[i]}, {phi_angles[primary_phi_idx]})", f"{gain:.2f}"])
            
            reversed_thetas = theta_angles[::-1]
            for i, gain in enumerate(gains_181_to_360):
                # The display angle for the second half is the reflection
                display_angle = 360 - reversed_thetas[i]
                table_data.append([display_angle, f"({reversed_thetas[i]}, {phi_angles[opposite_phi_idx]})", f"{gain:.2f}"])

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