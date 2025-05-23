import csv
import json
import uuid
import re
from pathlib import Path
from keywords import keywords_dict  # Thêm dòng này

def clean_float(val):
    try:
        return float(str(val).replace(",", "."))
    except:
        return None

def detect_department_from_name(name: str) -> str:
    name_lower = name.lower()
    if "trí tuệ nhân tạo" in name_lower or "ai" in name_lower:
        return "ttnt"
    elif "thương mại điện tử" in name_lower:
        return "tmdt"
    elif "khoa học dữ liệu" in name_lower:
        return "khdl"
    elif "an toàn thông tin" in name_lower:
        return "attt"
    elif "khoa học máy tính" in name_lower:
        return "khmt"
    elif "hệ thống thông tin" in name_lower:
        return "httt"
    elif "kỹ thuật phần mềm" in name_lower:
        return "ktpm"
    elif "kỹ thuật máy tính" in name_lower:
        return "ktmt"
    elif "vi mạch" in name_lower:
        return "tkvm"
    elif "công nghệ thông tin" in name_lower:
        return "cntt"
    else:
        return "ngành"

def chunk_multi_year_csv(csv_path: str, output_path: str):
    chunks = []
    current_year = None
    source = "csv_data\\diemchuanUIT.csv"

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not any(row):
                continue
            year_match = re.match(r'^20\d{2}$', row[0].strip())
            if year_match:
                current_year = int(row[0].strip())
                continue
            if row[0].strip().lower() == "stt":
                continue
            if current_year is None:
                continue  # Không có năm -> skip

            try:
                ma_nganh = row[1].strip()
                ten_nganh = row[2].strip().title()
                to_hop = row[3].strip()
                diem_chuan = clean_float(row[4])
                diem_dgnl = clean_float(row[5])
            except IndexError:
                continue

            # Tạo mô tả tự nhiên cho chunk
            description = (
                f"Năm {current_year}, ngành {ten_nganh} (mã ngành {ma_nganh}) "
                f"có điểm chuẩn là {diem_chuan}, điểm ĐGNL là {diem_dgnl}, "
                f"tổ hợp môn xét tuyển: {to_hop}. "
                f"Phương thức xét tuyển: điểm thi THPT và ĐGNL."
            )

            chunk_id = str(uuid.uuid4())
            department = detect_department_from_name(ten_nganh)
            field = "tuyển sinh"
            title_line = f"Ngành {ten_nganh}"
            header = f"Năm {current_year} - Mã ngành: {ma_nganh}"

            admission_info = {
                "phuong_thuc_xet_tuyen": "Điểm thi THPT + ĐGNL",
                "diem_chuan": diem_chuan,
                "diem_dgnl": diem_dgnl,
                "to_hop_mon": to_hop
            }

            # Lấy keywords từ keywords_dict (nếu có), đồng thời bổ sung mã ngành, tên ngành, tổ hợp môn
            found_keywords = [field] if field else []
            found_keywords += ["diem", "tuyensinh"]
            found_keywords += [ma_nganh, ten_nganh, to_hop]

            chunk = {
                "title": title_line,
                "header": header,
                "content": description,  # Dùng description để embedding
                "chunk_id": chunk_id,
                "field": field,
                "year": str(current_year),
                "department": department,
                "keywords": found_keywords,
                # "prev_chunk": None,
                # "next_chunk": None,
                "source": source,
                # "admission_info": admission_info
            }

            chunks.append(chunk)

    # Gán prev_chunk và next_chunk
    for i in range(len(chunks)):
        if i > 0:
            chunks[i]["prev_chunk"] = chunks[i - 1]["chunk_id"]
        if i < len(chunks) - 1:
            chunks[i]["next_chunk"] = chunks[i + 1]["chunk_id"]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Đã xử lý {len(chunks)} ngành và lưu vào {output_path}")

if __name__ == "__main__":
    chunk_multi_year_csv("csv_data/diemchuanUIT.csv", "cleaned_data/json/diemchuanUIT_chunks.json")