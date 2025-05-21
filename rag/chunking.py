import os
import re
import sys
import json
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from datetime import datetime
from unidecode import unidecode

def extract_year_from_filename(filename):
    """
    Trích xuất năm từ tên file Markdown (giả định tên file có định dạng chứa năm).

    Args:
        filename (str): Tên file Markdown.

    Returns:
        str: Năm được trích xuất, hoặc None nếu không tìm thấy.
    """
    match = re.search(r'20\d{2}', filename)
    return match.group(0) if match else None

def count_keywords_by_category(text, keywords_dict):
    """
    Đếm số từ khóa theo từng danh mục trong văn bản. Hỗ trợ so khớp không dấu.
    
    Returns:
        category_counts (dict): Số từ khóa theo danh mục.
        found_keywords (dict): Từ khóa đã tìm thấy theo danh mục.
    """
    category_counts = {}
    found_keywords = {}
    
    text_no_accent = unidecode(text.lower())
    
    for category, keywords in keywords_dict.items():
        count = 0
        matched_keywords = []
        for kw in keywords:
            kw_lower = kw.lower()
            kw_no_accent = unidecode(kw_lower)
            
            if kw_lower in text.lower() or kw_no_accent in text_no_accent:
                count += 1
                matched_keywords.append(kw)
        
        if count > 0:
            category_counts[category] = count
            found_keywords[category] = matched_keywords
            
    return category_counts, found_keywords

def determine_field_from_keywords(text, keywords_dict):
    """
    Xác định lĩnh vực của văn bản dựa trên vị trí xuất hiện đầu tiên của từ khóa trong text.

    Returns:
        tuple: (field, category_counts, all_found_keywords, department)
    """
    nganh_categories = ["attt", "cntt", "httt", "khdl", "khmt", "ktmt", "ktpm", 
                        "mmtvttdl", "tkvm", "tmdt", "ttnt", "ttdpt"]

    nganh_name_map = {
        "attt": "An toàn thông tin",
        "cntt": "Công nghệ thông tin",
        "httt": "Hệ thống thông tin",
        "khdl": "Khoa học dữ liệu",
        "khmt": "Khoa học máy tính",
        "ktmt": "Kỹ thuật máy tính",
        "ktpm": "Kỹ thuật phần mềm",
        "mmtvttdl": "Mạng máy tính và truyền thông dữ liệu",
        "tkvm": "Thiết kế vi mạch",
        "tmdt": "Thương mại điện tử",
        "ttnt": "Trí tuệ nhân tạo",
        "ttdpt": "Truyền thông đa phương tiện"
    }

    # Chuẩn hóa văn bản: bỏ dấu để khớp với từ khóa không dấu
    text_no_accent = unidecode(text.lower())

    category_counts, found_keywords = count_keywords_by_category(text, keywords_dict)

    # Gộp ngành học
    nganh_count = sum(category_counts.get(cat, 0) for cat in nganh_categories)
    grouped_counts = category_counts.copy()
    for cat in nganh_categories:
        grouped_counts.pop(cat, None)
    grouped_counts["ngành học"] = nganh_count

    all_found_keywords = []
    for kw_list in found_keywords.values():
        all_found_keywords.extend(kw_list)

    # Tìm vị trí xuất hiện đầu tiên của bất kỳ từ khóa nào trong text
    first_pos = len(text_no_accent) + 1
    selected_category = None
    selected_nganh = None

    # Kiểm tra các ngành học trước
    for cat in nganh_categories:
        for kw in keywords_dict.get(cat, []):
            idx = text_no_accent.find(unidecode(kw.lower()))
            if idx != -1 and idx < first_pos:
                first_pos = idx
                selected_category = "ngành học"
                selected_nganh = cat

    # Kiểm tra các category còn lại
    for category, keywords in keywords_dict.items():
        if category in nganh_categories:
            continue
        for kw in keywords:
            idx = text_no_accent.find(unidecode(kw.lower()))
            if idx != -1 and idx < first_pos:
                first_pos = idx
                selected_category = category
                selected_nganh = None

    # Luôn trả về department nếu xác định được ngành/khoa
    department = None
    if selected_nganh:
        department = nganh_name_map.get(selected_nganh, selected_nganh)

    if selected_category == "ngành học" and nganh_count > 0:
        return "ngành", category_counts, all_found_keywords, department

    elif selected_category:
        field_name = "học bổng" if selected_category == "hoc_bong" else (
            "tuyển sinh" if selected_category in ["tuyensinh", "diem"] else
            "trường" if selected_category == "truong" else
            "ngoài lề"
        )
        return field_name, category_counts, all_found_keywords, department

    return "ngoài lề", category_counts, all_found_keywords, department

def get_keywords(text, keywords_dict):
    """
    Lấy tất cả các từ khóa từ keywords_dict xuất hiện trong văn bản.

    Args:
        text (str): Chuỗi văn bản để tìm kiếm từ khóa.
        keywords_dict (dict): Từ điển chứa các từ khóa theo danh mục.

    Returns:
        list: Danh sách tất cả các từ khóa được tìm thấy trong văn bản.
    """
    text_lower = text.lower()
    found_keywords = set()

    for category, keywords in keywords_dict.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                found_keywords.add(kw)

    return list(found_keywords)

def determine_field_from_filename(filename, keywords_dict):
    """
    Xác định field dựa trên tên file (basename).

    Args:
        filename (str): Tên file Markdown.
        keywords_dict (dict): Từ điển chứa các từ khóa theo danh mục.

    Returns:
        tuple: (field, category_counts, all_found_keywords, department)
    """
    text = filename.lower().replace("_", " ").replace("-", " ")
    print(text)
    return determine_field_from_keywords(text, keywords_dict)


def chunk_markdown(content, source_file, keywords_dict, output_dir):
    """
    Chia nội dung Markdown thành các đoạn nhỏ (chunks) và tạo metadata,
    trích xuất source từ dòng cuối cùng của file và thông tin từ tên file.

    Args:
        content (str): Nội dung Markdown cần chia.
        source_file (str): Đường dẫn đến file Markdown nguồn.
        keywords_dict (dict): Từ điển chứa các từ khóa.
        output_dir (str): Đường dẫn đến thư mục output cho file JSON.

    Returns:
        list: Danh sách các chunk, mỗi chunk là một dictionary chứa nội dung và metadata.
    """
    filename = Path(source_file).name
    title_line = Path(source_file).stem.replace("_", " ").title() # Lấy title từ tên file mặc định
    year = extract_year_from_filename(filename)

    # Xác định field cho toàn bộ văn bản
    field, category_counts, _, filename_department = determine_field_from_filename(filename, keywords_dict)

    
    lines = content.splitlines()

    # Trích xuất title từ nội dung nếu có
    if lines and lines[0].startswith("#"):
        title_line = lines[0].replace("#", "").strip()

    # Trích xuất source từ dòng cuối cùng
    source = None
    if lines and lines[-1].startswith("Source:"):
        source = lines[-1].replace("Source:", "").strip()
    elif lines and re.match(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+", lines[-1]):
        source = f"Source: {lines[-1]}"
    else:
        source = f"Source: {source_file}"

    if source and content.endswith(lines[-1]):
        content = content[:-len(lines[-1])].rstrip("\n")
        lines = content.splitlines()

    admission_info = {}
    if field == "tuyển sinh":
        admission_info["dot_tuyen_sinh"] = re.search(r"đợt\s+(\d+)", content, re.IGNORECASE).group(1) if re.search(r"đợt\s+(\d+)", content, re.IGNORECASE) else None
        admission_info["phuong_thuc_xet_tuyen"] = re.search(r"phương thức\s+xét\s+tuyển\s*:\s*(.*)", content, re.IGNORECASE).group(1).strip() if re.search(r"phương thức\s+xét\s+tuyển\s*:\s*(.*)", content, re.IGNORECASE) else None
        admission_info["chi_tieu"] = int(re.search(r"chỉ\s+tiêu\s*:\s*(\d+)", content, re.IGNORECASE).group(1)) if re.search(r"chỉ\s+tiêu\s*:\s*(\d+)", content, re.IGNORECASE) else None
        diem_chuan_match = re.search(r"điểm\s+chuẩn\s*:\s*(\d+\.?\d*)", content, re.IGNORECASE)
        admission_info["diem_chuan"] = float(diem_chuan_match.group(1)) if diem_chuan_match else None
        admission_info["nguong_xet"] = re.search(r"ngưỡng\s+xét\s+tuyển\s*:\s*(.*)", content, re.IGNORECASE).group(1).strip() if re.search(r"ngưỡng\s+xét\s+tuyển\s*:\s*(.*)", content, re.IGNORECASE) else None

    header_pattern = re.compile(r"^#{2,6}\s+(.*)")
    chunks = []
    current_header = ""
    current_chunk_lines = []

    for line in lines:
        header_match = header_pattern.match(line)
        if header_match:
            if current_chunk_lines:
                chunks.append((current_header, "\n".join(current_chunk_lines)))
            current_chunk_lines = []
            current_header = header_match.group(1).strip()
        else:
            current_chunk_lines.append(line)

    if current_chunk_lines:
        chunks.append((current_header, "\n".join(current_chunk_lines)))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]
    )

    result = []
    chunk_counter = 0

    for header, chunk_text in chunks:
        sub_chunks = splitter.split_text(chunk_text)
        for sub_text in sub_chunks:
            chunk_counter += 1
            chunk_id = f"{Path(source_file).stem}_chunk_{chunk_counter}"
        
            category_counts, _ = count_keywords_by_category(sub_text, keywords_dict)
            found_keywords = list(category_counts.keys())
            
            department = filename_department

            metadata = {
                "title": title_line,
                "header": header,
                "content": sub_text,
                "chunk_id": chunk_id,
                "field": field,
                "year": year,
                "department": department,
                "keywords": found_keywords,
                "prev_chunk": None,
                "next_chunk": None,
                "source": source,
                "admission_info": admission_info if field == "tuyển sinh" else {},
            }
            result.append(metadata)

    for i in range(len(result)):
        if i > 0:
            result[i]["prev_chunk"] = result[i-1]["chunk_id"]
        if i < len(result) - 1:
            result[i]["next_chunk"] = result[i+1]["chunk_id"]

    return result

def save_chunks_to_json(chunks, output_path):
    """
    Lưu danh sách các chunk vào file JSON.

    Args:
        chunks (list): Danh sách các chunk.
        output_path (str): Đường dẫn đến file JSON đầu ra.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

def main():
    """
    Hàm chính của chương trình.
    """
    markdown_dir = "cleaned_data/markdown"
    output_dir = "cleaned_data/json"
    keywords_file = "keywords.py"

    # Tạo thư mục output nếu chưa tồn tại
    os.makedirs(output_dir, exist_ok=True)

    # Load keywords
    keywords_dict = {}
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, script_dir)
        from keywords import keywords_dict
        keywords_dict = keywords_dict
    except ImportError as e:
        print(f"Error: Could not import keywords_dict from {keywords_file}. Please ensure the file exists and the variable is correctly named. Error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: The file {keywords_file} was not found at {os.path.join(os.getcwd(), keywords_file)}. Please provide the correct path.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while loading keywords: {e}")
        sys.exit(1)

    markdown_files = [f for f in os.listdir(markdown_dir) if f.endswith(".md")]

    if not markdown_files:
        print(f"No markdown files found in {markdown_dir}")
        sys.exit(0)

    for filename in markdown_files:
        markdown_path = os.path.join(markdown_dir, filename)
        output_filename = Path(filename).stem + "_chunks.json"
        output_path = os.path.join(output_dir, output_filename)

        try:
            with open(markdown_path, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = chunk_markdown(content, markdown_path, keywords_dict, output_dir)
            save_chunks_to_json(chunks, output_path)
            print(f"Processed {markdown_path} and saved {len(chunks)} chunks to {output_path}")

        except FileNotFoundError:
            print(f"Error: The markdown file {markdown_path} was not found.")
        except Exception as e:
            print(f"An error occurred while processing {markdown_path}: {e}")

if __name__ == "__main__":
    main()