import os
import re
import unicodedata
import logging
from typing import List, Dict, Optional, Any

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Filter, FieldCondition, MatchAny, MatchValue, HasIdCondition
from sentence_transformers import SentenceTransformer

from keywords import keywords_dict

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class QdrantSearchSystem:
    def __init__(self):
        self._initialize_components()

    def _initialize_components(self):
        try:
            self.qdrant_client = QdrantClient(
                url=os.getenv("QDRANT_URL"),
                api_key=os.getenv("QDRANT_API_KEY"),
                timeout=10
            )

            if not self._check_qdrant_connection():
                raise ConnectionError("Không thể kết nối đến Qdrant server")

            self._create_indexes()

            self.model = SentenceTransformer('VoVanPhuc/sup-SimCSE-VietNamese-phobert-base')

            logger.info("Khởi tạo thành công hệ thống tìm kiếm")
        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo hệ thống: {str(e)}")
            raise

    def _check_qdrant_connection(self) -> bool:
        try:
            self.qdrant_client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Lỗi kết nối Qdrant: {str(e)}")
            return False

    def _create_indexes(self):
        for field in ["keywords", "year", "field"]:
            try:
                self.qdrant_client.create_payload_index(
                    collection_name="uit_documents",
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                logger.info(f"Đã tạo hoặc xác nhận tồn tại index cho trường '{field}'")
            except Exception as e:
                logger.warning(f"Không thể tạo index cho '{field}': {str(e)}")

    @staticmethod
    def normalize(text: str) -> str:
        text = text.lower()
        text = unicodedata.normalize('NFD', text)
        text = re.sub(r'[\u0300-\u036f]', '', text)
        return text

    def extract_filters(self, question: str) -> Dict[str, Any]:
        norm_question = self.normalize(question)

        # Từ khóa
        matched_keys = set()
        for key, kws in keywords_dict.items():
            for kw in kws:
                if self.normalize(kw) in norm_question:
                    matched_keys.add(key)
                    break  # Nếu đã match 1 từ khóa của key này thì không cần kiểm tra tiếp

        # Năm
        year_match = re.search(r"20\d{2}", question)
        year = year_match.group(0) if year_match else None

        # Lĩnh vực
        fields = ["học bổng", "tuyển sinh", "ngành", "ngoài lề"]
        field_match = next((f for f in fields if f in norm_question), None)

        # Department (ngành/khoa)
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
        department = None
        for key, name in nganh_name_map.items():
            if self.normalize(key) in norm_question or self.normalize(name) in norm_question:
                department = name
                break

        return {
            "filter_keywords": list(matched_keys),
            "year": year,
            "field": field_match,
            "department": department,
        }

    def build_query_from_question(self, question: str) -> Dict:
        filters = self.extract_filters(question)
        logger.info(
            f"Từ khóa: {filters['filter_keywords']}, Năm: {filters['year']}, Lĩnh vực: {filters['field']}, Ngành/Khoa: {filters['department']}"
        )
        return {
            "query": question,
            **filters
        }

    def query_qdrant(self, question: str, filter_keywords: List[str], year: Optional[str] = None, field: Optional[str] = None, department: Optional[str] = None, top_k: int = 5):
        try:
            question_embedding = self.model.encode([question])[0].tolist()

            # Xây dựng bộ lọc
            must_conditions = []
            if filter_keywords:
                must_conditions.append(FieldCondition(
                    key="keywords",
                    match=MatchAny(any=filter_keywords)
                ))
            if year:
                must_conditions.append(FieldCondition(
                    key="year",
                    match=MatchValue(value=year)
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

            points_filter = Filter(must=must_conditions) if must_conditions else None

            results = self.qdrant_client.search(
                collection_name="uit_documents",
                query_vector=question_embedding,
                limit=top_k,
                query_filter=points_filter,
                with_payload=True
            )

            return results

        except Exception as e:
            logger.error(f"Lỗi khi truy vấn Qdrant: {str(e)}")
            return None

    def format_results(self, results, question: str) -> str:
        if not results:
            return "⚠️ Không tìm thấy kết quả phù hợp."

        output = [f"\n🔍 Kết quả tìm kiếm cho câu hỏi: '{question}'"]

        for i, res in enumerate(results):
            payload = res.payload or {}
            keywords = payload.get('keywords', [])
            if isinstance(keywords, str):
                keywords = [keywords]

            output.append(f"\n--- Kết quả {i+1} ---")
            output.append(f"🔢 Score: {res.score:.4f}")
            output.append(f"📄 Title: {payload.get('title', 'Không có tiêu đề')}")
            output.append(f"🏷️ Keywords: {', '.join(keywords)}")
            output.append(f"📝 Nội dung: {payload.get('content', '')[:300]}...")
            output.append(f"📁 Nguồn: {payload.get('source', 'Không rõ nguồn')}")

        return "\n".join(output)


def main():
    try:
        search_system = QdrantSearchSystem()

        while True:
            question = input("\nNhập câu hỏi (hoặc 'quit' để thoát): ").strip()
            if question.lower() == "quit":
                break
            if not question:
                print("Vui lòng nhập câu hỏi.")
                continue

            query_obj = search_system.build_query_from_question(question)

            print(f"\nTừ khóa lọc: {query_obj['filter_keywords']}, Năm: {query_obj['year']}, Lĩnh vực: {query_obj['field']}")

            results = search_system.query_qdrant(
                question=query_obj["query"],
                filter_keywords=query_obj["filter_keywords"],
                year=query_obj["year"],
                field=query_obj["field"],
                top_k=5
            )
            print(search_system.format_results(results, question))
    except KeyboardInterrupt:
        print("\nĐã dừng chương trình.")
    except Exception as e:
        logger.error(f"Lỗi trong quá trình chạy: {str(e)}")


if __name__ == "__main__":
    main()
