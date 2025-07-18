class Language:
    def __init__(self):
        self.current = 'zh'  # Default language
        self.translations = {
            'zh': {
                'title': '天线方向图可视化',
                'file': '文件',
                'open': '打开',
                'save': '保存',
                'language': '语言',
                'chinese': '中文',
                'english': 'English',
                'frequency': '频率',
                'plane': '切面',
                'normalize': '归一化',
                'plot_title': '图表标题',
                'dpi': '分辨率(DPI)',
                'save_plot': '保存图片',
                'theta_angle': 'θ角度',
                'phi_angle': 'φ角度',
                'gain': '增益',
                'add_plot': '添加曲线',
                'remove_plot': '删除曲线',
                'curves': '曲线列表',
                'export': '导出',
                'theme': '主题',
                'light': '浅色',
                'dark': '深色',
                'auto': '自动',
                'grid': '网格',
                'legend': '图例',
                'file_filter': '数据文件 (*.csv *.xlsx *.xls)',
                'image_filter': '图片文件 (*.png *.jpg)',
                'error': '错误',
                'file_error': '文件读取错误',
                'plot_style': '绘图样式',
                'line_style': '线型',
                'line_color': '线条颜色',
                'line_width': '线宽',
                'marker': '标记',
                'marker_size': '标记大小',
                'polarization': '极化方式',
                '3d_view': '3D视图',
                'rotate': '旋转',
                'elevation': '仰角',
                'azimuth': '方位角',
                'view_type': '视图类型',
                '2d_view': '2D视图',
                'auto_rotate': '自动旋转',
                'axis_direction': '坐标轴方向',
                'axis_angle': '坐标轴角度',
                'insert_image': '插入图片',
                'remove_image': '移除图片',
                'select_image': '选择图片',
                'image_filter_all': '图片文件 (*.png *.jpg *.jpeg *.bmp)',
                'image_error': '图片加载错误',
                'reset_view': '重置视图',
                'update_plot': '更新图形',
                'save_confirm': '是否保存当前图像？',
                'discard': '放弃',
                'cancel': '取消',
                'min_db': '最小增益(dB)',
                'max_db': '最大增益(dB)',
                'auto_range': '自动范围',
                'modify_size': '修改大小',
                'modify_position': '修改位置',
                'width': '宽度',
                'height': '高度',
                'keep_aspect_ratio': '保持纵横比'
            },
            'en': {
                'title': 'Antenna Pattern Visualization',
                'file': 'File',
                'open': 'Open',
                'save': 'Save',
                'language': 'Language',
                'chinese': '中文',
                'english': 'English',
                'frequency': 'Frequency',
                'plane': 'Plane',
                'normalize': 'Normalize',
                'plot_title': 'Plot Title',
                'dpi': 'Resolution(DPI)',
                'save_plot': 'Save Plot',
                'theta_angle': 'Theta Angle',
                'phi_angle': 'Phi Angle',
                'gain': 'Gain',
                'add_plot': 'Add Plot',
                'remove_plot': 'Remove Plot',
                'curves': 'Curve List',
                'export': 'Export',
                'theme': 'Theme',
                'light': 'Light',
                'dark': 'Dark',
                'auto': 'Auto',
                'grid': 'Grid',
                'legend': 'Legend',
                'file_filter': 'Data Files (*.csv *.xlsx *.xls)',
                'image_filter': 'Image Files (*.png *.jpg)',
                'error': 'Error',
                'file_error': 'File Reading Error',
                'plot_style': 'Plot Style',
                'line_style': 'Line Style',
                'line_color': 'Line Color',
                'line_width': 'Line Width',
                'marker': 'Marker',
                'marker_size': 'Marker Size',
                'polarization': 'Polarization',
                '3d_view': '3D View',
                'rotate': 'Rotate',
                'elevation': 'Elevation',
                'azimuth': 'Azimuth',
                'view_type': 'View Type',
                '2d_view': '2D View',
                'auto_rotate': 'Auto Rotate',
                'reset_view': 'Reset View',
                'update_plot': 'Update Plot',
                'save_confirm': 'Do you want to save the current plot?',
                'discard': 'Discard',
                'cancel': 'Cancel',
                'min_db': 'Min Gain(dB)',
                'max_db': 'Max Gain(dB)',
                'auto_range': 'Auto Range',
                'axis_direction': 'Axis Direction',
                'axis_angle': 'Axis Angle',
                'insert_image': 'Insert Image',
                'remove_image': 'Remove Image',
                'select_image': 'Select Image',
                'image_filter_all': 'Image Files (*.png *.jpg *.jpeg *.bmp)',
                'image_error': 'Image Loading Error',
                'modify_size': 'Modify Size',
                'modify_position': 'Modify Position',
                'width': 'Width',
                'height': 'Height',
                'keep_aspect_ratio': 'Keep Aspect Ratio'
            }
        }
    
    def get(self, key):
        return self.translations[self.current].get(key, key)
    
    def set_language(self, lang):
        if lang in self.translations:
            self.current = lang
            return True
        return False 