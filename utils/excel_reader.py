import pandas as pd
import numpy as np
import os

class AntennaDataReader:
    def __init__(self, file_path, debug=False, sheet_name=None):
        self.file_path = os.path.normpath(file_path)
        self.debug = debug
        self.sheet_name = sheet_name
        if self.debug:
            print(f"[*] Initializing AntennaDataReader for {self.file_path} (Sheet: {self.sheet_name})")
        self.data = None
        self.frequencies = []
        self.theta_angles = []
        self.phi_angles = []
        self.gains = {}
        self.polarizations = ['Total']
        self.theta_angles_map = {}
        self.phi_angles_map = {}
        self.load_data()

    def load_data(self):
        """加载数据文件"""
        if self.debug:
            print(f"[*] Loading data from {self.file_path}")
        ext = os.path.splitext(self.file_path)[1].lower()
        try:
            if ext == '.csv':
                encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']
                for encoding in encodings:
                    try:
                        self.data = pd.read_csv(self.file_path, encoding=encoding, header=None)
                        if self.debug:
                            print(f"[*] Successfully read CSV with encoding: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                if self.data is None:
                    raise Exception("无法以支持的编码方式读取CSV文件")
            else:
                self.data = pd.read_excel(self.file_path, header=None, sheet_name=self.sheet_name)
            
            if self.debug and self.data is not None:
                print("[*] Data loaded successfully. First 5 rows:")
                print(self.data.head())

            self.process_data()
        except Exception as e:
            if self.debug:
                import traceback
                traceback.print_exc()
            raise Exception(f"Error loading file: {str(e)}")

    def process_data(self):
        """
        Process data from CSV or Excel.
        - Find frequency blocks.
        - A block starts with a row containing the frequency in the 2nd column.
        - Phi angles are in the same row, starting from the 4th column.
        - Data rows start 1-2 rows below, with Theta in the 3rd column.
        """
        if self.debug:
            print("\n[*] --- Starting Data Processing ---")

        self.frequencies = []
        self.theta_angles_map = {}
        self.phi_angles_map = {}
        self.gains = {}
        
        i = 0
        while i < len(self.data):
            row = self.data.iloc[i]
            
            try:
                # Check for a potential frequency header row
                # Condition: 2nd cell is numeric (frequency)
                freq_val = float(row.iloc[1])
                
                # Heuristic: Check if there are multiple numeric values after col 3, likely phi angles
                if pd.to_numeric(row.iloc[3:], errors='coerce').notna().sum() > 2:
                    # If the row contains "Total", check if it's followed by "Frequency (MHz)"
                    row_str_list = [str(s).lower() for s in row.tolist()]
                    if 'total' in row_str_list:
                        try:
                            total_index = row_str_list.index('total')
                            # Check if the next cell contains "frequency"
                            if not (total_index + 1 < len(row_str_list) and 'frequency' in row_str_list[total_index + 1]):
                                if self.debug:
                                    print(f"[*] Row {i} contains 'Total' but not 'Frequency (MHz)' next to it. Skipping.")
                                i += 1
                                continue
                        except ValueError:
                            # Should not happen if 'total' is in list, but as a safeguard
                            pass

                    current_freq = freq_val
                    if self.debug:
                        print(f"\n[*] Found frequency block for {current_freq} MHz at row {i}")
                    
                    if current_freq not in self.frequencies:
                        self.frequencies.append(current_freq)
                    
                    # Extract Phi angles from this row (starting at column index 3)
                    phi_angles = [float(p) for p in row.iloc[3:] if pd.notna(p) and isinstance(p, (int, float))]
                    self.phi_angles_map[current_freq] = phi_angles
                    if self.debug:
                        print(f"[*] Extracted Phi angles: {phi_angles}")
                    
                    # Data rows are expected to start 1 or 2 rows below the header
                    # We will search for the first valid data row
                    data_start_row = -1
                    for k in range(1, 4):
                        if i + k < len(self.data):
                            try:
                                # A data row has a numeric theta in column 2
                                float(self.data.iloc[i + k, 2])
                                data_start_row = i + k
                                break
                            except (ValueError, TypeError, IndexError):
                                continue
                    
                    if data_start_row == -1:
                        if self.debug:
                            print(f"[!] Could not find start of data for frequency {current_freq}")
                        i += 1
                        continue

                    theta_angles_for_freq = []
                    gains_for_freq = []
                    
                    j = data_start_row
                    while j < len(self.data):
                        data_row = self.data.iloc[j]
                        
                        # Check for summary section and stop parsing if found
                        try:
                            first_cell_str = str(data_row.iloc[0])
                            if 'totalpoint' in first_cell_str.lower():
                                if self.debug:
                                    print(f"[*] Found summary section at row {j}. Stopping data processing for this block.")
                                break
                        except IndexError:
                            pass

                        try:
                            # A data row should have a numeric theta angle in the 3rd column (index 2)
                            theta_val_candidate = data_row.iloc[2]
                            if pd.isna(theta_val_candidate):
                                if self.debug:
                                    print(f"[*] End of data block for {current_freq} at row {j} (NaN theta).")
                                break

                            theta_val = float(theta_val_candidate)
                            theta_angles_for_freq.append(theta_val)
                            
                            # Gain values start at column index 3
                            num_phi = len(phi_angles)
                            gain_values = data_row.iloc[3:3+num_phi].values.astype(float)
                            gains_for_freq.append(gain_values)
                            
                            j += 1
                        except (ValueError, TypeError, IndexError):
                            if self.debug:
                                print(f"[*] End of data block for {current_freq} at row {j}.")
                            break
                    
                    self.theta_angles_map[current_freq] = theta_angles_for_freq
                    self.gains[current_freq] = np.array(gains_for_freq)
                    if self.debug:
                        print(f"[*] Extracted {len(theta_angles_for_freq)} Theta angles.")
                        print(f"[*] Gain matrix shape: {self.gains[current_freq].shape}")
                        
                    # Found and processed the first data block, so we stop.
                    if self.debug:
                        print("[*] First data block processed. Halting search.")
                    break
            except (ValueError, TypeError, IndexError):
                pass
            
            i += 1

        if not self.frequencies:
            raise Exception("No valid frequency data blocks found. Please check the file format.")

        first_freq = self.frequencies[0]
        self.theta_angles = self.theta_angles_map.get(first_freq, [])
        self.phi_angles = self.phi_angles_map.get(first_freq, [])
        
        if self.debug:
            print("\n[*] --- Data Processing Finished ---")
            print(f"[*] Found frequencies: {self.frequencies}")
            print(f"[*] Using Theta angles from first freq: {self.theta_angles}")
            print(f"[*] Using Phi angles from first freq: {self.phi_angles}")

    def get_frequencies(self):
        return sorted(self.frequencies)
        
    def get_theta_angles(self):
        return self.theta_angles
        
    def get_phi_angles(self):
        return self.phi_angles
        
    def get_polarizations(self):
        return self.polarizations
        
    def get_gain_data_theta_cut(self, frequency_idx, phi_angle, polarization="Total"):
        """
        获取Theta切面的增益数据.
        为了显示0-360度的完整theta切面，这个函数:
        1. 选择请求的phi角度的数据 (例如 phi=15)，作为0-180度的显示部分.
        2. 选择其相反角度的数据 (phi=-15)，并将其倒序，作为181-360度的显示部分.
        3. 合并两部分数据.
        """
        if frequency_idx < 0 or frequency_idx >= len(self.frequencies):
            return None
            
        frequency = self.frequencies[frequency_idx]
        if frequency not in self.gains:
            return None
            
        phi_angles = self.phi_angles_map[frequency]
        theta_angles = self.theta_angles_map[frequency]

        # 1. 找到最接近的主要phi角度的索引
        primary_phi_idx = min(range(len(phi_angles)), key=lambda i: abs(phi_angles[i] - phi_angle))
        
        # 2. 计算相反的phi角度 (负值)
        opposite_phi_angle_req = -phi_angle
                
        # 找到最接近相反角度的索引
        opposite_phi_idx = min(range(len(phi_angles)), key=lambda i: abs(phi_angles[i] - opposite_phi_angle_req))

        # 3. 获取主要角度的增益 (对应界面0-180度)
        gains_0_to_180 = self.gains[frequency][:, primary_phi_idx]
        
        # 4. 获取相反角度的增益 (对应界面181-360度), 不倒序
        gains_181_to_360 = self.gains[frequency][:, opposite_phi_idx]
        
        # 5. 合并数据
        combined_gains = np.concatenate((gains_0_to_180, gains_181_to_360))
        
        # 6. Log详细信息
        if self.debug:
            primary_theta_val = phi_angles[primary_phi_idx]
            opposite_theta_val = phi_angles[opposite_phi_idx]
            
            print(f"\n[*] --- Theta Cut ({phi_angle} deg) Processing ---")
            print(f"[*] Primary Theta angle: {primary_theta_val} (requested {phi_angle}) for 0-180 deg display")
            print(f"[*] Opposite Theta angle: {opposite_theta_val} (requested {opposite_phi_angle_req}) for 181-360 deg display")
            
            print("[*] Detailed data mapping:")
            print("[*] Display Angle | Source (Phi, Theta) | Gain")
            print("-" * 50)

            # Log for 0-180 degrees
            for i, gain in enumerate(gains_0_to_180):
                display_angle = i
                source_phi = theta_angles[i]
                print(f"[*] {display_angle:<13} | ({primary_theta_val:<6}, {theta_angles[i]:<4}) | {gain}")

            # Log for 181-360 degrees
            for i, gain in enumerate(gains_181_to_360):
                display_angle = len(gains_0_to_180) + i
                source_phi = theta_angles[i] # Use normal theta_angles as requested
                print(f"[*] {display_angle:<13} | ({opposite_theta_val:<6}, {theta_angles[i]:<4}) | {gain}")
            print("-" * 50)
            
        return combined_gains
        
    def get_gain_data_phi_cut(self, frequency_idx, theta_angle, polarization="Total"):
        """获取Phi切面的增益数据（固定theta角度，phi从0到360度）"""
        if frequency_idx < 0 or frequency_idx >= len(self.frequencies):
            return None
            
        frequency = self.frequencies[frequency_idx]
        if frequency not in self.gains:
            return None
            
        theta_angles = self.theta_angles_map[frequency]
        phi_angles = self.phi_angles_map[frequency]

        # 找到最接近的theta角度
        theta_idx = min(range(len(theta_angles)), key=lambda i: abs(theta_angles[i] - theta_angle))
        
        # 获取该theta角度下所有phi角度的增益数据
        gains = self.gains[frequency][theta_idx, :]
        
        if self.debug:
            selected_theta = theta_angles[theta_idx]
            print(f"""
[*] --- Phi Cut ({theta_angle} deg) Processing ---""")
            print(f"[*] Selected Theta angle: {selected_theta} (requested {theta_angle})")
            
            print("[*] Detailed data mapping:")
            print("[*] Display Angle | Source (Phi, Theta) | Gain")
            print("-" * 50)

            for i, gain in enumerate(gains):
                display_angle = phi_angles[i]
                source_phi = phi_angles[i]
                print(f"[*] {display_angle:<13} | ({selected_theta:<6}, {source_phi:<4}) | {gain}")
            print("-" * 50)
            
        return gains
        
    def get_gain_data(self, frequency_idx, theta_angle=None, polarization="Total"):
        """获取增益数据（兼容旧接口）"""
        return self.get_gain_data_phi_cut(frequency_idx, theta_angle, polarization)
        
    def normalize_data(self, data):
        if data is None or data.size == 0:
            return None
        return data - np.max(data)
        
    def get_angles_in_radians(self, angles):
        return np.deg2rad(angles)