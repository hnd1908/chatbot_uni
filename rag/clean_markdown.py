import os
import re

markdown_folder = 'markdown_data'
cleaned_folder = 'cleaned_data/markdown'
os.makedirs(cleaned_folder, exist_ok=True)

excluded_keywords = [
    "thong-bao-muc-diem", "thong-bao-ket-qua", "ba44e70ae712a2cf3e6533000212f833",
    "goc-bao-chi", "giay-bao-nhaphoc", "giaybao-nhaphoc", "diem-chuan", "cam-nang-tuyen-sinh-2023", "chuong-trinh-dac-biet",
    "cuoc-song-sinh-vien", "su-kien-noi-bat", "vb2-lien-thong",
]

def remove_after_keyword(content, keyword):
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if keyword in line:
            break
        new_lines.append(line)
    return "\n".join(new_lines)

def should_exclude_file(filename, content):
    parts = filename.replace('.md', '').split('-')
    if any(keyword in '-'.join(parts) for keyword in excluded_keywords):
        return True
    if not content.strip():
        return True
    return False

def clean_markdown(content):
    lines = content.splitlines()

    first_line = lines[0]

    cleaned_lines = [line.replace('#', '') for line in lines[1:]]

    cleaned_lines = [line.replace('*', '') for line in lines[1:]]

    cleaned_content = '\n'.join([first_line] + cleaned_lines)

    cleaned_content = re.sub(r'[\u00a0\u200b\ufeff]+', ' ', cleaned_content)

    cleaned_content = re.sub(r'<.*?>', '', cleaned_content)
    
    cleaned_content = re.sub(r'\n\s*\n', '\n', cleaned_content)  # Loại bỏ các dòng trống thừa

    cleaned_content = re.sub(r'[-=_]{5,}', '', cleaned_content)  # Xóa các đường kẻ dài

    cleaned_content = re.sub(r'\[Skip to content\].*?\]', '', cleaned_content)

    cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_content)

    keyword = ['## Trang', "## Thông tin khác", "=>> Xem thêm"]

    for kw in keyword:
        cleaned_content = remove_after_keyword(cleaned_content, kw)

    cleaned_content = re.sub(r'!\[.*?\]\(.*?\)', '', cleaned_content)

    # La mã (I., II., etc.) → # I. Giới thiệu
    cleaned_content = re.sub(r'^\s*([IVXLCDM]{1,5})\.\s*(.*)', r'## \1. \2', cleaned_content, flags=re.MULTILINE)

    # 1.1.1 → #### 1.1.1 Giới thiệu
    cleaned_content = re.sub(r'^\s*(\d+)\.(\d+)\.(\d+)\s*(.*)', r'##### \1.\2.\3 \4', cleaned_content, flags=re.MULTILINE)

    # 1.1 → ### 1.1 Giới thiệu
    cleaned_content = re.sub(r'^\s*(\d+)\.(\d+)\s+(.*)', r'#### \1.\2 \3', cleaned_content, flags=re.MULTILINE)

    # 1. → ## 1. Giới thiệu
    cleaned_content = re.sub(r'^\s*(\d+)\.\s+(.*)', r'### \1. \2', cleaned_content, flags=re.MULTILINE)

    # Nếu không có header nào thì thêm tiêu đề mặc định
    if not re.search(r'^#{1,4} ', cleaned_content, flags=re.MULTILINE):
        cleaned_content = '# Nội dung\n\n' + cleaned_content

    cleaned_content = re.sub(
        r'^(#{2,5}\s*[^\n:]+):\s*(.+)',
        r'\1\n\2',
        cleaned_content,
        flags=re.MULTILINE
    )
    
    return cleaned_content.strip()

def process_markdown_files(markdown_folder, cleaned_folder):
    for markdown_file in os.listdir(markdown_folder):
        if markdown_file.endswith('.md'):
            markdown_filepath = os.path.join(markdown_folder, markdown_file)
            with open(markdown_filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if should_exclude_file(markdown_file, content):
                print(f"Excluded: {markdown_file}")
                continue

            cleaned_content = clean_markdown(content)
            cleaned_filepath = os.path.join(cleaned_folder, markdown_file)
            with open(cleaned_filepath, 'w', encoding='utf-8') as cleaned_file:
                cleaned_file.write(cleaned_content)
            
            print(f"Cleaned: {markdown_file} -> {cleaned_filepath}")



process_markdown_files(markdown_folder, cleaned_folder)
