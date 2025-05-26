import os
from pathlib import Path
import uuid
from typing import List, Dict, Any, Optional, Union
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType
from dotenv import load_dotenv

load_dotenv()

class DocEmbedder:
    def __init__(
            self,
            model_name: str = 'AITeamVN/Vietnamese_Embedding',
            qdrant_url: str = os.getenv("QDRANT_URL"),
            qdrant_api_key: str = os.getenv("QDRANT_API_KEY"),
            collection_name: str = "uit_documents_AITeamVN",
            vector_size: int = 1024,
            distance: str = Distance.COSINE,
    ):
        self.model = SentenceTransformer(model_name)
        self.qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
        )
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance
        
    def create_collection(self, index_fields: Optional[List[str]] = None):
        collection_name = self.collection_name
        self.qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=self.vector_size, distance=self.distance)
        )

        default_fields = ["title", "header", "content", "field", "year", "department", "keywords", "source"]
        field_to_index = index_fields if index_fields is not None else default_fields
        
        for field in field_to_index:
            try:
                self.qdrant_client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print(f"* Index cho trường '{field}' đã được tạo.")
            except Exception as e:
                print(f"! Không thể tạo index cho '{field}': {e}")

    def encode_document(self, document: List[Dict[str, Any]]) -> List[PointStruct]:
        text = []
        for doc in document:
            combined_text = "\n".join(
                [doc.get("title", ""), doc.get("title", ""), doc.get("header", ""), doc.get("header", ""), doc.get("header", ""), doc.get("header", ""), doc.get("header", ""), doc.get("content", "")]
            )
            text.append(combined_text)
        
        embeddings = self.model.encode(text, show_progress_bar=True)

        points = []

        for doc, embedding in zip(document, embeddings):
            point_id = str(uuid.uuid4())

            for key in ["keywords", "prev_chunk", "next_chunk"]:
                if key in doc and not isinstance(doc[key], list):
                    doc[key] = [doc[key]] if doc[key] else []

            point = PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload={
                    "title": doc.get("title", ""),
                    "header": doc.get("header", ""),
                    "content": doc.get("content", ""),
                    "chunk_id": doc.get("chunk_id", ""),
                    "field": doc.get("field", ""),
                    "year": doc.get("year", ""),
                    "department": doc.get("department", ""),
                    "keywords": doc.get("keywords", []),
                    # "prev_chunk": doc.get("prev_chunk", ""),
                    # "next_chunk": doc.get("next_chunk", ""),
                    "source": doc.get("source", "")
                }
            )
            points.append(point)
        
        return points

    def upload_points(self, points: List[PointStruct], batch_size: int = 500):  
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            print(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1} ({len(batch)} points)")

    def process_and_upload(self, documents: List[Dict[str, Any]], batch_size: int = 500):
        points = self.encode_document(documents)
        self.upload_points(points, batch_size=batch_size)
        return len(points)

if __name__ == "__main__":
    embedder = DocEmbedder()
    embedder.create_collection()
    data_dir = "json/json_AITeamVN"

    for json_file in Path(data_dir).glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            documents = json.load(f)
        num_points = embedder.process_and_upload(documents)
        print(f"Processed {num_points} points from {json_file.name}")
