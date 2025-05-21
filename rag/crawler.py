import os
import re
import time
import hashlib
import requests
import markdownify
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

crawl_folder = 'markdown_data'
os.makedirs(crawl_folder, exist_ok=True)

VALID_FILE_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.csv', '.html', '.htm'
]

EXCLUDE_SELECTORS = [
    "header", "footer", "nav", ".navigation", ".menu", ".sidebar",
    ".breadcrumb", ".site-branding", ".site-footer", "#content-lower",
    ".region-sidebar-first", ".region-sidebar-second"
]

# Tạo tên file markdown từ URL
def url_to_filename(url, base_url):
    if url.rstrip('/') == base_url.rstrip('/'):
        return "cac-su-kien-noi-bat-trang-chu.md"
    parsed = urlparse(url)
    path = parsed.path.strip('/').replace('/', '_')
    if not path:
        path = hashlib.md5(url.encode()).hexdigest()
    return path + ".md"

# Chuyển các liên kết, ảnh, script... thành tuyệt đối
def make_links_absolute(soup, base_url):
    for tag, attr in [
        ('img', 'src'), ('a', 'href'), ('iframe', 'src'),
        ('embed', 'src'), ('object', 'data'), ('source', 'src'),
        ('link', 'href'), ('script', 'src')
    ]:
        for el in soup.find_all(tag, **{attr: True}):
            el[attr] = urljoin(base_url, el[attr])
    return soup

# Xóa các phần không cần thiết theo selector
def remove_unwanted_sections(soup):
    for selector in EXCLUDE_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()
    return soup

# Lấy các link từ thẻ <a>
def extract_links_from_a_tags(soup, base_url):
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if href and href != '#' and not href.startswith('javascript:'):
            links.append(urljoin(base_url, href))
    return links

# In ra các thẻ img để debug
def debug_print_image_tags(soup, message=""):
    images = soup.find_all('img')
    print(f"🔍 {message} - Found {len(images)} images:")
    for i, img in enumerate(images[:5]):
        print(f"  {i+1}. {img.get('src', 'No src')} - {img.get('alt', 'No alt')}")
    if len(images) > 5:
        print(f"  ... and {len(images)-5} more images")

# Chuyển thẻ img HTML sang markdown
def manual_img_to_markdown(html_content, base_url):
    img_pattern = re.compile(r'<img[^>]+src="([^"]+)"[^>]*alt="([^"]*)"[^>]*>')
    def replace_img(match):
        src = match.group(1)
        alt = match.group(2) or "image"
        if not src.startswith(('http://', 'https://')):
            src = urljoin(base_url, src)
        return f"![{alt}]({src})"
    return img_pattern.sub(replace_img, html_content)

# Kiểm tra URL có phải file cần tải không
def should_download_file(url):
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in VALID_FILE_EXTENSIONS)

# Tải file về thư mục files/
def download_file(url, folder):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        print(f"📥 Downloading file: {url}")
        resp = requests.get(url, headers=headers, stream=True)
        if resp.status_code == 200:
            filename = os.path.basename(urlparse(url).path)
            if not filename:
                filename = hashlib.md5(url.encode()).hexdigest()
                ct = resp.headers.get('Content-Type', '')
                if 'pdf' in ct: filename += '.pdf'
                elif 'word' in ct: filename += '.docx'
                elif 'excel' in ct: filename += '.xlsx'
                elif 'powerpoint' in ct: filename += '.pptx'
                elif 'text/plain' in ct: filename += '.txt'
                elif 'text/html' in ct: filename += '.html'
                else: filename += '.bin'
            files_folder = os.path.join(folder, 'files')
            os.makedirs(files_folder, exist_ok=True)
            filepath = os.path.join(files_folder, filename)
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)
            print(f"✅ Saved file: {url} -> {filepath}")
            return True
        else:
            print(f"❌ Failed to download {url} - Status: {resp.status_code}")
    except Exception as e:
        print(f"❗ Error downloading {url}: {e}")
    return False

# Crawl trang web và lưu thành markdown
def crawl_and_save(url, folder, base_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    if should_download_file(url):
        download_file(url, folder)
        return []
    try:
        print(f"🌐 Crawling: {url}")
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            debug_print_image_tags(soup, "Original HTML")
            soup = make_links_absolute(soup, url)
            a_links = extract_links_from_a_tags(soup, url)
            content_selectors = [
                'div.field-item', 'div.field__item', 'div.main-content',
                'div.content-body', 'article .content', 'div.node-content',
                'div.body-content', 'div.entry-content', 'div.post-content',
                '.field-name-body'
            ]
            main_content = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    main_content = elements[0]
                    print(f"✓ Found content using selector: {selector}")
                    break
            if not main_content:
                main_content = soup.find('article') or soup.find('main') or soup.find('div', {'id': 'content'})
            if not main_content:
                main_content = soup.find('body')
                print("⚠️ Using fallback to body content")
            if main_content:
                debug_print_image_tags(main_content, "Before conversion")
                main_content_html = str(main_content)
                # Xử lý iframe
                iframe_info = []
                for idx, iframe in enumerate(main_content.find_all('iframe', src=True)):
                    src = iframe.get('src', '')
                    if src:
                        abs_src = urljoin(url, src)
                        iframe_info.append(f"**Iframe {idx+1}**: [{abs_src}]({abs_src})")
                # Chuyển HTML sang Markdown
                markdown_content = markdownify.markdownify(
                    main_content_html, heading_style="ATX", wrap=0
                )
                # Xử lý ảnh thủ công nếu markdownify bỏ sót
                manual_markdown = manual_img_to_markdown(main_content_html, url)
                if "![" not in markdown_content and "<img" in main_content_html:
                    print("⚠️ markdownify không chuyển đổi hình ảnh, dùng xử lý thủ công")
                    img_tags = re.findall(r'<img[^>]+>', main_content_html)
                    for img_tag in img_tags:
                        src_match = re.search(r'src="([^"]+)"', img_tag)
                        alt_match = re.search(r'alt="([^"]+)"', img_tag)
                        if src_match:
                            src = src_match.group(1)
                            alt = alt_match.group(1) if alt_match else "image"
                            if not src.startswith(('http://', 'https://')):
                                src = urljoin(url, src)
                            img_md = f"![{alt}]({src})"
                            if img_tag in markdown_content:
                                markdown_content = markdown_content.replace(img_tag, img_md)
                            else:
                                h2_match = re.search(r'## [^\n]+\n', markdown_content)
                                if h2_match:
                                    insert_pos = h2_match.end()
                                    markdown_content = markdown_content[:insert_pos] + "\n" + img_md + "\n\n" + markdown_content[insert_pos:]
                                else:
                                    markdown_content += f"\n\n{img_md}\n"
                # Thêm tiêu đề và nguồn
                title = soup.title.string.strip() if soup.title else "Không có tiêu đề"
                markdown_content = f"# {title}\n\n_Nguồn: [{url}]({url})_\n\n{markdown_content}"
                # Thêm thông tin iframe nếu có
                if iframe_info:
                    markdown_content += "\n\n## Embedded Content (iframes)\n\n" + "\n\n".join(iframe_info)
                # Lưu file markdown
                filename = url_to_filename(url, base_url)
                filepath = os.path.join(folder, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f"✅ Saved: {url} -> {filepath}")
                if "![" in markdown_content:
                    print(f"📷 Markdown contains images!")
                else:
                    print("⚠️ No images detected in the markdown output")
                    backup_filepath = os.path.join(folder, f"manual_{filename}")
                    with open(backup_filepath, 'w', encoding='utf-8') as f:
                        f.write(f"# {title}\n\n_Nguồn: [{url}]({url})_\n\n{manual_markdown}")
                    print(f"⚙️ Saved backup with manual image processing: {backup_filepath}")
            else:
                print(f"❌ No content found at: {url}")
            return a_links
        else:
            print(f"❌ Failed to get {url} - Status: {resp.status_code}")
    except Exception as e:
        print(f"❗ Error crawling {url}: {e}")
        import traceback
        traceback.print_exc()
    return []

if __name__ == "__main__":
    base_url = 'https://tuyensinh.uit.edu.vn/'
    visited = set()
    links = crawl_and_save(base_url, crawl_folder, base_url)
    visited.add(base_url.rstrip('/'))
    if links:
        filtered_links = []
        for link in links:
            try:
                if not link or not isinstance(link, str):
                    continue
                link = link.split('#')[0].strip()
                if not link:
                    continue
                parsed = urlparse(link)
                is_same_domain = 'tuyensinh.uit.edu.vn' in parsed.netloc
                if is_same_domain and link.rstrip('/') not in visited:
                    filtered_links.append(link)
            except Exception as e:
                print(f"⚠️ Skipping malformed link due to: {e}")
        for link in tqdm(filtered_links, desc="🔄 Crawling links"):
            if link.rstrip('/') not in visited:
                crawl_and_save(link, crawl_folder, base_url)
                visited.add(link.rstrip('/'))
                time.sleep(1)