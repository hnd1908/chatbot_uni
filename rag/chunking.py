import os
import re
import sys
import json
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from datetime import datetime

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

def extract_department_from_filename(filename):
    """
    Trích xuất tên khoa/ngành từ tên file Markdown (giả định tên file có chứa tên khoa/ngành).

    Args:
        filename (str): Tên file Markdown.

    Returns:
        str: Tên khoa/ngành được trích xuất, hoặc None nếu không tìm thấy.
    """
    parts = filename.lower().replace("_", " ").replace("-", " ").split()
    department_keywords = ["nganh", "khoa"]
    for i, part in enumerate(parts):
        if part in department_keywords and i + 1 < len(parts):
            return " ".join(parts[i+1:]).title().strip()
        elif part not in department_keywords:
            # Thử tìm các từ khóa có thể là tên ngành/khoa
            potential_department = " ".join(p.title() for p in parts[i:] if p not in ['thong', 'tin', 'dai', 'hoc', 'nam'])
            if potential_department:
                return potential_department.strip()
    return None

def detect_field_from_filename(filename):
    """
    Xác định lĩnh vực của văn bản dựa trên tên file Markdown.

    Args:
        filename (str): Tên file Markdown.

    Returns:
        str: Lĩnh vực của văn bản ("tuyển sinh", "ngành", "ngoài lề").
    """
    lowered_filename = filename.lower().replace("_", " ").replace("-", " ")
    if "tuyen sinh" in lowered_filename or "xet tuyen" in lowered_filename or "nhap hoc" in lowered_filename:
        return "tuyển sinh"
    elif "nganh" in lowered_filename or "khoa" in lowered_filename or "chuong trinh dao tao" in lowered_filename:
        return "ngành"
    elif "thong bao" in lowered_filename or "su kien" in lowered_filename or "hoi thao" in lowered_filename:
        return "ngoài lề"
    return "ngoài lề" # Mặc định nếu không tìm thấy

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

def chunk_markdown(content, source_file, priority_keywords_dict, output_dir):
    """
    Chia nội dung Markdown thành các đoạn nhỏ (chunks) và tạo metadata,
    trích xuất source từ dòng cuối cùng của file và thông tin từ tên file.

    Args:
        content (str): Nội dung Markdown cần chia.
        source_file (str): Đường dẫn đến file Markdown nguồn.
        priority_keywords_dict (dict): Từ điển chứa các từ khóa ưu tiên.
        output_dir (str): Đường dẫn đến thư mục output cho file JSON.

    Returns:
        list: Danh sách các chunk, mỗi chunk là một dictionary chứa nội dung và metadata.
    """
    filename = Path(source_file).name
    title_line = Path(source_file).stem.replace("_", " ").title() # Lấy title từ tên file mặc định
    field = detect_field_from_filename(filename)
    year = extract_year_from_filename(filename)
    department = extract_department_from_filename(filename)

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
        source = f"Source: {source_file}" # Mặc định nếu không tìm thấy

    # Loại bỏ dòng source khỏi nội dung để tránh nó bị đưa vào chunk
    if source and content.endswith(lines[-1]):
        content = content[:-len(lines[-1])].rstrip("\n")
        lines = content.splitlines() # Cập nhật lại lines sau khi loại bỏ

    # Thông tin tuyển sinh chi tiết hơn (vẫn dựa trên nội dung)
    admission_info = {}
    if field == "tuyển sinh":
        admission_info["dot_tuyen_sinh"] = re.search(r"đợt\s+(\d+)", content, re.IGNORECASE).group(1) if re.search(r"đợt\s+(\d+)", content, re.IGNORECASE) else None
        admission_info["phuong_thuc_xet_tuyen"] = re.search(r"phương thức\s+xét\s+tuyển\s*:\s*(.*)", content, re.IGNORECASE).group(1).strip() if re.search(r"phương thức\s+xét\s+tuyển\s*:\s*(.*)", content, re.IGNORECASE) else None
        admission_info["chi_tieu"] = int(re.search(r"chỉ\s+tiêu\s*:\s*(\d+)", content, re.IGNORECASE).group(1)) if re.search(r"chỉ\s+tiêu\s*:\s*(\d+)", content, re.IGNORECASE) else None
        diem_chuan_match = re.search(r"điểm\s+chuẩn\s*:\s*(\d+\.?\d*)", content, re.IGNORECASE)
        admission_info["diem_chuan"] = float(diem_chuan_match.group(1)) if diem_chuan_match else None
        admission_info["nguong_xet"] = re.search(r"ngưỡng\s+xét\s+tuyển\s*:\s*(.*)", content, re.IGNORECASE).group(1).strip() if re.search(r"ngưỡng\s+xét\s+tuyển\s*:\s*(.*)", content, re.IGNORECASE) else None

    # Tách chunk theo header ##, ###,...
    header_pattern = re.compile(r"^#{2,5}\s+(.*)")
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
        chunk_size=250,
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
            keywords = get_keywords(sub_text, priority_keywords_dict)

            metadata = {
                "title": title_line,
                "header": header,
                "content": sub_text,
                "chunk_id": chunk_id,
                "field": field,
                "year": year,
                "department": department,
                "keywords": keywords,
                "prev_chunk": None,
                "next_chunk": None,
                "source": source,
                "admission_info": admission_info,
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
            print(f"Processed {markdown_path} and saved {len(chunks)} to {output_path}")

        except FileNotFoundError:
            print(f"Error: The markdown file {markdown_path} was not found.")
        except Exception as e:
            print(f"An error occurred while processing {markdown_path}: {e}")

if __name__ == "__main__":
    main()