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
        self.polarizations = ['Total']  # Only support Total polarization
        self.theta_angles_map = {}
        self.phi_angles_map = {}
        self.total_data = {}  # Store Total data for each frequency
        self.file_format = None  # 'legacy' or 'matrix'
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
                # Read Excel file
                if self.sheet_name is None:
                    # Read first sheet by default
                    excel_data = pd.read_excel(self.file_path, header=None, sheet_name=None)
                    if isinstance(excel_data, dict):
                        # Get first sheet
                        first_sheet_name = list(excel_data.keys())[0]
                        self.data = excel_data[first_sheet_name]
                        if self.debug:
                            print(f"[*] Reading first sheet: {first_sheet_name}")
                    else:
                        self.data = excel_data
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
        Process data from CSV or Excel with automatic format detection:
        - Legacy format: Traditional structure with "Theta Angle (degree)" headers
        - Matrix format: New 3D-FREQ2.xlsx style with matrix layout
        """
        if self.debug:
            print("\n[*] --- Starting Data Processing (Auto-detect format) ---")

        # Detect file format
        self.file_format = self._detect_file_format()
        
        if self.debug:
            print(f"[*] Detected file format: {self.file_format}")
        
        if self.file_format == 'matrix':
            self._process_matrix_format()
        else:
            self._process_legacy_format()
        
        if not self.frequencies:
            raise Exception("No valid frequency data found. Please check the file format.")
        
        # Set up default data using first frequency
        first_freq = sorted(self.frequencies)[0]
        
        if first_freq in self.total_data:
            default_data = self.total_data[first_freq]
            self.theta_angles = default_data['theta_angles']
            self.phi_angles = default_data['phi_angles']
            self.theta_angles_map[first_freq] = default_data['theta_angles']
            self.phi_angles_map[first_freq] = default_data['phi_angles']
            self.gains[first_freq] = default_data['gains']
        
        if self.debug:
            print("\n[*] --- Data Processing Finished ---")
            print(f"[*] Found frequencies: {sorted(self.frequencies)}")
            print(f"[*] Using default frequency: {first_freq} MHz")
            print(f"[*] Default theta angles: {len(self.theta_angles)} angles")
            print(f"[*] Default phi angles: {len(self.phi_angles)} angles")
    
    def _detect_file_format(self):
        """
        Detect file format based on structure:
        - Matrix format: Has 'Freqency' and 'Phi' in row 1, large matrix structure
        - Legacy format: Has 'Theta Angle (degree)' headers in specific positions
        """
        if len(self.data) < 2:
            return 'legacy'
        
        # Check for matrix format indicators
        second_row = self.data.iloc[1]
        has_frequency_phi = False
        
        for col_idx in range(min(3, len(second_row))):
            cell_val = str(second_row.iloc[col_idx]).strip() if pd.notna(second_row.iloc[col_idx]) else ''
            if 'freqency' in cell_val.lower() or 'phi' in cell_val.lower():
                has_frequency_phi = True
                break
        
        # Check if it's a large matrix (typical of matrix format)
        is_large_matrix = len(self.data) > 300 and len(self.data.columns) > 300
        
        if has_frequency_phi and is_large_matrix:
            return 'matrix'
        else:
            return 'legacy'
    
    def _process_matrix_format(self):
        """
        Process matrix format data (3D-FREQ2.xlsx style):
        - Row 1: Contains theta angles (starting from column 2)
        - Row 2: Headers including 'Freqency', 'Phi', and theta angle values
        - Data rows: Frequency, Phi angle, and gain values
        """
        if self.debug:
            print("[*] Processing matrix format data")
        
        self.frequencies = []
        self.theta_angles_map = {}
        self.phi_angles_map = {}
        self.gains = {}
        self.total_data = {}
        
        # Extract theta angles from row 2 (starting from column 2)
        header_row = self.data.iloc[1]
        theta_angles = []
        
        for col_idx in range(2, len(header_row)):
            cell_val = header_row.iloc[col_idx]
            if pd.isna(cell_val):
                break
            try:
                # Skip text headers
                if isinstance(cell_val, str):
                    continue
                theta_val = float(cell_val)
                theta_angles.append(np.degrees(theta_val))  # Convert from radians to degrees
            except (ValueError, TypeError):
                break
        
        if self.debug:
            print(f"[*] Extracted {len(theta_angles)} theta angles from header")
            print(f"[*] Theta range: {theta_angles[0]:.1f}° to {theta_angles[-1]:.1f}°")
        
        # Process data rows (starting from row 2, index 2)
        data_by_frequency = {}
        
        for row_idx in range(2, len(self.data)):
            row = self.data.iloc[row_idx]
            
            try:
                # Extract frequency (column 0)
                frequency = float(row.iloc[0]) / 1e6  # Convert Hz to MHz
                
                # Extract phi angle (column 1) 
                phi_angle = float(row.iloc[1])
                phi_angle_deg = np.degrees(phi_angle)  # Convert from radians to degrees
                
                # Extract gain values (starting from column 2)
                gain_values = []
                for col_idx in range(2, min(2 + len(theta_angles), len(row))):
                    try:
                        gain_val = float(row.iloc[col_idx])
                        gain_values.append(gain_val)
                    except (ValueError, TypeError):
                        gain_values.append(np.nan)
                
                # Store data by frequency
                if frequency not in data_by_frequency:
                    data_by_frequency[frequency] = {
                        'phi_angles': [],
                        'gains': []
                    }
                
                data_by_frequency[frequency]['phi_angles'].append(phi_angle_deg)
                data_by_frequency[frequency]['gains'].append(gain_values)
                
            except (ValueError, TypeError, IndexError):
                continue
        
        # Convert to final format
        for frequency, freq_data in data_by_frequency.items():
            phi_angles = freq_data['phi_angles']
            gains_matrix = np.array(freq_data['gains'])
            
            # Transpose to match expected format: [theta_idx, phi_idx]
            gains_transposed = gains_matrix.T
            
            self.total_data[frequency] = {
                'theta_angles': theta_angles,
                'phi_angles': phi_angles,
                'gains': gains_transposed
            }
            
            self.frequencies.append(frequency)
            
            if self.debug:
                print(f"[*] Processed frequency {frequency} MHz:")
                print(f"    Phi angles: {len(phi_angles)} ({phi_angles[0]:.1f}° to {phi_angles[-1]:.1f}°)")
                print(f"    Gain matrix shape: {gains_transposed.shape}")
    
    def _process_legacy_format(self):
        """
        Process legacy format data (original 3D-FREQ.xlsx style):
        - Look for "Theta Angle (degree)" headers to identify data blocks
        - Extract frequency and polarization information
        - Only process Total polarization blocks
        """
        if self.debug:
            print("[*] Processing legacy format data")
        
        self.frequencies = []
        self.theta_angles_map = {}
        self.phi_angles_map = {}
        self.gains = {}
        self.total_data = {}
        
        # Find all data blocks by looking for "Theta Angle" rows
        data_blocks = []
        
        for i in range(len(self.data)):
            row = self.data.iloc[i]
            
            # Look for "Theta Angle (degree)" in any column
            for j in range(len(row)):
                cell_val = str(row.iloc[j]).strip() if pd.notna(row.iloc[j]) else ''
                if 'theta angle' in cell_val.lower():
                    # Found a potential data block, extract frequency from the same row
                    frequency = None
                    for k in range(len(row)):
                        try:
                            freq_val = float(row.iloc[k])
                            if 10 <= freq_val <= 100000:  # Reasonable frequency range
                                frequency = freq_val
                                break
                        except (ValueError, TypeError):
                            pass
                    
                    if frequency:
                        # Determine which polarization block this belongs to
                        polarization_type = self._find_polarization_block(i)
                        
                        data_blocks.append({
                            'row': i,
                            'frequency': frequency,
                            'polarization': polarization_type
                        })
                        
                        if self.debug:
                            print(f"[*] Found data block at row {i}: {frequency} MHz ({polarization_type})")
                    break
        
        if self.debug:
            print(f"[*] Found {len(data_blocks)} data blocks")
        
        # Process only Total blocks (filter out other polarizations)
        total_data_blocks = [block for block in data_blocks if block['polarization'] == 'total']
        
        if self.debug:
            print(f"[*] Found {len(total_data_blocks)} Total blocks")
        
        # Process each Total data block
        for block_idx, block_info in enumerate(total_data_blocks):
            row_idx = block_info['row']
            frequency = block_info['frequency']
            
            if self.debug:
                print(f"\n[*] Processing frequency {frequency} MHz at row {row_idx}")
            
            # Determine the end of this data block
            end_row = len(self.data)
            
            # Look for the next data block or polarization change
            for next_block in data_blocks:
                if next_block['row'] > row_idx:
                    end_row = next_block['row']
                    break
            
            # Also check for polarization changes
            for i in range(row_idx + 1, len(self.data)):
                check_row = self.data.iloc[i]
                first_col = str(check_row.iloc[0]).strip().lower() if pd.notna(check_row.iloc[0]) else ''
                if first_col in ['theta', 'phi', 'total']:
                    end_row = min(end_row, i)
                    break
            
            # Extract data from this block
            success, data = self._extract_frequency_data(row_idx, end_row, frequency)
            
            if success:
                self.total_data[frequency] = data
                self.frequencies.append(frequency)
                if self.debug:
                    print(f"[*] Successfully processed frequency {frequency} MHz")
            else:
                if self.debug:
                    print(f"[*] Failed to process frequency {frequency} MHz")
    
    def _find_polarization_block(self, row_idx):
        """Find which polarization block a row belongs to"""
        polarization_type = 'unknown'
        
        # Look backwards to find the most recent polarization identifier
        for i in range(row_idx, -1, -1):
            if i < len(self.data):
                row = self.data.iloc[i]
                first_col = str(row.iloc[0]).strip().lower() if pd.notna(row.iloc[0]) else ''
                if first_col in ['total', 'theta', 'phi']:
                    polarization_type = first_col
                    break
        
        return polarization_type
    
    def _extract_frequency_data(self, start_row, end_row, frequency):
        """Extract frequency data from a data block"""
        try:
            # The start_row contains "Theta Angle (degree)" and frequency
            header_row = self.data.iloc[start_row]
            
            # Extract Phi angles from the header row (starting from column 3)
            phi_angles = []
            for col_idx in range(3, len(header_row)):
                try:
                    cell_val = header_row.iloc[col_idx]
                    if pd.isna(cell_val):
                        break
                    # Skip text headers
                    if isinstance(cell_val, str):
                        continue
                    phi_val = float(cell_val)
                    phi_angles.append(phi_val)
                except (ValueError, TypeError):
                    break
            
            if self.debug:
                print(f"[*] Extracted {len(phi_angles)} Phi angles: {phi_angles[:10]}...")
            
            # Data starts 2 rows after the header
            data_start_row = start_row + 2
            
            theta_angles_for_freq = []
            gains_for_freq = []
            
            # Process data rows
            for j in range(data_start_row, end_row):
                if j >= len(self.data):
                    break
                    
                data_row = self.data.iloc[j]
                
                # Check for end of data (empty row or next block)
                try:
                    # Theta angle is in column 2
                    theta_cell = data_row.iloc[2]
                    if pd.isna(theta_cell):
                        if self.debug:
                            print(f"[*] End of data block at row {j} (NaN theta)")
                        break
                    
                    # Check for next block by looking at first column
                    first_cell = data_row.iloc[0] if not pd.isna(data_row.iloc[0]) else ""
                    first_cell_str = str(first_cell).lower()
                    if first_cell_str in ['total', 'theta', 'phi']:
                        if self.debug:
                            print(f"[*] End of data block at row {j} (found {first_cell_str})")
                        break
                    
                    # Extract theta angle
                    theta_val = float(theta_cell)
                    theta_angles_for_freq.append(theta_val)
                    
                    # Extract gain values (starting from column 3)
                    num_phi = len(phi_angles)
                    gain_values = []
                    for col_idx in range(3, min(3 + num_phi, len(data_row))):
                        try:
                            cell_val = data_row.iloc[col_idx]
                            if pd.isna(cell_val):
                                gain_values.append(np.nan)
                            else:
                                gain_val = float(cell_val)
                                gain_values.append(gain_val)
                        except (ValueError, TypeError):
                            gain_values.append(np.nan)
                    
                    gains_for_freq.append(gain_values)
                    
                except (ValueError, TypeError, IndexError):
                    if self.debug:
                        print(f"[*] End of data block at row {j} (parsing error)")
                    break
            
            # Return data for this frequency
            if theta_angles_for_freq and gains_for_freq:
                data = {
                    'theta_angles': theta_angles_for_freq,
                    'phi_angles': phi_angles,
                    'gains': np.array(gains_for_freq)
                }
                
                if self.debug:
                    print(f"[*] Processed {len(theta_angles_for_freq)} theta angles")
                    print(f"[*] Gain matrix shape: {np.array(gains_for_freq).shape}")
                
                return True, data
            else:
                if self.debug:
                    print(f"[*] No valid data found for frequency {frequency}")
                return False, None
                
        except Exception as e:
            if self.debug:
                print(f"[*] Error extracting data for frequency {frequency}: {e}")
            return False, None

    def get_frequencies(self):
        return sorted(self.frequencies)
        
    def get_theta_angles(self):
        return self.theta_angles
        
    def get_phi_angles(self):
        return self.phi_angles
        
    def get_polarizations(self):
        return self.polarizations
    
    def set_current_frequency(self, frequency_idx):
        """设置当前使用的频率"""
        if frequency_idx < 0 or frequency_idx >= len(self.frequencies):
            return False
            
        frequency = self.frequencies[frequency_idx]
        
        if frequency in self.total_data:
            data = self.total_data[frequency]
            self.theta_angles = data['theta_angles']
            self.phi_angles = data['phi_angles']
            self.theta_angles_map[frequency] = data['theta_angles']
            self.phi_angles_map[frequency] = data['phi_angles']
            self.gains[frequency] = data['gains']
            
            if self.debug:
                print(f"[*] Switched to frequency: {frequency} MHz")
                print(f"[*] Theta angles: {len(self.theta_angles)} angles")
                print(f"[*] Phi angles: {len(self.phi_angles)} angles")
            
            return True
        
        return False
    
    def get_frequency_data(self, frequency_idx):
        """获取指定频率的数据信息"""
        if frequency_idx < 0 or frequency_idx >= len(self.frequencies):
            return None
            
        frequency = self.frequencies[frequency_idx]
        
        if frequency in self.total_data:
            data = self.total_data[frequency]
            return {
                'frequency': frequency,
                'theta_count': len(data['theta_angles']),
                'phi_count': len(data['phi_angles']),
                'theta_range': [min(data['theta_angles']), max(data['theta_angles'])],
                'phi_range': [min(data['phi_angles']), max(data['phi_angles'])],
                'gain_range': [data['gains'].min(), data['gains'].max()]
            }
        
        return None
        
    def get_gain_data_theta_cut(self, frequency_idx, phi_angle, polarization=None):
        """
        获取Theta切面的增益数据.
        为了显示0-360度的完整theta切面，这个函数:
        1. 选择请求的phi角度的数据 (例如 phi=15)，作为0-180度的显示部分.
        2. 选择其相反角度的数据 (phi=-15)，并将其倒序，作为181-360度的显示部分.
        3. 合并两部分数据.
        
        Args:
            frequency_idx: 频率索引
            phi_angle: phi角度
            polarization: 极化类型 (为了向后兼容，但会被忽略，只使用Total数据)
        """
        if frequency_idx < 0 or frequency_idx >= len(self.frequencies):
            return None
            
        frequency = self.frequencies[frequency_idx]
        
        # Get data from Total data structure
        if frequency in self.total_data:
            data = self.total_data[frequency]
            phi_angles = data['phi_angles']
            theta_angles = data['theta_angles']
            gains = data['gains']
        else:
            # Fallback to legacy data structure
            if frequency not in self.gains:
                return None
            phi_angles = self.phi_angles_map[frequency]
            theta_angles = self.theta_angles_map[frequency]
            gains = self.gains[frequency]

        # 1. 找到最接近的主要phi角度的索引
        primary_phi_idx = min(range(len(phi_angles)), key=lambda i: abs(phi_angles[i] - phi_angle))
        
        # 2. 计算相反的phi角度 (负值)
        opposite_phi_angle_req = -phi_angle
                
        # 找到最接近相反角度的索引
        opposite_phi_idx = min(range(len(phi_angles)), key=lambda i: abs(phi_angles[i] - opposite_phi_angle_req))

        # 3. 获取主要角度的增益 (对应界面0-180度)
        gains_0_to_180 = gains[:, primary_phi_idx]
        
        # 4. 获取相反角度的增益 (对应界面181-360度), 不倒序
        gains_181_to_360 = gains[:, opposite_phi_idx]
        
        # 5. 合并数据
        combined_gains = np.concatenate((gains_0_to_180, gains_181_to_360))
        
        # 6. Log详细信息
        if self.debug:
            primary_theta_val = phi_angles[primary_phi_idx]
            opposite_theta_val = phi_angles[opposite_phi_idx]
            
            print(f"\n[*] --- Theta Cut ({phi_angle} deg, {frequency} MHz) Processing ---")
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
        
    def get_gain_data_phi_cut(self, frequency_idx, theta_angle, polarization=None):
        """
        获取Phi切面的增益数据（固定theta角度，phi从0到360度）
        
        Args:
            frequency_idx: 频率索引
            theta_angle: theta角度
            polarization: 极化类型 (为了向后兼容，但会被忽略，只使用Total数据)
        """
        if frequency_idx < 0 or frequency_idx >= len(self.frequencies):
            return None
            
        frequency = self.frequencies[frequency_idx]
        
        # Get data from Total data structure
        if frequency in self.total_data:
            data = self.total_data[frequency]
            phi_angles = data['phi_angles']
            theta_angles = data['theta_angles']
            gains = data['gains']
        else:
            # Fallback to legacy data structure
            if frequency not in self.gains:
                return None
            theta_angles = self.theta_angles_map[frequency]
            phi_angles = self.phi_angles_map[frequency]
            gains = self.gains[frequency]

        # 找到最接近的theta角度
        theta_idx = min(range(len(theta_angles)), key=lambda i: abs(theta_angles[i] - theta_angle))
        
        # 获取该theta角度下所有phi角度的增益数据
        gain_data = gains[theta_idx, :]
        
        if self.debug:
            selected_theta = theta_angles[theta_idx]
            print(f"""
[*] --- Phi Cut ({theta_angle} deg, {frequency} MHz) Processing ---""")
            print(f"[*] Selected Theta angle: {selected_theta} (requested {theta_angle})")
            
            print("[*] Detailed data mapping:")
            print("[*] Display Angle | Source (Phi, Theta) | Gain")
            print("-" * 50)

            for i, gain in enumerate(gain_data):
                display_angle = phi_angles[i]
                source_phi = phi_angles[i]
                print(f"[*] {display_angle:<13} | ({selected_theta:<6}, {source_phi:<4}) | {gain}")
            print("-" * 50)
            
        return gain_data
        
    def get_gain_data(self, frequency_idx, theta_angle=None, polarization=None):
        """
        获取增益数据（兼容旧接口）
        
        Args:
            frequency_idx: 频率索引
            theta_angle: theta角度
            polarization: 极化类型 (为了向后兼容，但会被忽略，只使用Total数据)
        """
        return self.get_gain_data_phi_cut(frequency_idx, theta_angle, polarization)
        
    def normalize_data(self, data):
        if data is None or data.size == 0:
            return None
        return data - np.max(data)
        
    def get_angles_in_radians(self, angles):
        return np.deg2rad(angles)