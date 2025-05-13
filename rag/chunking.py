import re
import os
import json
from pathlib import Path

folder_dir = "cleaned_data"
data_dir = "cleaned_data/markdown"

def extract_year(text):
    match = re.search(r'20\d{2}', text)
    return match.group() if match else None

def extract_department(text):
    match = re.search(r'(ngành|khoa)\s+(.*)', text, re.IGNORECASE)
    return match.group(2).strip() if match else None

def detect_field(title):
    lowered = title.lower()
    tuyen_sinh_keywords = ["tuyển sinh", "đợt", "phương thức"]
    nganh_keywords = ["tổng quan", "ngành", "khoa"]

    tuyen_sinh_count = sum(1 for word in tuyen_sinh_keywords if word in lowered)
    nganh_count = sum(1 for word in nganh_keywords if word in lowered)

    if tuyen_sinh_count >= 2:
        return "tuyển sinh"
    elif nganh_count >= 2:
        return "ngành"
    else:
        return "ngoài lề"

# def chunk_markdown(content, source_file):
    lines = content.splitlines()
    title_line = lines[0]
    title_line = title_line.replace("#","").strip()
    field = detect_field(title_line)
    year = extract_year(content) if field in ['tuyển sinh', 'ngoài lề'] else None
    department = extract_department(title_line) if field == 'ngành' else None

    # Đếm số lần xuất hiện mỗi header
    header_counts = {
        '##': sum(1 for line in lines if line.startswith('## ')),
        '###': sum(1 for line in lines if line.startswith('### ')),
        '####': sum(1 for line in lines if line.startswith('#### ')),
    }

    chunks = []

    # Ưu tiên header cao hơn trước (## > ### > ####)
    for level in ['##', '###', '####']:
        if header_counts[level] >= 2:
            header_prefix = level
            print(f"Header level: {header_prefix}")
            pattern = rf'{re.escape(header_prefix)}\s+(.*)\n(.*?)(?=\n{re.escape(header_prefix)}\s+|\n#{1,4}\s+|\Z)'
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            print(f"Matches found: {matches}")
            # Chuyển đổi các chunk thành định dạng mong muốn
            for header, body, _ in matches:
                header = header.strip()
                body = body.strip()
                print(f"Header: {header}")
                print(f"Body: {body}")
                if header and body:
                    chunks.append({
                        'header': header,
                        'content': body,
                    })
            break
        else:
            # Không có đủ header nào để tách
            chunks = [{
                'header': "",
                'content': content.strip()
            }]
            header_prefix = ''


    chunked_data = []
    base_filename = Path(source_file).stem

    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        header = chunk.get("header", "")
        content = chunk.get("content", "")
        lines = content.strip().splitlines()
        print(lines[0])
        if not lines:
            continue

        title = title_line
        # Gộp title gốc và tiêu đề từng phần
        title_combined = f"{title.strip()} - {header.strip()}" if header else title.strip()

        body = '\n'.join(lines)

        entry = {
            "title": title_combined,
            "content": body.strip(),
            "source_file": source_file,
            "chunk_id": f"{base_filename}_{i+1}",
            "field": field
        }
        if year:
            entry["year"] = year
        if department:
            entry["department"] = department
        chunked_data.append(entry)

    return chunked_data


def chunk_markdown(content, source_file):
    """
    Chia nội dung Markdown thành các chunk nhỏ hơn dựa trên tiêu đề,
    tuân thủ giới hạn token và định dạng tiêu đề mới.

    Args:
        content (str): Nội dung Markdown cần chia.
        source_file (str): Đường dẫn đến file nguồn.

    Returns:
        list: Danh sách các chunk, mỗi chunk là một dictionary.
    """
    lines = content.splitlines()
    title_line = lines[0].replace("#", "").strip()
    field = detect_field(title_line)
    year = extract_year(content) if field in ['tuyển sinh', 'ngoài lề'] else None
    department = extract_department(title_line) if field == 'ngành' else None

    chunks = []
    current_chunk = []
    current_header = ""
    header_level = 0

    for line in lines[1:]:  # Bỏ dòng tiêu đề đầu tiên
        line = line.strip()
        if not line:
            continue

        if line.startswith('##'):
            level = len(line) - len(line.lstrip('#'))
            if level in [2, 3, 4, 5]:  # Các cấp header được chấp nhận
                if current_chunk:
                    chunks.append({
                        'header': current_header,
                        'content': '\n'.join(current_chunk).strip()
                    })
                current_header = line.replace('#', '').strip()
                current_chunk = []
                header_level = level
                continue

        current_chunk.append(line)

    # Thêm chunk cuối cùng
    if current_chunk:
        chunks.append({
            'header': current_header,
            'content': '\n'.join(current_chunk).strip()
        })

    # Chia mỗi chunk thành sub-chunk tối đa 250 tokens
    chunked_data = []
    base_filename = Path(source_file).stem
    chunk_index = 1

    for chunk in chunks:
        content_text = chunk["content"]
        if not content_text.strip():
            continue

        # Tiêu đề mới theo yêu cầu
        new_title = ""
        if field:
            new_title += field
        if year:
            new_title += f" {year}"
        if department:
            new_title += f" {department}"
        new_title = new_title.strip()

        # Tiêu đề gốc viết hoa
        original_title_upper = title_line.upper()
        header_text = chunk['header']

        combined_text = f"{original_title_upper} # {header_text} {content_text}"
        tokens = combined_text.split() # Đơn giản hóa việc đếm token, có thể cần thay thế bằng thư viện nếu cần độ chính xác cao

        sub_content = ""
        for token in tokens:
            if len(sub_content.split()) + 1 > 250:
                entry = {
                    "title": new_title,
                    "content": sub_content.strip(),
                    "source_file": source_file,
                    "chunk_id": f"{base_filename}_{chunk_index}",
                    "field": field
                }
                if year:
                    entry["year"] = year
                if department:
                    entry["department"] = department
                chunked_data.append(entry)
                chunk_index += 1
                sub_content = token # Start the new sub_content with the current token
            else:
                sub_content += " " + token

        # Add the last chunk
        if sub_content.strip():
            entry = {
                    "title": new_title,
                    "content": sub_content.strip(),
                    "source_file": source_file,
                    "chunk_id": f"{base_filename}_{chunk_index}",
                    "field": field
                }
            if year:
                entry["year"] = year
            if department:
                entry["department"] = department
            chunked_data.append(entry)
            chunk_index += 1

    return chunked_data


def process_markdown_file(folder):
    folder_path = Path(folder_dir)
    output_path = Path(folder_dir) / "chunked_json"
    print(f"Processing folder: {folder_path}")
    print(f"Output folder: {output_path}")
    if not output_path.exists():
        print(f"Creating output folder: {output_path}")
        output_path.mkdir(parents=True, exist_ok=True)
    
    for file in folder_path.glob("*.md"):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Processing file: {file}")
        chunked_data = chunk_markdown(content, str(file))

        json_filename = output_path / (file.stem + ".json")
        with open(json_filename, 'w', encoding='utf-8') as out_file:
            json.dump(chunked_data, out_file, ensure_ascii=False, indent=2)

process_markdown_file(data_dir)