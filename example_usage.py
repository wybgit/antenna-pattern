#!/usr/bin/env python3
"""
天线方向图工具使用示例
演示如何使用新的多格式支持功能
"""

import sys
import os
sys.path.append('.')

from utils.excel_reader import AntennaDataReader
import matplotlib.pyplot as plt
import numpy as np

def example_load_and_plot():
    """示例：加载数据并绘制方向图"""
    
    print("=== 天线方向图工具使用示例 ===\n")
    
    # 示例1：加载新格式文件
    print("1. 加载矩阵格式文件 (3D-FREQ2.xlsx)")
    try:
        reader_new = AntennaDataReader('demo/3D-FREQ2.xlsx', debug=False)
        print(f"   ✓ 文件格式: {reader_new.file_format}")
        print(f"   ✓ 频率列表: {reader_new.get_frequencies()} MHz")
        print(f"   ✓ 数据规模: {len(reader_new.get_theta_angles())}×{len(reader_new.get_phi_angles())}")
    except Exception as e:
        print(f"   ✗ 加载失败: {e}")
        return
    
    # 示例2：加载传统格式文件
    print("\n2. 加载传统格式文件 (3D-FREQ.xlsx)")
    try:
        reader_old = AntennaDataReader('demo/3D-FREQ.xlsx', debug=False)
        print(f"   ✓ 文件格式: {reader_old.file_format}")
        print(f"   ✓ 频率列表: {reader_old.get_frequencies()} MHz")
        print(f"   ✓ 数据规模: {len(reader_old.get_theta_angles())}×{len(reader_old.get_phi_angles())}")
    except Exception as e:
        print(f"   ✗ 加载失败: {e}")
        return
    
    # 示例3：绘制对比图
    print("\n3. 绘制两种格式数据的对比图")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10), subplot_kw=dict(projection='polar'))
    fig.suptitle('天线方向图对比 - 新格式 vs 传统格式', fontsize=16)
    
    # 新格式数据绘图
    freq_idx = 0
    
    # 新格式 - Theta切面
    theta_data_new = reader_new.get_gain_data_theta_cut(freq_idx, 0)  # phi=0°
    if theta_data_new is not None:
        angles = np.linspace(0, 2*np.pi, len(theta_data_new), endpoint=False)
        axes[0,0].plot(angles, theta_data_new, 'b-', linewidth=2)
        axes[0,0].set_title('新格式 - Theta切面 (Phi=0°)')
        axes[0,0].grid(True)
    
    # 新格式 - Phi切面
    phi_data_new = reader_new.get_gain_data_phi_cut(freq_idx, 90)  # theta=90°
    if phi_data_new is not None:
        phi_angles = np.array(reader_new.get_phi_angles())
        phi_angles_rad = np.deg2rad(phi_angles)
        # 扩展到360度
        full_angles = np.concatenate([phi_angles_rad, phi_angles_rad + np.pi])
        full_data = np.concatenate([phi_data_new, phi_data_new])
        axes[0,1].plot(full_angles, full_data, 'b-', linewidth=2)
        axes[0,1].set_title('新格式 - Phi切面 (Theta=90°)')
        axes[0,1].grid(True)
    
    # 传统格式数据绘图
    # 传统格式 - Theta切面
    theta_data_old = reader_old.get_gain_data_theta_cut(freq_idx, 0)  # phi=0°
    if theta_data_old is not None:
        angles = np.linspace(0, 2*np.pi, len(theta_data_old), endpoint=False)
        axes[1,0].plot(angles, theta_data_old, 'r-', linewidth=2)
        axes[1,0].set_title('传统格式 - Theta切面 (Phi=0°)')
        axes[1,0].grid(True)
    
    # 传统格式 - Phi切面
    phi_data_old = reader_old.get_gain_data_phi_cut(freq_idx, 90)  # theta=90°
    if phi_data_old is not None:
        phi_angles = np.array(reader_old.get_phi_angles())
        phi_angles_rad = np.deg2rad(phi_angles)
        # 扩展到360度
        full_angles = np.concatenate([phi_angles_rad, phi_angles_rad + np.pi])
        full_data = np.concatenate([phi_data_old, phi_data_old])
        axes[1,1].plot(full_angles, full_data, 'r-', linewidth=2)
        axes[1,1].set_title('传统格式 - Phi切面 (Theta=90°)')
        axes[1,1].grid(True)
    
    plt.tight_layout()
    plt.savefig('format_comparison.png', dpi=150, bbox_inches='tight')
    print("   ✓ 对比图已保存: format_comparison.png")
    
    # 示例4：数据信息对比
    print("\n4. 数据信息对比")
    print("   新格式文件:")
    freq_info_new = reader_new.get_frequency_data(0)
    if freq_info_new:
        print(f"     - 频率: {freq_info_new['frequency']} MHz")
        print(f"     - Theta范围: {freq_info_new['theta_range'][0]:.1f}° 到 {freq_info_new['theta_range'][1]:.1f}°")
        print(f"     - Phi范围: {freq_info_new['phi_range'][0]:.1f}° 到 {freq_info_new['phi_range'][1]:.1f}°")
        print(f"     - 增益范围: {freq_info_new['gain_range'][0]:.1f} 到 {freq_info_new['gain_range'][1]:.1f} dB")
    
    print("   传统格式文件:")
    freq_info_old = reader_old.get_frequency_data(0)
    if freq_info_old:
        print(f"     - 频率: {freq_info_old['frequency']} MHz")
        print(f"     - Theta范围: {freq_info_old['theta_range'][0]:.1f}° 到 {freq_info_old['theta_range'][1]:.1f}°")
        print(f"     - Phi范围: {freq_info_old['phi_range'][0]:.1f}° 到 {freq_info_old['phi_range'][1]:.1f}°")
        print(f"     - 增益范围: {freq_info_old['gain_range'][0]:.1f} 到 {freq_info_old['gain_range'][1]:.1f} dB")
    
    print("\n=== 示例完成 ===")
    print("现在可以使用GUI工具 (python main.py) 来交互式地处理这些文件")

def example_gui_usage():
    """示例：GUI使用说明"""
    print("\n=== GUI使用说明 ===")
    print("1. 启动GUI: python main.py")
    print("2. 点击'导入数据'按钮选择Excel文件")
    print("3. 程序会自动检测文件格式并加载数据")
    print("4. 在'曲线设置'标签页中:")
    print("   - 选择频率点")
    print("   - 选择切面类型 (Theta/Phi)")
    print("   - 选择切面角度")
    print("   - 设置曲线样式")
    print("5. 在'视图设置'标签页中:")
    print("   - 切换2D/3D视图")
    print("   - 调整坐标轴设置")
    print("   - 控制增益范围")
    print("6. 在'导出设置'标签页中:")
    print("   - 设置图表标题")
    print("   - 调整DPI")
    print("   - 保存图片")

if __name__ == '__main__':
    example_load_and_plot()
    example_gui_usage()