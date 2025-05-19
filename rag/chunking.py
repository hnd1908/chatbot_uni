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

def count_keywords_by_category(text, keywords_dict):
    """
    Đếm số lượng từ khóa xuất hiện trong văn bản cho mỗi danh mục.
    
    Args:
        text (str): Chuỗi văn bản để tìm kiếm từ khóa.
        keywords_dict (dict): Từ điển chứa các từ khóa theo danh mục.
        
    Returns:
        dict: Từ điển với khóa là danh mục và giá trị là số lượng từ khóa tìm thấy.
    """
    text_lower = text.lower()
    category_counts = {}
    found_keywords = {}
    
    # Khởi tạo đếm cho mỗi danh mục
    for category in keywords_dict:
        category_counts[category] = 0
        found_keywords[category] = []
    
    # Đếm số lượng từ khóa cho mỗi danh mục
    for category, keywords in keywords_dict.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                category_counts[category] += 1
                found_keywords[category].append(kw)
                
    return category_counts, found_keywords

def determine_field_from_keywords(text, keywords_dict):
    """
    Xác định lĩnh vực của văn bản dựa trên số lượng từ khóa tìm thấy.
    
    Args:
        text (str): Chuỗi văn bản để tìm kiếm từ khóa.
        keywords_dict (dict): Từ điển chứa các từ khóa theo danh mục.
        
    Returns:
        tuple: (field, category_counts, all_found_keywords, department)
            - field: Lĩnh vực được xác định
            - category_counts: Từ điển với khóa là danh mục và giá trị là số lượng từ khóa tìm thấy
            - all_found_keywords: Danh sách tất cả các từ khóa được tìm thấy
            - department: Tên khoa/ngành cụ thể (nếu field là "ngành")
    """
    # Các ngành học
    nganh_categories = ["attt", "cntt", "httt", "khdl", "khmt", "ktmt", "ktpm", 
                         "mmtvttdl", "tkvm", "tmdt", "ttnt", "ttdpt"]
    
    category_counts, found_keywords = count_keywords_by_category(text, keywords_dict)
    
    # Tính tổng số từ khóa ngành học để xác định field (gộp tạm thời)
    nganh_count = sum(category_counts[cat] for cat in nganh_categories if cat in category_counts)
    
    # Tạo từ điển mới với "ngành học" gộp chung chỉ để xác định field
    grouped_counts = category_counts.copy()
    for cat in nganh_categories:
        if cat in grouped_counts:
            del grouped_counts[cat]
    grouped_counts["ngành học"] = nganh_count
    
    # Lấy danh mục có nhiều từ khóa nhất
    sorted_categories = sorted(grouped_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Tổng hợp tất cả các từ khóa tìm thấy
    all_found_keywords = []
    for cat, keywords_list in found_keywords.items():
        all_found_keywords.extend(keywords_list)
    
    # Biến lưu tên khoa/ngành cụ thể
    department = None
    
    # Xác định field dựa trên danh mục hàng đầu
    if len(sorted_categories) > 0 and sorted_categories[0][1] > 0:
        top_category = sorted_categories[0][0]
        
        # Nếu danh mục hàng đầu là tuyensinh hoặc diem
        if top_category in ["tuyensinh", "diem"]:
            return "tuyển sinh", category_counts, all_found_keywords, None
        # Nếu danh mục hàng đầu là ngành học
        elif top_category == "ngành học":
            # Tìm ngành cụ thể có số lượng từ khóa cao nhất
            nganh_counts = {cat: category_counts[cat] for cat in nganh_categories if cat in category_counts}
            if nganh_counts:
                top_nganh = max(nganh_counts.items(), key=lambda x: x[1])
                
                # Chuyển đổi tên viết tắt thành tên đầy đủ
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
                
                department = nganh_name_map.get(top_nganh[0], top_nganh[0])
            
            return "ngành", category_counts, all_found_keywords, department
        # Nếu danh mục hàng đầu là truong
        elif top_category == "truong":
            return "trường", category_counts, all_found_keywords, None
        # Nếu danh mục hàng đầu là ngoai_le
        elif top_category == "ngoai_le":
            return "ngoài lề", category_counts, all_found_keywords, None
    
    # Mặc định
    return "ngoài lề", category_counts, all_found_keywords, None

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
    
    # Phân tích filename để lấy department nếu có
    filename_department = extract_department_from_filename(filename)

    # Xác định field cho toàn bộ văn bản
    field, category_counts, _, _ = determine_field_from_keywords(content, keywords_dict)
    
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
        chunk_size=500,
        chunk_overlap=20,
        separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]
    )

    result = []
    chunk_counter = 0

    for header, chunk_text in chunks:
        sub_chunks = splitter.split_text(chunk_text)
        for sub_text in sub_chunks:
            chunk_counter += 1
            chunk_id = f"{Path(source_file).stem}_chunk_{chunk_counter}"
        
            sub_field, sub_category_counts, found_keywords, chunk_department = determine_field_from_keywords(sub_text, keywords_dict)
            
            department = chunk_department if chunk_department else filename_department

            metadata = {
                "title": title_line,
                "header": header,
                "content": sub_text,
                "chunk_id": chunk_id,
                "field": sub_field,
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