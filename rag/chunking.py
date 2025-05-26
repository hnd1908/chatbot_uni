import os
import re
import sys
import json
from pathlib import Path
from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from sentence_transformers import SentenceTransformer
from pyvi.ViTokenizer import tokenize
from datetime import datetime
from unidecode import unidecode

class LocalEmbeddings:
    def __init__(self, model_name='AITeamVN/Vietnamese_Embedding'):
        self.model = SentenceTransformer(model_name)
    def embed_documents(self, texts):
        return self.model.encode(texts, convert_to_numpy=True).tolist()
    def embed_query(self, text):
        return self.model.encode([text], convert_to_numpy=True)[0].tolist()

def extract_year_from_filename(filename):
    match = re.search(r'20\d{2}', filename)
    return match.group(0) if match else None

def count_keywords_by_category(text, keywords_dict):
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

    text_no_accent = unidecode(text.lower())

    category_counts, found_keywords = count_keywords_by_category(text, keywords_dict)

    nganh_count = sum(category_counts.get(cat, 0) for cat in nganh_categories)
    grouped_counts = category_counts.copy()
    for cat in nganh_categories:
        grouped_counts.pop(cat, None)
    grouped_counts["ngành học"] = nganh_count

    all_found_keywords = []
    for kw_list in found_keywords.values():
        all_found_keywords.extend(kw_list)

    first_pos = len(text_no_accent) + 1
    selected_category = None
    selected_nganh = None

    for cat in nganh_categories:
        for kw in keywords_dict.get(cat, []):
            idx = text_no_accent.find(unidecode(kw.lower()))
            if idx != -1 and idx < first_pos:
                first_pos = idx
                selected_category = "ngành học"
                selected_nganh = cat

    for category, keywords in keywords_dict.items():
        if category in nganh_categories:
            continue
        for kw in keywords:
            idx = text_no_accent.find(unidecode(kw.lower()))
            if idx != -1 and idx < first_pos:
                first_pos = idx
                selected_category = category
                selected_nganh = None

    department = None
    if selected_nganh:
        department = nganh_name_map.get(selected_nganh, selected_nganh)

    if selected_category == "ngành học" and nganh_count > 0:
        return "ngành", category_counts, all_found_keywords, department

    elif selected_category:
        field_name = (
            "học bổng" if selected_category == "hoc_bong" else
            "tuyển sinh" if selected_category in ["tuyensinh", "diem"] else
            "ngoài lề" if selected_category not in ["truong", "hoc_bong", "tuyensinh", "diem"] else
            "trường"
        )
        return field_name, category_counts, all_found_keywords, department

    return "ngoài lề", category_counts, all_found_keywords, department

def get_keywords(text, keywords_dict):
    text_lower = text.lower()
    found_keywords = set()

    for category, keywords in keywords_dict.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                found_keywords.add(kw)

    return list(found_keywords)

def determine_field_from_filename(filename, keywords_dict):
    text = filename.lower().replace("_", " ").replace("-", " ")
    print(text)
    return determine_field_from_keywords(text, keywords_dict)


def chunk_markdown(content, source_file, keywords_dict, output_dir):
    filename = Path(source_file).name
    title_line = Path(source_file).stem.replace("_", " ").title()
    year = extract_year_from_filename(filename)

    field, category_counts, _, filename_department = determine_field_from_filename(filename, keywords_dict)

    lines = content.splitlines()

    if lines and lines[0].startswith("#"):
        title_line = lines[0].replace("#", "").strip()

    source = None
    rel_path = os.path.relpath(source_file)
    # rel_path = os.path.relpath(source_file).replace("cleaned_data\\markdown", "markdown_data")
    source = rel_path

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

    splitter = SemanticChunker(LocalEmbeddings(), breakpoint_threshold_type="interquartile", breakpoint_threshold_amount=0.9,buffer_size=10)
    result = []
    chunk_counter = 0

    for header, chunk_text in chunks:
        sub_chunks = splitter.split_text(chunk_text)
        
        for sub_text in sub_chunks:
            chunk_counter += 1
            chunk_id = f"{Path(source_file).stem}_chunk_{chunk_counter}"

            department = filename_department
            category_counts, _ = count_keywords_by_category(sub_text, keywords_dict)
            found_keywords = list(category_counts.keys())
            metadata = {
                "title": title_line,
                "header": header,
                "content": sub_text,
                "chunk_id": chunk_id,
                "field": field,
                "year": year,
                "department": department,
                "keywords": found_keywords,
                # "prev_chunk": None,
                # "next_chunk": None,
                "source": source,
                # "admission_info": admission_info if field == "tuyển sinh" else {},
            }
            result.append(metadata)

    # for i in range(len(result)):
    #     if i > 0:
    #         result[i]["prev_chunk"] = result[i-1]["chunk_id"]
    #     if i < len(result) - 1:
    #         result[i]["next_chunk"] = result[i+1]["chunk_id"]

    return result

def save_chunks_to_json(chunks, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

def main():
    markdown_dir = "markdown_data"
    output_dir = "json/json_AITeamVN"
    keywords_file = "keywords.py"
    os.makedirs(output_dir, exist_ok=True)
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