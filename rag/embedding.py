import os
import json
from pathlib import Path
from typing import List, Dict
from transformers import AutoModel, AutoTokenizer
import torch
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from tqdm import tqdm
import re
import uuid  # Import thư viện uuid
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)

load_dotenv()

# Cấu hình
DATA_DIR = "cleaned_data/chunked_json"
EMBEDDING_MODEL_NAME = "VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"
BATCH_SIZE = 8
MAX_LENGTH = 256
TITLE_WEIGHT = 2.0  # Ví dụ: tăng gấp đôi trọng số của tiêu đề

# Khởi tạo Qdrant client
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

# Khởi tạo model và tokenizer
tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()


def clean_text(text: str) -> str:
    """Làm sạch văn bản nhưng giữ lại cấu trúc metadata"""
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_embeddings(texts: List[str]) -> np.ndarray:
    """Tạo embeddings"""
    try:
        inputs = tokenizer(
            texts,
            padding='max_length',
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors="pt",
            return_attention_mask=True
        ).to(device)

        if torch.any(inputs["input_ids"] >= tokenizer.vocab_size):
            inputs["input_ids"] = torch.clamp(inputs["input_ids"], max=tokenizer.vocab_size - 1)

        with torch.no_grad():
            outputs = model(**inputs)

        # Sử dụng [CLS] token embedding
        embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return embeddings
    except Exception as e:
        print(f"Lỗi khi tạo embeddings: {e}")
        return np.zeros((len(texts), model.config.hidden_size))


def combine_embeddings(title_embedding: np.ndarray, content_embedding: np.ndarray, title_weight: float = 1.0) -> np.ndarray:
    """
    Kết hợp embedding của tiêu đề và nội dung bằng cách cộng có trọng số.

    Args:
        title_embedding: Embedding của tiêu đề.
        content_embedding: Embedding của nội dung.
        title_weight: Trọng số của tiêu đề (ví dụ: 2.0 để tăng gấp đôi tầm quan trọng).

    Returns:
        Embedding kết hợp.
    """
    if content_embedding.ndim == 1:
        return (title_embedding * title_weight + content_embedding) / (title_weight + 1)
    else:
        return (title_embedding * title_weight + np.mean(content_embedding, axis=0)) / (title_weight + 1)



def process_json_file(json_file_path: str) -> PointStruct:
    """Xử lý một file JSON duy nhất và tạo một PointStruct."""
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_content = ""
    title = ""
    field = ""
    year = ""
    department = ""
    chunk_ids = []

    # Lấy thông tin từ chunk đầu tiên (hoặc chunk có thông tin)
    if data:
        title = data[0].get("title", "")
        field = data[0].get("field", "")
        year = data[0].get("year", "")
        department = data[0].get("department", "")

    # Chuẩn bị danh sách chứa embeddings của các chunk
    chunk_embeddings = []

    for chunk in data:
        content = chunk.get("content", "")
        chunk_ids.append(chunk.get("chunk_id", ""))
        all_content += " " + content
        
        clean_content = clean_text(content)
        embedding = get_embeddings([clean_content])[0]  # Lấy embedding của chunk
        chunk_embeddings.append(embedding)

    # Tính embedding của tiêu đề và nội dung
    title_embedding = get_embeddings([clean_text(title)])[0]
    content_embedding = np.array(chunk_embeddings) # Chuyển thành numpy array
    # Kết hợp embedding của tiêu đề và nội dung
    combined_embedding = combine_embeddings(title_embedding, content_embedding, TITLE_WEIGHT)

    # Tạo ID hợp lệ cho Qdrant (sử dụng UUID)
    point_id = str(uuid.uuid4())

    point = PointStruct(
        id=point_id, # Sử dụng UUID thay vì hash(json_file_path)
        vector=combined_embedding.tolist(),
        payload={
            "title": title,
            "content": all_content,
            "source_file": str(json_file_path),
            "chunk_ids": chunk_ids,
            "field": field,
            "year": year,
            "department": department,
        }
    )
    return point



def create_collection(collection_name: str, vector_size: int = 768):
    """Tạo collection mới"""
    qdrant_client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )



def upload_to_qdrant(collection_name: str, points: List[PointStruct]):
    """Tải points lên Qdrant"""
    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )



def process_all_files(collection_name: str = "uit_documents_per_file"):
    """Xử lý tất cả các file JSON và tạo embeddings cho mỗi file."""
    create_collection(collection_name)
    all_points = []
    file_count = 0

    for json_file_path in Path(DATA_DIR).glob("*.json"):
        try:
            point = process_json_file(json_file_path)
            all_points.append(point)
            file_count += 1

            if len(all_points) >= 500:
                upload_to_qdrant(collection_name, all_points)
                all_points = []
                print(f"Đã tải lên {file_count} files")
        except Exception as e:
            print(f"Lỗi khi xử lý file {json_file_path}: {e}")

    if all_points:
        upload_to_qdrant(collection_name, all_points)

    print(f"Hoàn thành! Tổng cộng {file_count} files đã được tải lên collection '{collection_name}'")



if __name__ == "__main__":
    process_all_files()
