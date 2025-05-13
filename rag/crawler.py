import requests
from bs4 import BeautifulSoup
import markdownify
import os
from urllib.parse import urlparse, urljoin
import hashlib
import time

crawl_folder = 'markdown_data'
os.makedirs(crawl_folder, exist_ok=True)

def url_to_filename(url):
    parsed = urlparse(url)
    path = parsed.path.strip('/').replace('/', '_')
    if not path:
        path = hashlib.md5(url.encode()).hexdigest()
    return path + ".md"

def crawl_and_save(url, folder):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            main_content = soup.find('div', {'class': 'main-content'})
            if main_content:
                markdown_content = markdownify.markdownify(str(main_content), heading_style="ATX")
                filename = url_to_filename(url)
                filepath = os.path.join(folder, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f"Saved: {url} -> {filename}")
            else:
                print(f"No main-content found at: {url}")
            
            return links
        else:
            print(f"Failed to get {url} - Status: {response.status_code}")
    except Exception as e:
        print(f"Error crawling {url}: {e}")
    return None

base_url = 'https://tuyensinh.uit.edu.vn/'
visited = set()

links = crawl_and_save(base_url, crawl_folder)
visited.add(base_url.rstrip('/'))

if links:
    for link in links:
        href = link['href'].split('#')[0].strip()

        if href.startswith('http') and 'tuyensinh.uit.edu.vn' not in href:
            continue

        full_url = urljoin(base_url, href)
        norm_url = full_url.rstrip('/')

        if norm_url not in visited:
            crawl_and_save(norm_url, crawl_folder)
            visited.add(norm_url)
            time.sleep(1)
