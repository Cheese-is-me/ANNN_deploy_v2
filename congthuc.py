import numpy as np

class WaterSecurityIndicators:
    def __init__(self, silent=False):
        self.results = {}
        self.silent = silent

    def display_info(self, index, formula, unit, explanation):
        if not self.silent:
            print(f"--- Chỉ số {index} ---")
            print(f"Công thức: {formula}")
            print(f"Đơn vị: {unit}")
            print(f"Diễn giải biến: {explanation}")
            print("-" * 20)

    # --- Nhóm 1: Tiềm năng nguồn nước ---
    def calculate_idx_1(self, Q_tb, F):
        """Mô đun dòng chảy năm"""
        res = (Q_tb * 1000) / F
        self.display_info(1, "M0 = (Q_tb * 1000) / F", "l/s.km2", 
                         "Q_tb: Lưu lượng dòng chảy trung bình năm (m3/s); F: Diện tích lưu vực (km2)")
        return res

    def calculate_idx_2(self, Q_tb_kiet, F):
        """Mô đun dòng chảy mùa kiệt"""
        res = (Q_tb_kiet * 1000) / F
        self.display_info(2, "M_kiet = (Q_tb_kiet * 1000) / F", "l/s.km2", 
                         "Q_tb_kiet: Lưu lượng dòng chảy trung bình mùa kiệt (m3/s); F: Diện tích lưu vực (km2)")
        return res

    def calculate_idx_3(self, sigma, X_tb):
        """Mức độ biến động dòng chảy kiệt (Cv-kiệt)"""
        res = sigma / X_tb
        self.display_info(3, "Cv_kiet = sigma / X_tb", "Không đơn vị", 
                         "sigma: Độ lệch chuẩn; X_tb: Giá trị trung bình")
        return res

    def calculate_idx_4(self, rain_months):
        """Tổng lượng mưa bình quân năm"""
        res = sum(rain_months) / 12
        self.display_info(4, "X_tb_nam = (X1 + X2 + ... + X12) / 12", "mm", 
                         "X_i: Tổng lượng mưa bình quân tháng i")
        return res

    def calculate_idx_5(self, X_nam_i, X_nam_j):
        """Tỷ lệ % lượng mưa thay đổi qua các năm (BĐKH)"""
        res = ((X_nam_i - X_nam_j) / X_nam_i) * 100
        self.display_info(5, "((X_nam_i - X_nam_j) / X_nam_i) * 100", "%", 
                         "X_nam_i: Lượng mưa năm i; X_nam_j: Lượng mưa năm j")
        return res

    def calculate_idx_6(self, h_nam_i, h_nam_j):
        """Tỷ lệ thay đổi mực nước ngầm"""
        res = ((h_nam_i - h_nam_j) / h_nam_i) * 100
        self.display_info(6, "((h_nam_i - h_nam_j) / h_nam_i) * 100", "%", 
                         "h_nam_i: Mực nước ngầm năm i; h_nam_j: Mực nước ngầm năm j")
        return res

    # Chỉ số 7, 8: Thường là giá trị thu thập trực tiếp
    def info_idx_7(self, V_reservoirs):
        self.display_info(7, "V_tru_luong", "10^6 m3", "Trữ lượng nước trong các hồ chứa lớn tại đầu mùa kiệt")
        return V_reservoirs

    def info_idx_8(self, flood_hours):
        self.display_info(8, "T_ngap_lut", "Giờ", "Thời gian ngập lụt trung bình hàng năm")
        return flood_hours

    def calculate_idx_9(self, X, X_mean, sigma):
        """Chỉ số hạn hán (SPI)"""
        res = (X - X_mean) / sigma
        self.display_info(9, "SPI = (X - X_mean) / sigma", "Không đơn vị", 
                         "X: Lượng mưa tính toán; X_mean: Lượng mưa TB; sigma: Độ lệch chuẩn")
        return res

    # Chỉ số 10: Xâm nhập mặn (WSI3) - Thường lấy từ trạm quan trắc
    def info_idx_10(self, salinity_val):
        self.display_info(10, "WSI3", "‰", "Mức độ ảnh hưởng của xâm nhập mặn")
        return salinity_val

    def calculate_idx_11(self, K, k):
        """Chất lượng nước mặt"""
        res = (K / k) * 100
        self.display_info(11, "P_cln = (K / k) * 100", "%", 
                         "K: Số lần vượt ngưỡng QC 08/2023; k: Tổng số lần lấy mẫu")
        return res

    def calculate_idx_12(self, H, h):
        """Mức độ hài lòng về chất lượng nước"""
        res = (H / h) * 100
        self.display_info(12, "P_hai_long = (H / h) * 100", "%", 
                         "H: Số hộ KHÔNG hài lòng; h: Tổng số hộ được cấp nước")
        return res

    # --- Nhóm 2: Hạ tầng & Khả năng tiếp cận ---
    def calculate_idx_13(self, W, w):
        """Năng lực cấp nước"""
        res = W / w
        self.display_info(13, "Cap_nuoc = W / w", "m3/người/ngày", 
                         "W: Tổng công suất cấp nước; w: Tổng dân số")
        return res

    def calculate_idx_14(self, M_xc, m):
        """Tình trạng công trình khai thác"""
        res = M_xc / m
        self.display_info(14, "Tinh_trang = M_xc / m", "Tỷ lệ", 
                         "M_xc: Số công trình xuống cấp; m: Tổng số công trình")
        return res

    def calculate_idx_15(self, N, n):
        """Mức độ ổn định hệ thống (số ngày mất nước)"""
        res = N / n
        self.display_info(15, "On_dinh = N / n", "ngày/năm", 
                         "N: Số ngày mất nước không kế hoạch; n: Tổng số ngày trong năm")
        return res

    def calculate_idx_16(self, P_xl, P):
        """Khả năng tiếp cận nước sạch"""
        res = (P_xl / P) * 100
        self.display_info(16, "P_tiep_can = (P_xl / P) * 100", "%", 
                         "P_xl: Số người dân được cấp nước sạch; P: Tổng dân số khu vực")
        return res

    # --- Nhóm 3: Hộ sử dụng nước ---
    def calculate_idx_17(self, S, S_tn):
        """Khả năng chi trả"""
        res = (S / S_tn) * 100
        self.display_info(17, "Chi_tra = (S / S_tn) * 100", "%", 
                         "S: Chi phí tiền nước; S_tn: Tổng thu nhập hộ dân")
        return res

    def calculate_idx_18(self, S_cham, W_total):
        """Khó khăn trong chi trả"""
        res = (S_cham / W_total) * 100
        self.display_info(18, "Cham_tra = (S_cham / W) * 100", "%", 
                         "S_cham: Số hộ chậm trả tiền nước; W: Tổng số hộ được cấp nước")
        return res

    def calculate_idx_19(self, PA, W_total):
        """Mức độ hài lòng (qua khiếu nại)"""
        res = (PA / W_total) * 100
        self.display_info(19, "Phan_anh = (PA / W) * 100", "%", 
                         "PA: Số hộ phản ánh, khiếu nại; W: Tổng số hộ được cấp nước")
        return res

    def info_idx_20(self, demand_increase):
        """Nhu cầu tương lai"""
        self.display_info(20, "Nhu_cau_tuong_lai", "%", "Mức độ gia tăng nhu cầu dùng nước trong 2-5 năm tới")
        return demand_increase

    # --- Nhóm 4: Tính công bằng & Phúc lợi ---
    def calculate_idx_21(self, TC_dt, TC_nt):
        """Tính công bằng Đô thị - Nông thôn"""
        res = (TC_dt / TC_nt) * 100
        self.display_info(21, "Cong_bang = (TC_dt / TC_nt) * 100", "%", 
                         "TC_dt: % hộ đô thị tiếp cận nước sạch; TC_nt: % hộ nông thôn tiếp cận nước sạch")
        return res

    def calculate_idx_22(self, Z, z_total):
        """Mức độ quan tâm của chính quyền"""
        res = (Z / z_total) * 100
        self.display_info(22, "Quan_tam = (Z / z) * 100", "%", 
                         "Z: Số văn bản hướng dẫn ANNN; z: Tổng số văn bản liên quan cấp nước")
        return res

    def calculate_idx_23(self, P_school, p_total):
        """Tiếp cận nước sạch tại trường học"""
        res = (P_school / p_total) * 100
        self.display_info(23, "Truong_hoc_nuoc = (P / p) * 100", "%", 
                         "P: Số trường có nước sạch thường xuyên; p: Tổng số trường học")
        return res

    def calculate_idx_24(self, Q_school, p_total):
        """Vệ sinh đạt chuẩn tại trường học"""
        res = (Q_school / p_total) * 100
        self.display_info(24, "Truong_hoc_vsinh = (Q / p) * 100", "%", 
                         "Q: Số trường có khu vệ sinh/rửa tay đạt chuẩn; p: Tổng số trường học")
        return res

# --- Ví dụ sử dụng ---
calc = WaterSecurityIndicators()