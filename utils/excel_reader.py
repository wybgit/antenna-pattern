import pandas as pd
import numpy as np
import os

class AntennaDataReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        self.frequencies = []
        self.theta_angles = []
        self.phi_angles = []
        self.gains = {}
        self.polarizations = []  # Add polarization tracking
        self.load_data()
        
    def load_data(self):
        """加载数据文件"""
        ext = os.path.splitext(self.file_path)[1].lower()
        try:
            if ext == '.csv':
                self.data = pd.read_csv(self.file_path, encoding='utf-8-sig')  # Use UTF-8 with BOM
            else:
                self.data = pd.read_excel(self.file_path)
            self.process_data()
        except Exception as e:
            raise Exception(f"Error loading file: {str(e)}")
        
    def process_data(self):
        """处理数据，提取频率、角度和增益信息"""
        try:
            # 初始化数据结构
            self.frequencies = []
            self.theta_angles = []
            self.phi_angles = []
            self.gains = {}
            self.polarizations = []
            
            # 查找频率行
            freq_row = None
            for i, row in self.data.iterrows():
                if isinstance(row.iloc[2], str) and 'Frequency' in row.iloc[2]:
                    freq_row = i
                    break
            
            if freq_row is None:
                raise Exception("Cannot find frequency data")
            
            # 提取频率信息
            freqs = self.data.iloc[freq_row+1:freq_row+2, 2:].values[0]
            self.frequencies = [float(f) for f in freqs if pd.notna(f) and isinstance(f, (int, float))]
            
            # 提取phi角度
            phi_row = freq_row - 1
            phi_angles = self.data.iloc[phi_row, 3:16].values
            self.phi_angles = [float(p) for p in phi_angles if pd.notna(p)]
            
            # 处理每个极化和theta角度的数据
            current_polarization = None
            current_theta = None
            
            for i, row in self.data.iterrows():
                # 检查是否是极化标记行
                if pd.notna(row.iloc[0]) and row.iloc[0] == "Polarization":
                    current_polarization = "Theta" if "Theta" in str(row.iloc[1]) else "Phi"
                    if current_polarization not in self.polarizations:
                        self.polarizations.append(current_polarization)
                    continue
                
                # 检查是否是新的theta角度
                if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == "Theta":
                    continue
                    
                if pd.notna(row.iloc[1]):
                    try:
                        theta = float(row.iloc[1])
                        current_theta = theta
                        if theta not in self.theta_angles:
                            self.theta_angles.append(theta)
                        if theta not in self.gains:
                            self.gains[theta] = {}
                    except:
                        continue
                
                # 提取增益数据
                if pd.notna(row.iloc[2]) and current_theta is not None:
                    try:
                        gains = row.iloc[3:16].values.astype(float)
                        if current_polarization not in self.gains[current_theta]:
                            self.gains[current_theta][current_polarization] = {}
                        self.gains[current_theta][current_polarization] = gains
                    except:
                        continue
            
            # 排序角度列表
            self.theta_angles = sorted(self.theta_angles)
            
        except Exception as e:
            raise Exception(f"Error processing data: {str(e)}")
        
    def get_frequencies(self):
        """获取所有频率点"""
        return self.frequencies
        
    def get_theta_angles(self):
        """获取所有theta角度"""
        return self.theta_angles
        
    def get_phi_angles(self):
        """获取所有phi角度"""
        return self.phi_angles
        
    def get_polarizations(self):
        """获取所有极化方式"""
        return self.polarizations
        
    def get_gain_data(self, frequency_idx, theta_angle=None, polarization="Theta"):
        """获取指定频率、theta角度和极化方式的增益数据"""
        if theta_angle is None:
            # 返回所有theta角度的数据
            gains = []
            for theta in self.theta_angles:
                if theta in self.gains and polarization in self.gains[theta]:
                    gains.append(self.gains[theta][polarization][frequency_idx])
            return np.array(gains)
        else:
            # 返回指定theta角度的数据
            if theta_angle in self.gains and polarization in self.gains[theta_angle]:
                return self.gains[theta_angle][polarization]
            return None
        
    def normalize_data(self, data):
        """归一化数据"""
        if data is None:
            return None
        return data - np.max(data)  # dB数据的归一化
        
    def get_angles_in_radians(self, angles):
        """将角度转换为弧度"""
        return np.deg2rad(angles) 