import numpy as np
from typing import List, Dict, Any, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchAny, MatchValue
from sentence_transformers import SentenceTransformer
from .keywords import keywords_dict
import unicodedata
from unidecode import unidecode
import re
from dotenv import load_dotenv
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(dotenv_path)

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

def extract_field_department_year(question: str, keywords_dict: dict):
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

    text = question
    text_no_accent = unidecode(text.lower())

    # Extract year
    match = re.search(r'20\d{2}', question)
    year = match.group(0) if match else None

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
        field = "ngành"
    elif selected_category:
        field = (
            "học bổng" if selected_category == "hoc_bong" else
            "tuyển sinh" if selected_category in ["tuyensinh", "diem"] else
            "trường" if selected_category == "truong" else
            "ngoài lề"
        )
    else:
        field = "ngoài lề"

    # Trả về field, list các key (category) tìm được, list từ khóa thực sự, department, year
    return field, list(category_counts.keys()), all_found_keywords, department, year

class HybridSearchQdrant:
    def __init__(
        self,
        qdrant_url: str,
        qdrant_api_key: str,
        collection_name: str,
        embedding_model: SentenceTransformer,
        metadata_weight: float = 0.4,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.2,
        field_weight: float = 0.3,
        department_weight: float = 0.3,
        year_weight: float = 0.2,
        min_confidence_threshold: float = 0.0
    ):
        self.qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10
        )
        self.collection_name = collection_name
        self.embedding_model = embedding_model

        self.metadata_weight = metadata_weight
        self.semantic_weight = semantic_weight

        total = keyword_weight + field_weight + department_weight + year_weight
        self.keyword_weight = keyword_weight / total
        self.field_weight = field_weight / total
        self.department_weight = department_weight / total
        self.year_weight = year_weight / total

        self.min_confidence_threshold = min_confidence_threshold

    def _score_metadata_match(
        self,
        doc: Dict[str, Any],
        filter_keywords: Optional[List[str]] = None,
        field: Optional[str] = None,
        department: Optional[str] = None,
        year: Optional[Union[int, str]] = None
    ) -> float:
        score = 0.0
        if filter_keywords:
            doc_keywords = doc.get("keywords", [])
            if isinstance(doc_keywords, str):
                doc_keywords = [doc_keywords]
            keyword_match = any(k in doc_keywords for k in filter_keywords)
            score += self.keyword_weight * (1.0 if keyword_match else 0.0)
        else:
            score += self.keyword_weight

        if field:
            doc_field = doc.get("field", "").lower()
            score += self.field_weight * (1.0 if field.lower() == doc_field else 0.0)
        else:
            score += self.field_weight

        if department:
            doc_dept = doc.get("department", "").lower()
            score += self.department_weight * (1.0 if department.lower() == doc_dept else 0.0)
        else:
            score += self.department_weight

        if year:
            doc_year = str(doc.get("year", ""))
            score += self.year_weight * (1.0 if str(year) == doc_year else 0.0)
        else:
            score += self.year_weight

        return score

    def search(
        self,
        query: str,
        filter_keywords: Optional[List[str]] = None,
        field: Optional[str] = None,
        department: Optional[str] = None,
        year: Optional[Union[int, str]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        query_embedding = self.embedding_model.encode([query])[0].tolist()

        # Xây dựng hard filter
        must_conditions = []
        if filter_keywords:
            must_conditions.append(FieldCondition(
                key="keywords",
                match=MatchAny(any=filter_keywords)
            ))
        if field:
            must_conditions.append(FieldCondition(
                key="field",
                match=MatchValue(value=field)
            ))
        if department:
            must_conditions.append(FieldCondition(
                key="department",
                match=MatchValue(value=department)
            ))
        if year:
            must_conditions.append(FieldCondition(
                key="year",
                match=MatchValue(value=str(year))
            ))

        points_filter = Filter(must=must_conditions) if must_conditions else None

        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k * 10,
            with_payload=True,
            query_filter=points_filter
        )

        results_with_scores = []
        for res in results:
            payload = res.payload or {}
            metadata_score = self._score_metadata_match(
                payload,
                filter_keywords=filter_keywords,
                field=field,
                department=department,
                year=year
            )
            semantic_score = res.score
            combined_score = (
                self.metadata_weight * metadata_score +
                self.semantic_weight * semantic_score
            )
            if combined_score >= self.min_confidence_threshold:
                results_with_scores.append((res, combined_score, metadata_score, semantic_score))

        results_with_scores.sort(key=lambda x: x[1], reverse=True)
        final_results = []
        for res, combined_score, metadata_score, semantic_score in results_with_scores[:top_k]:
            doc = res.payload.copy()
            doc["combined_score"] = float(combined_score)
            doc["metadata_score"] = float(metadata_score)
            doc["semantic_score"] = float(semantic_score)
            final_results.append(doc)
        return final_results

if __name__ == "__main__":
    model = SentenceTransformer('AITeamVN/Vietnamese_Embedding')
    search_engine = HybridSearchQdrant(
        qdrant_url=os.getenv("QDRANT_URL"),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        collection_name="uit_documents_AITeamVN",
        embedding_model=model,
        metadata_weight=0.2,
        semantic_weight=0.8
    )

    while True:
        query = input("\nNhập câu hỏi (hoặc 'exit' để thoát): ").strip()
        if query.lower() == "exit":
            break

        field, filter_keywords, found_keywords, department, year = extract_field_department_year(query, keywords_dict)

        print(f"Keywords: {filter_keywords}")
        print(f"Field: {field}")
        print(f"Department: {department}")
        print(f"Year: {year}")
        results = search_engine.search(
            query=query,
            filter_keywords=filter_keywords,
            field=field,
            department=department,
            year=year,
            top_k=5
        )
        for i, doc in enumerate(results):
            print(f"\n--- Kết quả {i+1} ---")
            print(f"Score: {doc['combined_score']:.4f}")
            print(f"Title: {doc.get('title', '')}")
            print(f"Field: {doc.get('field', '')}")
            print(f"Department: {doc.get('department', '')}")
            print(f"Year: {doc.get('year', '')}")
            print(f"Content: {doc.get('content', '')[:500]}...")