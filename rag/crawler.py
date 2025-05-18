import os
import re
from urllib.parse import urlparse, unquote, urljoin
import time
import requests
from bs4 import BeautifulSoup

def convert_table_to_markdown(table):
    """
    Chuyển đổi bảng HTML sang định dạng Markdown.

    Args:
        table (bs4.element.Tag): Đối tượng bảng HTML.

    Returns:
        str: Chuỗi Markdown biểu diễn bảng.
    """
    rows = table.find_all('tr')
    if not rows:
        return ""

    markdown = []

    # Xử lý hàng tiêu đề
    headers = []
    for th in rows[0].find_all(['th', 'td']):
        headers.append(th.get_text(strip=True))

    if headers:
        markdown.append('| ' + ' | '.join(headers) + ' |')
        markdown.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')

    # Xử lý các hàng dữ liệu
    for row in rows[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
        if cells:
            markdown.append('| ' + ' | '.join(cells) + ' |')

    return '\n\n' + '\n'.join(markdown) + '\n\n'

def extract_main_content(html_content, is_base_url=False):
    """
    Trích xuất nội dung chính từ HTML.

    Args:
        html_content (str): Chuỗi HTML.
        is_base_url (bool, optional): Xác định xem đây có phải là base URL không. Mặc định là False.

    Returns:
        str: Nội dung chính của trang web dưới dạng chuỗi.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Loại bỏ các phần tử không cần thiết
    for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'form', 'aside']):
        element.decompose()

    # Loại bỏ các ảnh không cần thiết (chỉ giữ lại ảnh trong nội dung chính)
    for img in soup.find_all('img'):
        if not img.find_parent('main') and not img.find_parent('article'):
            img.decompose()

    if is_base_url:
        main_content = soup.find('div', {'class': 'main-content'})
    else:
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article|post'))

    if not main_content:
        main_content = soup.find('body')

    if main_content:
        # Xử lý bảng
        for table in main_content.find_all('table'):
            markdown_table = convert_table_to_markdown(table)
            table.replace_with(markdown_table)

        # Lấy text và xử lý
        text = main_content.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n\n'.join(lines)

    return None # Trả về None nếu không trích xuất được nội dung

def generate_file_name(url):
    """
    Tạo tên file từ URL.

    Args:
        url (str): URL của trang web.

    Returns:
        str: Tên file hợp lệ.
    """
    decoded_url = unquote(url)
    parsed_url = urlparse(decoded_url)
    path = parsed_url.path.strip('/')

    if path:
        parts = path.split('/')
        file_name = parts[-1]
        file_name = re.sub(r'\.[^.]+$', '', file_name) # Loại bỏ phần mở rộng
        file_name = file_name.replace('/', '_') # Đảm bảo không còn dấu gạch chéo
    else:
        file_name = parsed_url.netloc.replace('.', '_')

    if len(file_name) > 100:
        file_name = file_name[:100]

    return file_name

def process_url(url, output_dir, visited_urls, base_url, recursive=False):
    """
    Xử lý một URL, lưu nội dung markdown và đệ quy nếu cần.

    Args:
        url (str): URL của trang web cần xử lý.
        output_dir (str): Đường dẫn thư mục để lưu file markdown.
        visited_urls (set): Tập hợp các URL đã được truy cập.
        base_url (str): URL gốc để đệ quy.
        recursive (bool, optional): Có thực hiện đệ quy hay không. Mặc định là False.

    Returns:
        tuple: (True, tên file) nếu thành công, (False, None) nếu thất bại.
    """
    try:
        print(f"Processing URL: {url}")

        # Tạo tên file
        file_name = generate_file_name(url)
        markdown_path = os.path.join(output_dir, f"{file_name}.md")

        # Kiểm tra nếu file đã tồn tại
        if os.path.exists(markdown_path):
            timestamp = int(time.time())
            file_name = f"{file_name}_{timestamp}"
            markdown_path = os.path.join(output_dir, f"{file_name}.md")
            print(f"File exists, using new name: {file_name}")

        # Lấy nội dung
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for bad status codes.
        html_content = response.text
        is_base = (url == base_url)
        markdown_content = extract_main_content(html_content, is_base_url=is_base)

        if markdown_content: # Chỉ lưu và đệ quy nếu có nội dung
            # Add source URL to the end of the content
            markdown_content += f"\n\nSource: {url}"

            # Lưu nội dung markdown
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"Saved content to: {markdown_path}")

            # Đệ quy nếu là base URL, chưa được thăm và có nội dung
            if recursive and url == base_url and url not in visited_urls:
                visited_urls.add(url) # Thêm url hiện tại vào set
                soup = BeautifulSoup(response.content, 'html.parser') # Sử dụng response.content
                links = soup.find_all('a', href=True)
                for a_tag in links:
                    href = a_tag.get('href')
                    if href:
                        absolute_url = urljoin(base_url, href)
                        if absolute_url.startswith(base_url) and absolute_url not in visited_urls: # Chỉ crawl các URL cùng base URL và chưa được thăm
                            process_url(absolute_url, output_dir, visited_urls, base_url, recursive) # Đệ quy
            return True, file_name
        else:
            print(f"Could not extract content from {url}")
            return False, None

    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return False, None

def main():
    """
    Hàm chính để crawl dữ liệu.
    """
    # Khai báo base URL và additional URLs
    base_url = 'https://tuyensinh.uit.edu.vn/'
    additional_urls = [
        "https://student.uit.edu.vn/content/cu-nhan-nganh-toan-thong-tin-ap-dung-tu-khoa-19-2024",
        "https://student.uit.edu.vn/content/cu-nhan-nganh-cong-nghe-thong-tin-ap-dung-tu-khoa-19-2024",
        "https://student.uit.edu.vn/content/cu-nhan-nganh-he-thong-thong-tin-ap-dung-tu-khoa-19-2024",
        "https://student.uit.edu.vn/content/cu-nhan-khoa-hoc-nganh-khoa-hoc-du-lieu-ap-dung-tu-khoa-19-2024",
        "https://student.uit.edu.vn/content/cu-nhan-nganh-khoa-hoc-may-tinh-ap-dung-tu-khoa-19-2024",
        "https://student.uit.edu.vn/content/cu-nhan-nganh-ky-thuat-may-tinh-ap-dung-tu-khoa-19-2024",
        "https://student.uit.edu.vn/content/cu-nhan-nganh-ky-thuat-phan-mem-ap-dung-tu-khoa-19-2024",
        "https://student.uit.edu.vn/content/cu-nhan-nganh-mang-may-tinh-va-truyen-thong-du-lieu-ap-dung-tu-khoa-19-2024",
        "https://student.uit.edu.vn/content/cu-nhan-nganh-thiet-ke-vi-mach-ap-dung-tu-khoa-19-2024",
        "https://student.uit.edu.vn/content/cu-nhan-nganh-thuong-mai-dien-tu-ap-dung-tu-khoa-19-2024",
        "https://student.uit.edu.vn/content/cu-nhan-nganh-truyen-thong-da-phuong-tien-ap-dung-tu-khoa-20-2025",
        "https://student.uit.edu.vn/content/cu-nhan-nganh-tri-tue-nhan-tao-ap-dung-tu-khoa-19-2024"
    ]
    visited_urls = set() # Set để theo dõi các URL đã được thăm

    crawl_folder = 'markdown_data' #Sử dụng biến crawl_folder
    os.makedirs(crawl_folder, exist_ok=True)
    print(f"Output directory: {crawl_folder}")

    success_count = 0
    failed_urls = []

    # Crawl base URL (có đệ quy)
    success, file_name = process_url(base_url, crawl_folder, visited_urls, base_url, recursive=True)
    if success:
        success_count += 1
        print(f"✅ Saved: {file_name}.md")
    else:
        failed_urls.append(base_url)

    # Crawl additional URLs (không đệ quy)
    for url in additional_urls:
        success, file_name = process_url(url, crawl_folder, visited_urls, base_url, recursive=False)
        if success:
            success_count += 1
            print(f"✅ Saved: {file_name}.md")
        else:
            failed_urls.append(url)

    # Log summary
    print(f"Complete! Successfully processed {success_count}/{len(additional_urls) + 1} URLs") # Thay đổi len() để phản ánh đúng số lượng URL
    if failed_urls:
        print(f"Failed URLs: {len(failed_urls)}")
        with open("failed_urls.txt", "w", encoding="utf-8") as f:
            for url in failed_urls:
                f.write(f"{url}\n")
    print(f"Base URL được crawl đệ quy: {base_url}")


if __name__ == "__main__":
    main()