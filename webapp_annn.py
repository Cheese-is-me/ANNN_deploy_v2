"""
Webapp tính toán chỉ số An ninh nguồn nước sinh hoạt (ANNN SH)
Sử dụng Streamlit để hiển thị bảng dữ liệu có thể chỉnh sửa

Chức năng:
1. Lựa chọn xã/phường khu vực Bắc Bộ muốn tính toán
2. Lựa chọn tính toán cho tất cả hoặc cho 13 chỉ số cơ bản của ANNN
3. Hiển thị bảng dữ liệu tương ứng với xã/phường đã chọn
4. Cho phép người dùng chỉnh sửa dữ liệu trong bảng và lưu lại
5. Tự động cập nhật kết quả tổng hợp khi chỉnh sửa
6. Xuất dữ liệu đã chỉnh sửa ra file CSV
"""
import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
from pathlib import Path
from congthuc import WaterSecurityIndicators

# Khởi tạo calculator từ congthuc.py (silent mode)
calc = WaterSecurityIndicators(silent=True)

# Cấu hình trang
st.set_page_config(
    page_title="Tính toán chỉ số ANNN Sinh hoạt",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1565C0;
        text-align: center;
        padding: 0.5rem 0;
        margin-bottom: 1rem;
    }
    .stDataFrame {
        font-size: 0.85rem;
    }
    .result-card {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #1565C0;
    }
    .warning-card {
        background-color: #FFF8E1;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #FFA000;
    }
    .success-card {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #43A047;
    }
</style>
""", unsafe_allow_html=True)

# ============== DỮ LIỆU CHỈ SỐ ANNN SH ==============

# 24 chỉ số ANNN SH
INDICATORS_DATA = [
    {
        "STT": 1,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Tiềm năng nước mặt (Mô đun dòng chảy năm)",
        "Biến số": "M0",
        "Công thức": "M0 = (Q_tb * 1000) / F",
        "Đơn vị": "l/s.km2",
        "Diễn giải": "Q_tb: Lưu lượng dòng chảy trung bình năm (m3/s); F: Diện tích lưu vực (km2)",
        "Ý nghĩa": "Mô đun dòng chảy năm (M0) thể hiện khả năng sản sinh nước trên lưu vực. M0 càng lớn thể hiện mức độ phong phú, sẵn có của nguồn nước. M0 càng lớn thì mức độ ANNN càng cao.",
        "Biến cần nhập": ["Q_tb", "F"]
    },
    {
        "STT": 2,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Tiềm năng nước mặt (Mô đun dòng chảy mùa kiệt)",
        "Biến số": "M_KIET",
        "Công thức": "M_kiet = (Q_tb_kiet * 1000) / F",
        "Đơn vị": "l/s.km2",
        "Diễn giải": "Q_tb_kiet: Lưu lượng dòng chảy trung bình mùa kiệt (m3/s); F: Diện tích lưu vực (km2)",
        "Ý nghĩa": "Mô đun dòng chảy kiệt (Mkiệt) thể hiện khả năng sản sinh nước trên lưu vực trong mùa kiệt. Mkiệt càng nhỏ thể hiện mức độ thiếu hụt nguồn nước càng lớn. Mkiệt càng lớn thì mức độ ANNN (mùa kiệt) càng tốt.",
        "Biến cần nhập": ["Q_tb_kiet", "F"]
    },
    {
        "STT": 3,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Tiềm năng nước mặt (Mức độ biến động dòng chảy kiệt)",
        "Biến số": "CV_KIET",
        "Công thức": "Cv_kiet = sigma / X_tb",
        "Đơn vị": "",
        "Diễn giải": "sigma: Độ lệch chuẩn; X_tb: Giá trị trung bình",
        "Ý nghĩa": "Mức độ biến động dòng chảy mùa kiệt (Cv-kiệt) càng lớn tức độ phân tán của chuỗi số liệu dòng chảy mùa kiệt lớn nên khả năng xuất hiện những đợt hạn cực trị cao. Cv-kiệt càng cao càng mất ANNN",
        "Biến cần nhập": ["sigma", "X_tb"]
    },
    {
        "STT": 4,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Tiềm năng nước mưa",
        "Biến số": "LUONG_MUA_NAM",
        "Công thức": "X_tb_nam = (X1 + X2 + ... + X12) / 12",
        "Đơn vị": "mm",
        "Diễn giải": "X_i: Tổng lượng mưa bình quân tháng i (từ tháng 1 đến tháng 12)",
        "Ý nghĩa": "Tổng lượng nước đến do mưa phân bố ở các địa phương càng lớn thì mức độ ANNN càng cao.",
        "Biến cần nhập": ["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9", "X10", "X11", "X12"]
    },
    {
        "STT": 5,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Xu thế biến đổi lượng mưa dưới tác động của BĐKH",
        "Biến số": "TL_MUA_THAYDOI",
        "Công thức": "((X_nam_i - X_nam_j) / X_nam_i) * 100",
        "Đơn vị": "%",
        "Diễn giải": "X_nam_i: Lượng mưa năm i; X_nam_j: Lượng mưa năm j",
        "Ý nghĩa": "Lượng mưa thay đổi ảnh hưởng đến nguồn nước trong khu vực, nếu lượng mưa tăng sẽ tăng thêm trữ lượng nước trên các lưu vực sông",
        "Biến cần nhập": ["X_nam_i", "X_nam_j"]
    },
    {
        "STT": 6,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Xu thế thay đổi mực nước ngầm",
        "Biến số": "TL_NUOCNGAM_THAYDOI",
        "Công thức": "((h_nam_i - h_nam_j) / h_nam_i) * 100",
        "Đơn vị": "%",
        "Diễn giải": "h_nam_i: Mực nước ngầm năm i; h_nam_j: Mực nước ngầm năm j",
        "Ý nghĩa": "Khả năng bổ sung nguồn nước từ nước ngầm, tiềm năng nước ngầm càng lớn mức độ ANNN càng cao.",
        "Biến cần nhập": ["h_nam_i", "h_nam_j"]
    },
    {
        "STT": 7,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Tổng lượng nước trong các hồ chứa phục vụ cấp nước sinh hoạt",
        "Biến số": "TRULUONG_HOCHUA",
        "Công thức": "V_tru_luong",
        "Đơn vị": "10^6 m3",
        "Diễn giải": "V_reservoirs: Trữ lượng nước trong các hồ chứa lớn tại đầu mùa kiệt",
        "Ý nghĩa": "Trên địa bàn có nhiều hồ chứa (thủy lợi/ thủy điện) thì khả năng giữ nước lại trên lưu vực càng cao, tăng mức đảm bảo cung cấp nước đáp ứng các nhu cầu sử dụng tại địa phương, tỷ lệ này cao chứng tỏ mức độ ANNN đối với vùng được hưởng lợi tốt. Lượng nước trong hồ chứa tại thời điểm đánh giá càng nhiều sẽ đảm bảo đủ nguồn nước cấp cho sinh hoạt",
        "Biến cần nhập": ["V_reservoirs"]
    },
    {
        "STT": 8,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Thời gian ngập lụt trung bình hàng năm",
        "Biến số": "THOIGIAN_NGAPLUT",
        "Công thức": "T_ngap_lut",
        "Đơn vị": "Giờ",
        "Diễn giải": "flood_hours: Thời gian ngập lụt trung bình hàng năm",
        "Ý nghĩa": "Đánh giá nguy cơ ngập lụt làm ảnh hưởng đến nguồn nước sinh hoạt",
        "Biến cần nhập": ["flood_hours"]
    },
    {
        "STT": 9,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Mức độ hạn hán trong khu vực",
        "Biến số": "SPI",
        "Công thức": "SPI = (X - X_mean) / sigma",
        "Đơn vị": "",
        "Diễn giải": "X: Lượng mưa tính toán; X_mean: Lượng mưa TB; sigma_spi: Độ lệch chuẩn",
        "Ý nghĩa": "Địa phương có mức độ hạn hán nhiều ảnh hưởng nhiều đến khả năng cung cấp nước phục vụ cho các ngành. Chỉ số này càng cao thì ANNN càng thấp.",
        "Biến cần nhập": ["X", "X_mean", "sigma_spi"]
    },
    {
        "STT": 10,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Mức độ xâm nhập mặn",
        "Biến số": "WSI3",
        "Công thức": "WSI3",
        "Đơn vị": "‰",
        "Diễn giải": "salinity_val: Mức độ ảnh hưởng của xâm nhập mặn",
        "Ý nghĩa": "Mức độ nhiễm mặn càng lớn ảnh hưởng đến nguồn nước cấp cho người dân và các nhà máy nước sử dụng nguồn nước sông",
        "Biến cần nhập": ["salinity_val"]
    },
    {
        "STT": 11,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Chất lượng nước mặt tại các sông/hồ trong khu vực (xã/phường)",
        "Biến số": "SO_LAN_VUOT_NGUONG",
        "Công thức": "P_cln = (K / k) * 100",
        "Đơn vị": "%",
        "Diễn giải": "K: Số lần vượt ngưỡng QC 08/2023; k: Tổng số lần lấy mẫu",
        "Ý nghĩa": "Thể hiện khả năng nguồn nước tự nhiên trong khu vực có đáp ứng được cho sinh hoạt",
        "Biến cần nhập": ["K", "k"]
    },
    {
        "STT": 12,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Mức độ hài lòng của người dân về chất lượng nước sinh hoạt",
        "Biến số": "TL_HAILONG_CLN",
        "Công thức": "P_hai_long = (H / h) * 100",
        "Đơn vị": "%",
        "Diễn giải": "H: Số hộ KHÔNG hài lòng; h: Tổng số hộ được cấp nước",
        "Ý nghĩa": "Mức độ hài lòng của người dân về chất lượng nước sinh hoạt",
        "Biến cần nhập": ["H", "h"]
    },
    {
        "STT": 13,
        "Nhóm chỉ số": "Hạ tầng phân bổ nguồn nước (Khả năng tiếp cận và tính ổn định)",
        "Chỉ thị": "Năng lực cấp nước từ các công trình cấp nước sạch",
        "Biến số": "MUCDO_CONGTRINH",
        "Công thức": "Cap_nuoc = W / w",
        "Đơn vị": "m3/người/ngày",
        "Diễn giải": "W: Tổng công suất cấp nước (m3/ngày); w: Tổng dân số (người)",
        "Ý nghĩa": "Tổng công suất cấp nước của các nhà máy so với tổng dân số có đáp ứng theo quy chuẩn nước sạch thành thị và nông thôn?",
        "Biến cần nhập": ["W_13", "w_13"]
    },
    {
        "STT": 14,
        "Nhóm chỉ số": "Hạ tầng phân bổ nguồn nước (Khả năng tiếp cận và tính ổn định)",
        "Chỉ thị": "Tình trạng các công trình khai thác và cấp nước sinh hoạt trên địa bàn",
        "Biến số": "CONGSUAT_CAPNUOC",
        "Công thức": "Tinh_trang = M_xc / m",
        "Đơn vị": "Tỷ lệ",
        "Diễn giải": "M_xc: Số công trình xuống cấp; m: Tổng số công trình",
        "Ý nghĩa": "Tình trạng các công trình khai thác và cấp nước thể hiện sự ổn định, hoàn thiện của các công trình cấp nước đến các hộ dùng nước",
        "Biến cần nhập": ["M_xc", "m"]
    },
    {
        "STT": 15,
        "Nhóm chỉ số": "Hạ tầng phân bổ nguồn nước (Khả năng tiếp cận và tính ổn định)",
        "Chỉ thị": "Mức độ ổn định của hệ thống cấp nước sinh hoạt",
        "Biến số": "SO_NGAY_MAT_NUOC",
        "Công thức": "On_dinh = N / n",
        "Đơn vị": "ngày/năm",
        "Diễn giải": "N: Số ngày mất nước không kế hoạch; n: Tổng số ngày trong năm (365)",
        "Ý nghĩa": "Số ngày mất nước trong năm gần đó càng ít thì mức độ ổn định của hệ thống càng cao",
        "Biến cần nhập": ["N", "n"]
    },
    {
        "STT": 16,
        "Nhóm chỉ số": "Hạ tầng phân bổ nguồn nước (Khả năng tiếp cận và tính ổn định)",
        "Chỉ thị": "Khả năng người dân tiếp cận nguồn nước sạch tại địa phương",
        "Biến số": "TL_TIEPCAN_NUOCSACH",
        "Công thức": "P_tiep_can = (P_xl / P) * 100",
        "Đơn vị": "%",
        "Diễn giải": "P_xl: Số người dân được cấp nước sạch; P: Tổng dân số khu vực",
        "Ý nghĩa": "Đánh giá khả năng tiếp cận nguồn nước sạch từng vùng",
        "Biến cần nhập": ["P_xl", "P"]
    },
    {
        "STT": 17,
        "Nhóm chỉ số": "Hộ sử dụng nước",
        "Chỉ thị": "Khả năng chi trả tiền của người dân",
        "Biến số": "TL_TIEN_NUOC",
        "Công thức": "Chi_tra = (S / S_tn) * 100",
        "Đơn vị": "%",
        "Diễn giải": "S: Chi phí tiền nước; S_tn: Tổng thu nhập hộ dân",
        "Ý nghĩa": "Đánh giá khả chi trả tiền nước sạch của người dân",
        "Biến cần nhập": ["S", "S_tn"]
    },
    {
        "STT": 18,
        "Nhóm chỉ số": "Hộ sử dụng nước",
        "Chỉ thị": "Mức độ khó khăn trong chi trả tiền nguồn nước",
        "Biến số": "TL_CHAM_TRA",
        "Công thức": "Cham_tra = (S_cham / W) * 100",
        "Đơn vị": "%",
        "Diễn giải": "S_cham: Số hộ chậm trả tiền nước; W_18: Tổng số hộ được cấp nước",
        "Ý nghĩa": "Đánh giá mức độ khó khăn trong thanh toán/tiếp cận nguồn nước",
        "Biến cần nhập": ["S_cham", "W_18"]
    },
    {
        "STT": 19,
        "Nhóm chỉ số": "Hộ sử dụng nước",
        "Chỉ thị": "Mức độ hài lòng của người dân về nguồn nước sử dụng hiện tại",
        "Biến số": "TL_KHIEUNAI",
        "Công thức": "Phan_anh = (PA / W) * 100",
        "Đơn vị": "%",
        "Diễn giải": "PA: Số hộ phản ánh, khiếu nại; W_19: Tổng số hộ được cấp nước",
        "Ý nghĩa": "Phản ảnh mức độ hài lòng của người dân về nguồn nước",
        "Biến cần nhập": ["PA", "W_19"]
    },
    {
        "STT": 20,
        "Nhóm chỉ số": "Hộ sử dụng nước",
        "Chỉ thị": "Nhu cầu sử dụng nước trong tương lai",
        "Biến số": "MUCDO_GIATANG_NHUCAU",
        "Công thức": "Nhu_cau_tuong_lai",
        "Đơn vị": "%",
        "Diễn giải": "demand_increase: Mức độ gia tăng nhu cầu dùng nước trong 2-5 năm tới (%)",
        "Ý nghĩa": "Đánh giá xu thế thay đổi nhu cầu dùng nước của người dân trong tương lai",
        "Biến cần nhập": ["demand_increase"]
    },
    {
        "STT": 21,
        "Nhóm chỉ số": "Tính công bằng trong sử dụng nguồn nước sinh hoạt và phúc lợi trẻ em",
        "Chỉ thị": "Tính công bằng trong tiếp cận nguồn nước giữa các vùng",
        "Biến số": "TL_TIEPCAN_DOTHI_NONGTHON",
        "Công thức": "Cong_bang = (TC_dt / TC_nt) * 100",
        "Đơn vị": "%",
        "Diễn giải": "TC_dt: % hộ đô thị tiếp cận nước sạch; TC_nt: % hộ nông thôn tiếp cận nước sạch",
        "Ý nghĩa": "Phản ánh tính công bằng trong tiếp cận nguồn nước giữa các vùng",
        "Biến cần nhập": ["TC_dt", "TC_nt"]
    },
    {
        "STT": 22,
        "Nhóm chỉ số": "Tính công bằng trong sử dụng nguồn nước sinh hoạt và phúc lợi trẻ em",
        "Chỉ thị": "Mức độ quan tâm đến ANNN trong chỉ đạo, điều hành",
        "Biến số": "MUCDO_HOANTHIEN_VANBAN",
        "Công thức": "Quan_tam = (Z / z) * 100",
        "Đơn vị": "%",
        "Diễn giải": "Z: Số văn bản hướng dẫn ANNN; z: Tổng số văn bản liên quan cấp nước",
        "Ý nghĩa": "Phản ảnh mức độ quan tâm của các cơ quan chức năng đến cấp nước sinh hoạt",
        "Biến cần nhập": ["Z", "z"]
    },
    {
        "STT": 23,
        "Nhóm chỉ số": "Tính công bằng trong sử dụng nguồn nước sinh hoạt và phúc lợi trẻ em",
        "Chỉ thị": "Khả năng tiếp cận nguồn nước sạch tại các trường học/cơ sở giáo dục",
        "Biến số": "TL_TRUONGHOC_NUOCSACH",
        "Công thức": "Truong_hoc_nuoc = (P / p) * 100",
        "Đơn vị": "%",
        "Diễn giải": "P_school: Số trường có nước sạch thường xuyên; p_total: Tổng số trường học",
        "Ý nghĩa": "Phản ảnh % trường học / cơ sở giáo dục có nước uống an toàn, sẵn có cho trẻ em",
        "Biến cần nhập": ["P_school", "p_total"]
    },
    {
        "STT": 24,
        "Nhóm chỉ số": "Tính công bằng trong sử dụng nguồn nước sinh hoạt và phúc lợi trẻ em",
        "Chỉ thị": "Các cơ sở giáo dục có khu vệ sinh đạt yêu cầu cho trẻ em",
        "Biến số": "TL_CSGD_VESINH",
        "Công thức": "Truong_hoc_vsinh = (Q / p) * 100",
        "Đơn vị": "%",
        "Diễn giải": "Q_school: Số trường có khu vệ sinh/rửa tay đạt chuẩn; p_total_24: Tổng số trường học",
        "Ý nghĩa": "Các cơ sở giáo dục có khu vệ sinh đạt yêu cầu cho trẻ em phản ánh khả năng tiếp cận thực tế trẻ em đối với nước sinh hoạt an toàn",
        "Biến cần nhập": ["Q_school", "p_total_24"]
    }
]

# 13 chỉ số cơ bản của ANNN SH (theo STT)
BASIC_INDICATORS = [2, 4, 6, 7, 11, 13, 15, 16, 19, 20, 21, 23, 24]

# Danh sách tất cả biến đầu vào với diễn giải
VARIABLE_INFO = {
    "F": "Diện tích lưu vực (km²)",
    "Q_tb": "Lưu lượng dòng chảy trung bình năm (m³/s)",
    "Q_tb_kiet": "Lưu lượng dòng chảy TB mùa kiệt (m³/s)",
    "sigma": "Độ lệch chuẩn dòng chảy kiệt",
    "X_tb": "Giá trị trung bình dòng chảy kiệt",
    "X1": "Lượng mưa tháng 1 (mm)", "X2": "Lượng mưa tháng 2 (mm)", "X3": "Lượng mưa tháng 3 (mm)",
    "X4": "Lượng mưa tháng 4 (mm)", "X5": "Lượng mưa tháng 5 (mm)", "X6": "Lượng mưa tháng 6 (mm)",
    "X7": "Lượng mưa tháng 7 (mm)", "X8": "Lượng mưa tháng 8 (mm)", "X9": "Lượng mưa tháng 9 (mm)",
    "X10": "Lượng mưa tháng 10 (mm)", "X11": "Lượng mưa tháng 11 (mm)", "X12": "Lượng mưa tháng 12 (mm)",
    "X_nam_i": "Lượng mưa năm i (mm)", "X_nam_j": "Lượng mưa năm j (mm)",
    "h_nam_i": "Mực nước ngầm năm i (m)", "h_nam_j": "Mực nước ngầm năm j (m)",
    "V_reservoirs": "Trữ lượng nước hồ chứa (10⁶ m³)",
    "flood_hours": "Thời gian ngập lụt TB hàng năm (giờ)",
    "X": "Lượng mưa tính toán SPI (mm)", "X_mean": "Lượng mưa TB cho SPI (mm)", "sigma_spi": "Độ lệch chuẩn cho SPI",
    "salinity_val": "Mức độ xâm nhập mặn (‰)",
    "K": "Số lần vượt ngưỡng QC", "k": "Tổng số lần lấy mẫu",
    "H": "Số hộ KHÔNG hài lòng về CLN", "h": "Tổng số hộ được cấp nước",
    "W_13": "Tổng công suất cấp nước (m³/ngày)", "w_13": "Tổng dân số (người)",
    "M_xc": "Số công trình xuống cấp", "m": "Tổng số công trình",
    "N": "Số ngày mất nước không kế hoạch", "n": "Tổng số ngày trong năm (365)",
    "P_xl": "Số người được cấp nước sạch", "P": "Tổng dân số khu vực",
    "S": "Chi phí tiền nước (VNĐ/tháng)", "S_tn": "Tổng thu nhập hộ dân (VNĐ/tháng)",
    "S_cham": "Số hộ chậm trả tiền nước", "W_18": "Tổng số hộ được cấp nước",
    "PA": "Số hộ phản ánh/khiếu nại", "W_19": "Tổng số hộ được cấp nước",
    "demand_increase": "Mức độ gia tăng nhu cầu nước (%)",
    "TC_dt": "% hộ đô thị tiếp cận nước sạch", "TC_nt": "% hộ nông thôn tiếp cận nước sạch",
    "Z": "Số văn bản hướng dẫn ANNN", "z": "Tổng số văn bản liên quan cấp nước",
    "P_school": "Số trường có nước sạch", "p_total": "Tổng số trường học",
    "Q_school": "Số trường có vệ sinh đạt chuẩn", "p_total_24": "Tổng số trường học (cho chỉ số 24)",
}

# ============== CÁC HÀM TÍNH TOÁN ==============

def calculate_indicator(stt, variables):
    """Tính toán giá trị cho từng chỉ số dựa trên biến số đầu vào"""
    try:
        if stt == 1:  # Mô đun dòng chảy năm
            Q_tb = variables.get('Q_tb', 0) or 0
            F = variables.get('F', 1) or 1
            if F == 0: return None
            return calc.calculate_idx_1(Q_tb=Q_tb, F=F)
        
        elif stt == 2:  # Mô đun dòng chảy mùa kiệt
            Q_tb_kiet = variables.get('Q_tb_kiet', 0) or 0
            F = variables.get('F', 1) or 1
            if F == 0: return None
            return calc.calculate_idx_2(Q_tb_kiet=Q_tb_kiet, F=F)
        
        elif stt == 3:  # Cv-kiệt
            sigma = variables.get('sigma', 0) or 0
            X_tb = variables.get('X_tb', 1) or 1
            if X_tb == 0: return None
            return calc.calculate_idx_3(sigma=sigma, X_tb=X_tb)
        
        elif stt == 4:  # Lượng mưa năm
            rain_months = [
                variables.get('X1', 0) or 0, variables.get('X2', 0) or 0, variables.get('X3', 0) or 0,
                variables.get('X4', 0) or 0, variables.get('X5', 0) or 0, variables.get('X6', 0) or 0,
                variables.get('X7', 0) or 0, variables.get('X8', 0) or 0, variables.get('X9', 0) or 0,
                variables.get('X10', 0) or 0, variables.get('X11', 0) or 0, variables.get('X12', 0) or 0
            ]
            return calc.calculate_idx_4(rain_months=rain_months)
        
        elif stt == 5:  # Biến đổi lượng mưa
            X_nam_i = variables.get('X_nam_i', 0) or 0
            X_nam_j = variables.get('X_nam_j', 0) or 0
            if X_nam_i == 0: return None
            return calc.calculate_idx_5(X_nam_i=X_nam_i, X_nam_j=X_nam_j)
        
        elif stt == 6:  # Thay đổi mực nước ngầm
            h_nam_i = variables.get('h_nam_i', 0) or 0
            h_nam_j = variables.get('h_nam_j', 0) or 0
            if h_nam_i == 0: return None
            return calc.calculate_idx_6(h_nam_i=h_nam_i, h_nam_j=h_nam_j)
        
        elif stt == 7:  # Trữ lượng hồ chứa
            V_reservoirs = variables.get('V_reservoirs', 0) or 0
            return calc.info_idx_7(V_reservoirs=V_reservoirs)
        
        elif stt == 8:  # Thời gian ngập lụt
            flood_hours = variables.get('flood_hours', 0) or 0
            return calc.info_idx_8(flood_hours=flood_hours)
        
        elif stt == 9:  # SPI
            X = variables.get('X', 0) or 0
            X_mean = variables.get('X_mean', 0) or 0
            sigma = variables.get('sigma_spi', 1) or 1
            if sigma == 0: return None
            return calc.calculate_idx_9(X=X, X_mean=X_mean, sigma=sigma)
        
        elif stt == 10:  # Xâm nhập mặn
            salinity_val = variables.get('salinity_val', 0) or 0
            return calc.info_idx_10(salinity_val=salinity_val)
        
        elif stt == 11:  # Chất lượng nước mặt
            K = variables.get('K', 0) or 0
            k = variables.get('k', 1) or 1
            if k == 0: return None
            return calc.calculate_idx_11(K=K, k=k)
        
        elif stt == 12:  # Hài lòng về CLN
            H = variables.get('H', 0) or 0
            h = variables.get('h', 1) or 1
            if h == 0: return None
            return calc.calculate_idx_12(H=H, h=h)
        
        elif stt == 13:  # Năng lực cấp nước
            W = variables.get('W_13', 0) or 0
            w = variables.get('w_13', 1) or 1
            if w == 0: return None
            return calc.calculate_idx_13(W=W, w=w)
        
        elif stt == 14:  # Tình trạng công trình
            M_xc = variables.get('M_xc', 0) or 0
            m = variables.get('m', 1) or 1
            if m == 0: return None
            return calc.calculate_idx_14(M_xc=M_xc, m=m)
        
        elif stt == 15:  # Mức độ ổn định
            N = variables.get('N', 0) or 0
            n = variables.get('n', 365) or 365
            if n == 0: return None
            return calc.calculate_idx_15(N=N, n=n)
        
        elif stt == 16:  # Khả năng tiếp cận nước sạch
            P_xl = variables.get('P_xl', 0) or 0
            P = variables.get('P', 1) or 1
            if P == 0: return None
            return calc.calculate_idx_16(P_xl=P_xl, P=P)
        
        elif stt == 17:  # Khả năng chi trả
            S = variables.get('S', 0) or 0
            S_tn = variables.get('S_tn', 1) or 1
            if S_tn == 0: return None
            return calc.calculate_idx_17(S=S, S_tn=S_tn)
        
        elif stt == 18:  # Khó khăn chi trả
            S_cham = variables.get('S_cham', 0) or 0
            W_total = variables.get('W_18', 1) or 1
            if W_total == 0: return None
            return calc.calculate_idx_18(S_cham=S_cham, W_total=W_total)
        
        elif stt == 19:  # Hài lòng qua khiếu nại
            PA = variables.get('PA', 0) or 0
            W_total = variables.get('W_19', 1) or 1
            if W_total == 0: return None
            return calc.calculate_idx_19(PA=PA, W_total=W_total)
        
        elif stt == 20:  # Nhu cầu tương lai
            demand_increase = variables.get('demand_increase', 0) or 0
            return calc.info_idx_20(demand_increase=demand_increase)
        
        elif stt == 21:  # Công bằng đô thị - nông thôn
            TC_dt = variables.get('TC_dt', 0) or 0
            TC_nt = variables.get('TC_nt', 1) or 1
            if TC_nt == 0: return None
            return calc.calculate_idx_21(TC_dt=TC_dt, TC_nt=TC_nt)
        
        elif stt == 22:  # Mức độ quan tâm của chính quyền
            Z = variables.get('Z', 0) or 0
            z_total = variables.get('z', 1) or 1
            if z_total == 0: return None
            return calc.calculate_idx_22(Z=Z, z_total=z_total)
        
        elif stt == 23:  # Tiếp cận nước sạch tại trường học
            P_school = variables.get('P_school', 0) or 0
            p_total = variables.get('p_total', 1) or 1
            if p_total == 0: return None
            return calc.calculate_idx_23(P_school=P_school, p_total=p_total)
        
        elif stt == 24:  # Vệ sinh đạt chuẩn tại trường học
            Q_school = variables.get('Q_school', 0) or 0
            p_total = variables.get('p_total_24', 1) or 1
            if p_total == 0: return None
            return calc.calculate_idx_24(Q_school=Q_school, p_total=p_total)
        
        return None
    except Exception as e:
        return f"Lỗi: {str(e)}"

def get_required_variables(indicator_stts):
    """Lấy danh sách các biến cần nhập cho các chỉ số đã chọn"""
    all_vars = set()
    for ind in INDICATORS_DATA:
        if ind["STT"] in indicator_stts:
            all_vars.update(ind["Biến cần nhập"])
    return sorted(list(all_vars))

def get_variables_with_stt(indicator_stts):
    """Lấy danh sách các biến cần nhập kèm STT chỉ số, sắp xếp theo STT"""
    var_info_list = []
    for ind in INDICATORS_DATA:
        if ind["STT"] in indicator_stts:
            stt = ind["STT"]
            chi_thi = ind["Chỉ thị"]
            for var in ind["Biến cần nhập"]:
                var_info_list.append({
                    "STT": stt,
                    "Chỉ thị": chi_thi,
                    "Biến số": var
                })
    # Sắp xếp theo STT rồi theo tên biến
    var_info_list.sort(key=lambda x: (x["STT"], x["Biến số"]))
    return var_info_list

# ============== TẢI DỮ LIỆU ==============

BASE_DIR = Path(__file__).resolve().parent
BACBO_CSV_PATH = BASE_DIR / "BacBo_xa_data_input_minhhoa.csv"
OUTPUT_CSV_PATH = BASE_DIR / "data_xa_edited.csv"

@st.cache_data
def load_xa_data():
    """Tải dữ liệu xã/phường từ file CSV"""
    try:
        df = pd.read_csv(BACBO_CSV_PATH, encoding='utf-8')
        return df
    except Exception as e:
        st.error(f"Không thể tải dữ liệu: {e}")
        return pd.DataFrame()

def get_xa_list(df):
    """Lấy danh sách xã/phường từ dữ liệu"""
    if 'Ten_Xa' in df.columns:
        return df['Ten_Xa'].dropna().unique().tolist()
    return []

def get_xa_row(df, xa_name):
    """Lấy dữ liệu của một xã cụ thể"""
    if 'Ten_Xa' in df.columns:
        row = df[df['Ten_Xa'] == xa_name]
        if not row.empty:
            return row.iloc[0].to_dict()
    return {}

# Màu nền cho từng nhóm chỉ số
GROUP_COLORS = {
    "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)": "#E3F2FD",  # Xanh nhạt
    "Hạ tầng phân bổ nguồn nước (Khả năng tiếp cận và tính ổn định)": "#E8F5E9",  # Xanh lá nhạt
    "Hộ sử dụng nước": "#FFF3E0",  # Cam nhạt
    "Tính công bằng trong sử dụng nguồn nước sinh hoạt và phúc lợi trẻ em": "#F3E5F5"  # Tím nhạt
}

# ============== GIAO DIỆN CHÍNH ==============

def main():
    st.markdown('<h1 class="main-header"> Tính toán chỉ số An ninh nguồn nước sinh hoạt</h1>', unsafe_allow_html=True)
    
    # Tải dữ liệu
    df_data = load_xa_data()
    xa_list = get_xa_list(df_data)
    
    # ===== SIDEBAR: CÀI ĐẶT =====
    with st.sidebar:
        st.header("⚙️ Cài đặt")
        
        # 1. Chọn xã/phường
        st.subheader("1️⃣ Chọn xã/phường")
        if xa_list:
            selected_xa = st.selectbox(
                "Xã/Phường khu vực Bắc Bộ:",
                options=xa_list,
                index=0,
                help="Chọn xã/phường cần tính toán chỉ số ANNN"
            )
        else:
            selected_xa = st.text_input("Nhập tên xã/phường:", value="Xã mẫu")
        
        st.divider()
        
        # 2. Chọn loại chỉ số
        st.subheader("2️⃣ Chọn nhóm chỉ số")
        indicator_mode = st.radio(
            "Tính toán cho:",
            options=["13 chỉ số cơ bản", "Tất cả 24 chỉ số"],
            index=0,
            help="Là các chỉ số cơ bản được các chuyên gia khuyến nghị nên tính toán để đánh giá ANNN SH"
        )
        
        # Xác định chỉ số cần hiển thị
        if indicator_mode == "13 chỉ số cơ bản":
            selected_indicator_stts = BASIC_INDICATORS
        else:
            selected_indicator_stts = list(range(1, 25))
        
        st.divider()
        
        # 3. Hướng dẫn
        st.subheader("📖 Hướng dẫn")
        st.markdown("""
        1. Chọn xã/phường cần đánh giá
        2. Chọn nhóm chỉ số (cơ bản hoặc đầy đủ)
        3. Chỉnh sửa giá trị đầu vào trong bảng
        4. Kết quả tự động cập nhật
        5. Tải xuống kết quả khi cần
        """)
    
    # ===== NỘI DUNG CHÍNH =====
    
    # Hiển thị thông tin xã đã chọn
    st.info(f"📍 **Đang xem dữ liệu cho:** {selected_xa} | **Chế độ:** {indicator_mode}")
    
    # Lấy dữ liệu hiện có của xã
    existing_data = get_xa_row(df_data, selected_xa) if xa_list else {}
    
    # ===== BẢNG DỮ LIỆU ĐẦU VÀO =====
    st.subheader("📝 Bảng dữ liệu đầu vào")
    st.caption("Chỉnh sửa các giá trị trong bảng bên dưới. Các biến được sắp xếp theo chỉ số (STT). Kết quả sẽ tự động cập nhật.")
    
    # Lấy danh sách biến kèm theo STT chỉ số
    vars_with_stt = get_variables_with_stt(selected_indicator_stts)
    
    # Tạo DataFrame cho bảng nhập liệu
    input_data = []
    for var_info in vars_with_stt:
        var = var_info["Biến số"]
        stt = var_info["STT"]
        chi_thi = var_info["Chỉ thị"]
        
        # Lấy giá trị từ dữ liệu có sẵn hoặc mặc định
        existing_val = existing_data.get(var, None)
        if pd.isna(existing_val) or existing_val == "":
            existing_val = 0.0
        else:
            try:
                existing_val = float(existing_val)
            except (ValueError, TypeError):
                existing_val = 0.0
        
        input_data.append({
            "STT": stt,
            "Chỉ thị": chi_thi,
            "Biến số": var,
            "Diễn giải": VARIABLE_INFO.get(var, ""),
            "Giá trị": existing_val
        })
    
    df_input = pd.DataFrame(input_data)
    
    # Key duy nhất cho data_editor dựa trên xã và chế độ chỉ số
    editor_key = f"data_editor_{selected_xa}_{indicator_mode}"
    
    # Bảng có thể chỉnh sửa - giới hạn chiều cao với thanh cuộn
    edited_df = st.data_editor(
        df_input,
        column_config={
            "STT": st.column_config.NumberColumn("STT", disabled=True, width="small"),
            "Chỉ thị": st.column_config.TextColumn("Chỉ thị", disabled=True, width="medium"),
            "Biến số": st.column_config.TextColumn("Biến số", disabled=True, width="small"),
            "Diễn giải": st.column_config.TextColumn("Diễn giải", disabled=True, width="medium"),
            "Giá trị": st.column_config.NumberColumn("Giá trị", min_value=0, format="%.4f", width="small"),
        },
        hide_index=True,
        width="stretch",
        height=500,
        key=editor_key,
        num_rows="fixed"
    )
    
    # Chuyển đổi dữ liệu đã chỉnh sửa thành dictionary
    variables_dict = dict(zip(edited_df["Biến số"], edited_df["Giá trị"]))
    
    st.divider()
    
    # ===== BẢNG KẾT QUẢ TÍNH TOÁN =====
    st.subheader("📊 Kết quả tính toán chỉ số ANNN")
    
    # Tính toán kết quả cho từng chỉ số
    results_data = []
    for ind in INDICATORS_DATA:
        if ind["STT"] in selected_indicator_stts:
            result_value = calculate_indicator(ind["STT"], variables_dict)
            
            # Định dạng kết quả
            if result_value is None:
                formatted_result = "N/A"
            elif isinstance(result_value, str) and result_value.startswith("Lỗi"):
                formatted_result = result_value
            else:
                try:
                    formatted_result = f"{float(result_value):.4f}"
                except:
                    formatted_result = str(result_value)
            
            results_data.append({
                "STT": ind["STT"],
                "Nhóm chỉ số": ind["Nhóm chỉ số"],
                "Chỉ thị": ind["Chỉ thị"],
                "Ý nghĩa": ind.get("Ý nghĩa", ""),
                "Kết quả": formatted_result,
                "Đơn vị": ind["Đơn vị"]
            })
    
    df_results = pd.DataFrame(results_data)
    
    # Tạo HTML bảng kết quả với tooltip (bọc trong div để tránh lỗi Markdown parser)
    table_html = """<div class="annn-wrapper"><style>
.annn-wrapper { width: 100%; }
.annn-table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 14px; }
.annn-table th { background-color: #1565C0; color: white; padding: 12px 8px; text-align: left; border: 1px solid #ddd; }
.annn-table td { padding: 10px 8px; border: 1px solid #ddd; vertical-align: middle; }
.annn-table tr:hover { filter: brightness(0.95); }
.tooltip-cell { position: relative; cursor: help; }
.tooltip-cell .tooltip-text {
    visibility: hidden;
    width: 350px;
    background-color: #333;
    color: #fff;
    text-align: left;
    border-radius: 6px;
    padding: 10px;
    position: absolute;
    z-index: 1000;
    bottom: 100%;
    left: 0;
    margin-bottom: 5px;
    font-size: 12px;
    line-height: 1.4;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}
.tooltip-cell:hover .tooltip-text { visibility: visible; }
.chi-thi-text { font-weight: 500; }
.help-icon { color: #1565C0; margin-left: 5px; font-size: 12px; }
</style><table class="annn-table"><thead><tr><th style="width:50px;text-align:center;">STT</th><th style="width:55%;">Chỉ thị</th><th style="width:120px;text-align:center;">Kết quả</th><th style="width:100px;text-align:center;">Đơn vị</th></tr></thead><tbody>"""
    
    for _, row in df_results.iterrows():
        group = row['Nhóm chỉ số']
        color = GROUP_COLORS.get(group, '#FFFFFF')
        y_nghia = str(row.get('Ý nghĩa', '')).replace('"', '&quot;').replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;")
        chi_thi = str(row['Chỉ thị']).replace('"', '&quot;').replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;")
        ket_qua = str(row['Kết quả'])
        don_vi = str(row['Đơn vị'])
        stt = row['STT']
        
        # Tối ưu f-string: giảm thiểu khoảng trắng, đưa thẻ <tr> sát vào chuỗi
        table_html += f'<tr style="background-color:{color};"><td style="text-align:center;font-weight:bold;">{stt}</td><td class="tooltip-cell"><span class="chi-thi-text">{chi_thi}</span><span class="help-icon">ℹ️</span><span class="tooltip-text">💡 <b>Ý nghĩa:</b> {y_nghia}</span></td><td style="text-align:center;font-weight:bold;">{ket_qua}</td><td style="text-align:center;">{don_vi}</td></tr>'
    
    table_html += "</tbody></table></div>"
    
    # Sử dụng st.html nếu có (Streamlit >= 1.33), fallback về st.markdown
    if hasattr(st, 'html'):
        st.html(table_html)
    else:
        st.markdown(table_html, unsafe_allow_html=True)
    
    # Hiển thị chú thích màu
    st.markdown("**📌 Chú thích màu theo nhóm chỉ số:**")
    legend_cols = st.columns(len(GROUP_COLORS))
    for i, (group, color) in enumerate(GROUP_COLORS.items()):
        with legend_cols[i]:
            short_name = group.split("(")[0].strip() if "(" in group else group[:20]
            st.markdown(f"<div style='background-color: {color}; padding: 6px; border-radius: 5px; font-size: 10px; text-align: center;'>{short_name}</div>", unsafe_allow_html=True)
    
    # ===== THỐNG KÊ TÓM TẮT =====
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    # Đếm số chỉ số có kết quả hợp lệ
    valid_results = [r for r in results_data if r["Kết quả"] != "N/A" and not r["Kết quả"].startswith("Lỗi")]
    na_results = [r for r in results_data if r["Kết quả"] == "N/A"]
    error_results = [r for r in results_data if r["Kết quả"].startswith("Lỗi")]
    
    with col1:
        st.metric("✅ Chỉ số đã tính", f"{len(valid_results)}/{len(results_data)}")
    
    with col2:
        st.metric("⚠️ Thiếu dữ liệu", len(na_results))
    
    with col3:
        st.metric("❌ Có lỗi", len(error_results))
    
    st.divider()
    
    # ===== XUẤT DỮ LIỆU =====
    st.subheader("💾 Xuất dữ liệu")
    
    col_export1, col_export2 = st.columns(2)
    
    with col_export1:
        # Xuất dữ liệu đầu vào đã chỉnh sửa
        csv_input = edited_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Tải dữ liệu đầu vào (CSV)",
            data=csv_input.encode('utf-8-sig'),
            file_name=f"ANNN_input_{selected_xa}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Tải xuống bảng dữ liệu đầu vào đã chỉnh sửa"
        )
    
    with col_export2:
        # Xuất kết quả tính toán
        csv_results = df_results.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Tải kết quả tính toán (CSV)",
            data=csv_results.encode('utf-8-sig'),
            file_name=f"ANNN_results_{selected_xa}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Tải xuống bảng kết quả tính toán"
        )
    
    # Lưu dữ liệu tự động (tùy chọn)
    st.divider()
    
    if st.button("💾 Lưu dữ liệu vào hệ thống", type="primary"):
        try:
            # Tạo DataFrame để lưu
            save_data = {
                "Xã/Phường": selected_xa,
                "Thời gian": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                **variables_dict
            }
            df_save = pd.DataFrame([save_data])
            
            # Lưu vào file
            if OUTPUT_CSV_PATH.exists():
                df_existing = pd.read_csv(OUTPUT_CSV_PATH, encoding='utf-8-sig')
                df_combined = pd.concat([df_existing, df_save], ignore_index=True)
            else:
                df_combined = df_save
            
            df_combined.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')
            st.success(f"✅ Đã lưu dữ liệu cho {selected_xa} thành công!")
        except Exception as e:
            st.error(f"❌ Lỗi khi lưu: {str(e)}")
    
    # ===== FOOTER =====
    st.divider()
    st.caption("Tính toán chỉ số An ninh nguồn nước sinh hoạt - Khu vực Bắc Bộ")

if __name__ == "__main__":
    main()
