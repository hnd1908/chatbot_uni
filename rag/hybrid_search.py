import numpy as np
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter
from sentence_transformers import SentenceTransformer
import unicodedata
from unidecode import unidecode
import re
from dotenv import load_dotenv
import os
import math
import glob
import json
import pickle
from pyvi.ViTokenizer import tokenize
import time

t0 = time.time()
# Load environment variables
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(dotenv_path)

# Load stopwords
with open(os.path.join(os.path.dirname(__file__), 'vietnamese-stopwords.txt'), encoding='utf-8') as f:
    STOPWORDS = set([line.strip() for line in f if line.strip() and not line.startswith('//')])

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def remove_stopword(text):
    return ' '.join([w for w in text.split() if w not in STOPWORDS])

def generate_ngrams(tokens: List[str], n: int) -> List[str]:
    return ['_'.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def preprocess_text(text, ngram_range=(1, 2)) -> str:
    text = normalize_text(text)
    text = tokenize(text)
    text = remove_stopword(text)
    tokens = text.split()
    
    ngrams = []
    for n in range(ngram_range[0], ngram_range[1] + 1):
        ngrams.extend(generate_ngrams(tokens, n))
    
    return ' '.join(ngrams)


class BM25:
    def __init__(self, k1=1.5, b=0.75):
        self.b = b
        self.k1 = k1

    def fit(self, corpus):
        tf = []
        df = {}
        idf = {}
        doc_len = []
        corpus_size = 0
        for document in corpus:
            corpus_size += 1
            doc_len.append(len(document))
            frequencies = {}
            for term in document:
                term_count = frequencies.get(term, 0) + 1
                frequencies[term] = term_count
            tf.append(frequencies)
            for term, _ in frequencies.items():
                df_count = df.get(term, 0) + 1
                df[term] = df_count
        for term, freq in df.items():
            idf[term] = math.log(1 + (corpus_size - freq + 0.5) / (freq + 0.5))
        self.tf_ = tf
        self.df_ = df
        self.idf_ = idf
        self.doc_len_ = doc_len
        self.corpus_ = corpus
        self.corpus_size_ = corpus_size
        self.avg_doc_len_ = sum(doc_len) / corpus_size
        return self

    def search(self, query):
        scores = [self._score(query, index) for index in range(self.corpus_size_)]
        return scores

    def _score(self, query, index):
        score = 0.0
        doc_len = self.doc_len_[index]
        frequencies = self.tf_[index]
        for term in query:
            if term not in frequencies:
                continue
            freq = frequencies[term]
            numerator = self.idf_[term] * freq * (self.k1 + 1)
            denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len_)
            score += (numerator / denominator)
        return score

class HybridSearchQdrant:
    def __init__(
        self,
        qdrant_url: str,
        qdrant_api_key: str,
        collection_name: str,
        embedding_model: SentenceTransformer,
        chunk_dir: str = None,
        ngram_range: tuple = (1, 2),
        semantic_weight: float = 0.5,
        bm25_weight: float = 0.5,
        min_confidence_semantic_threshold: float = 0.0,
        min_confidence_bm25_threshold: float = 0.0,
        bm25_pickle_path: str = "bm25_model.pkl"
    ):
        self.qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10
        )
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.semantic_weight = semantic_weight
        self.bm25_weight = bm25_weight
        self.min_confidence_semantic_threshold = min_confidence_semantic_threshold
        self.min_confidence_bm25_threshold = min_confidence_bm25_threshold
        self.chunk_dir = chunk_dir
        self.bm25_pickle_path = bm25_pickle_path
        self._load_or_build_bm25()
        self.ngram_range = ngram_range

    def _load_or_build_bm25(self):
        if os.path.exists(self.bm25_pickle_path):
            with open(self.bm25_pickle_path, "rb") as f:
                bm25_data = pickle.load(f)
                self.bm25_model = bm25_data["model"]
                self.bm25_doc_map = bm25_data["doc_map"]
        else:
            bm25_docs = []
            bm25_doc_map = []
            for file in glob.glob(os.path.join(self.chunk_dir, '*_chunks.json')):
                with open(file, encoding='utf-8') as f:
                    data = json.load(f)
                    for chunk in data:
                        content = chunk.get('content', '')
                        processed = preprocess_text(content, ngram_range=(1, 5))  # unigram + bigram
                        bm25_docs.append(processed.split())
                        bm25_doc_map.append(chunk)
            self.bm25_model = BM25()
            self.bm25_model.fit(bm25_docs)
            self.bm25_doc_map = bm25_doc_map
            with open(self.bm25_pickle_path, "wb") as f:
                pickle.dump({"model": self.bm25_model, "doc_map": self.bm25_doc_map}, f)

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k * 20,
            with_payload=True,
            query_filter=None
        )
        bm25_query = preprocess_text(query).split()
        bm25_scores = self.bm25_model.search(bm25_query)
        bm25_score_map = {self.bm25_doc_map[i].get('chunk_id'): bm25_scores[i] for i in range(len(bm25_scores))}
        max_bm25 = max(bm25_scores) if bm25_scores else 1.0
        results_with_scores = []
        for res in results:
            payload = res.payload or {}
            semantic_score = res.score
            bm25_score = bm25_score_map.get(payload.get('chunk_id'), 0.0)
            bm25_score_norm = bm25_score / max_bm25 if max_bm25 else 0.0
            combined_score = self.semantic_weight * semantic_score + self.bm25_weight * bm25_score_norm
            if semantic_score >= self.min_confidence_semantic_threshold and bm25_score >= self.min_confidence_bm25_threshold:
                payload = payload.copy()
                payload['semantic_score'] = float(semantic_score)
                payload['bm25_score'] = float(bm25_score_norm)
                payload['combined_score'] = float(combined_score)
                results_with_scores.append((payload, combined_score))
        results_with_scores.sort(key=lambda x: x[1], reverse=True)
        final_results = [res for res, _ in results_with_scores[:top_k]]
        return final_results
    
    def get_top_bm25_keywords_for_chunk(self, chunk_index, top_n=10):
        """
        Trả về list (term, score) BM25 quan trọng nhất cho chunk_index.
        Yêu cầu: self phải có self.bm25_model và self.bm25_doc_map.
        """
        chunk_terms = self.bm25_model.corpus_[chunk_index]
        term_scores = {term: self.bm25_model._score([term], chunk_index) for term in set(chunk_terms)}
        important_terms = sorted(term_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return important_terms

    def get_top_bm25_keywords_for_chunk_id(self, chunk_id, top_n=10):
        """
        Trả về list (term, score) BM25 quan trọng nhất cho chunk_id.
        """
        for idx, chunk in enumerate(self.bm25_doc_map):
            if chunk.get('chunk_id') == chunk_id:
                return self.get_top_bm25_keywords_for_chunk(idx, top_n)
        return []

    def print_top_bm25_keywords(self, top_n=10):
        """
        In ra top N từ khóa BM25 cho từng chunk.
        """
        for idx, chunk in enumerate(self.bm25_doc_map):
            chunk_id = chunk.get('chunk_id', f'chunk_{idx}')
            title = chunk.get('title', '')
            keywords = self.get_top_bm25_keywords_for_chunk(idx, top_n)
            print(f"\n--- Chunk {idx+1} | ID: {chunk_id} | Title: {title} ---")
            for term, score in keywords:
                print(f"  {term}: {score:.4f}")
    

# Để import dùng từ views.py:
# from rag.hybrid_search import HybridSearchQdrant
# model = SentenceTransformer('AITeamVN/Vietnamese_Embedding')
# search_engine = HybridSearchQdrant(
#     qdrant_url=os.getenv("QDRANT_URL"),
#     qdrant_api_key=os.getenv("QDRANT_API_KEY"),
#     collection_name="uit_documents_AITeamVN",
#     embedding_model=model,
#     semantic_weight=0.5,
#     bm25_weight=0.5
# )
# results = search_engine.search(query, top_k=5)

if __name__ == "__main__":
    model = SentenceTransformer('AITeamVN/Vietnamese_Embedding')
    search_engine = HybridSearchQdrant(
        qdrant_url=os.getenv("QDRANT_URL"),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        collection_name="uit_documents_AITeamVN",
        embedding_model=model,
        chunk_dir=os.path.join(os.path.dirname(__file__), 'json', 'json_AITeamVN'),
        ngram_range=(1, 5),
        semantic_weight=0.5,
        bm25_weight=0.5,
        min_confidence_semantic_threshold=0.3,
        min_confidence_bm25_threshold = 0.6
    )
    t1 = time.time()
    print("khởi tạo thành công, chuẩn bị in keywords mỗi chunk: ", t1-t0)
    search_engine.print_top_bm25_keywords(top_n=5)
    t2 = time.time()
    print("nhập câu hỏi: ", t2-t0)
    while True:
        query = input("\nNhập câu hỏi (hoặc 'exit' để thoát): ").strip()
        if query.lower() == "exit":
            break
        results = search_engine.search(query, top_k=5)
        for i, doc in enumerate(results):
            print(f"\n--- Kết quả {i+1} ---")
            print(f"Score: {doc['combined_score']:.4f}")
            print(f"Semantic Score: {doc['semantic_score']:.4f}")
            print(f"BM25 Score: {doc['bm25_score']:.4f}")
            print(f"Title: {doc.get('title', '')}")
            print(f"Field: {doc.get('field', '')}")
            print(f"Department: {doc.get('department', '')}")
            print(f"Year: {doc.get('year', '')}")
            print(f"Content: {doc.get('content', '')[:500]}...")