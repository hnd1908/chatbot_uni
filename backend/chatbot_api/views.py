import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    
import google.generativeai as genai
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from .models import ChatMessage, Conversation
from .serializers import ChatMessageSerializer, ConversationSerializer
from rag.hybrid_search import HybridSearchQdrant, extract_field_department_year, count_keywords_by_category
from sentence_transformers import SentenceTransformer
from rag.keywords import keywords_dict
from datetime import datetime
import pytz
import torch
import numpy as np
from typing import List, Dict
from qdrant_client import QdrantClient
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)

dotenv_path = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(dotenv_path)

# --- Qdrant cấu hình ---
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"
MAX_LENGTH = 2048

# Qdrant client và model
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embedding_model = SentenceTransformer(EMBEDDING_MODEL)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
embedding_model = embedding_model.to(device)
embedding_model.eval()

hybrid_search_engine = HybridSearchQdrant(
    qdrant_url=QDRANT_URL,
    qdrant_api_key=QDRANT_API_KEY,
    collection_name=COLLECTION_NAME,
    embedding_model=embedding_model,
    metadata_weight=0.2,
    semantic_weight=0.8
)

def retrieve_documents(query: str, top_k: int = 5) -> List[Dict]:
    try:
        field, filter_keywords, found_keywords, department, year = extract_field_department_year(query, keywords_dict)
        results = hybrid_search_engine.search(
            query=query,
            filter_keywords=filter_keywords,
            field=field,
            department=department,
            year=year,
            top_k=top_k
        )
        
        for temp_doc in results:
            if temp_doc.get("combined_score", 0) < 0.45:
                print(f"⚠️ Bỏ qua tài liệu {temp_doc.get('title', 'không có tiêu đề')} do điểm quá thấp: {temp_doc.get('combined_score', 0)}")

        return [
            {
                "score": doc.get("combined_score", 0),
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "source": doc.get("source_file", "")
            }
            for doc in results if doc.get("combined_score", 0) >= 0.45
        ]
    except Exception as e:
        print(f"Lỗi khi truy vấn Qdrant (hybrid): {e}")
        return []

def get_markdown_content_from_sources(source_files: set) -> str:
    """Đọc toàn bộ nội dung các file markdown nguồn."""
    content = ""
    for src in source_files:
        md_path = os.path.join("markdown_data", src)
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                content += f"\n---\nFile: {src}\n" + f.read()
    return content

def format_response(documents: List[Dict]) -> str:
    if not documents:
        return "Không tìm thấy tài liệu phù hợp."
    response = ""
    for i, doc in enumerate(documents):
        response += f"\nTài liệu {i} (score {doc['score']:.2f}):\nTiêu đề: {doc['title']}\nNội dung: {doc['content']}\n"
    return response

import time
# ...existing code...

def get_chat_response(user_message, history):
    model = genai.GenerativeModel("gemini-2.0-flash")
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    current_date = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
    generation_config = {
        "temperature": 0.3,
        "max_output_tokens": 2048,
        "top_k": 20,
        "top_p": 0.95,
    }

    t0 = time.time()
    documents = retrieve_documents(user_message)
    t1 = time.time()
    docs_summary = format_response(documents)
    print(documents)
    # Tạo set các file nguồn trước
    source_files = set(doc["source"] for doc in documents if doc.get("source"))
    # Sau đó mới load nội dung các file markdown
    full_markdown_content = get_markdown_content_from_sources(source_files)
    t2 = time.time()

    base_prompt = f'''
    Bạn là một chatbot, trợ lý ảo thông minh và được sinh ra với mục đích tư vấn tuyển sinh cho trường Đại học Công nghệ Thông tin - ĐHQG TP.HCM (UIT). Bạn có thể trả lời các câu hỏi liên quan đến tuyển sinh, ngành học, chương trình đào tạo và các thông tin khác liên quan đến trường dựa vào các tài liệu tham khảo.
    *QUAN TRỌNG*: Bạn phải sử dụng toàn bộ nội dung từ các tài liệu tham khảo để trả lời. Hãy đánh giá, so sánh và tổng hợp thông tin từ nhiều tài liệu nếu cần thiết để tạo ra câu trả lời chính xác và đầy đủ nhất.

    *Nguyên tắc bắt buộc*:
    1. Từ tất cả các tài liệu tham khảo, bạn cần đọc hết một cách chi tiết các tài liệu đó sau đó xác định câu hỏi có liên quan đến tất cả tài liệu được cung cấp không và trả lời câu hỏi một cách chính xác, đầy đủ nhất.
    2. Nếu câu hỏi liên quan đến các tài liệu hiện tại, bạn cần trả lời dựa trên các tài liệu đã được cung cấp.
    3. Nếu câu hỏi không liên quan đến tài liệu hiện tại, bạn vẫn có thể trả lời bằng kiến thức chung, nhưng phải mở đầu rõ ràng:
    → "Câu hỏi này không nằm trong các tài liệu được cung cấp. Tôi sẽ sử dụng kiến thức chung để trả lời:"
    4. Sử dụng font Unicode tiêu chuẩn.
    5. Nếu người dùng hỏi bằng ngôn ngữ khác, không phải tiếng Việt, hãy hỏi lại lịch sự:
    → "Bạn có muốn tôi trả lời bằng tiếng Việt không?"

    📅 Ngày hiện tại: {current_date}
    🏫 Trường: Đại học Công nghệ Thông tin - ĐHQG TP.HCM (UIT)
    📚 Danh sách các tài liệu tham khảo (các đoạn liên quan nhất):
    {docs_summary}

    📂 Nội dung đầy đủ của các file tài liệu nguồn (hãy đọc kỹ để trả lời đầy đủ nhất):
    {full_markdown_content}
    '''

    history_text = "".join(
        f"Người dùng: {msg.user_message}\nChatbot_uni: {msg.bot_response}\n" for msg in history
    )
    new_message = f"Người dùng: {user_message}\nChatbot_uni:"

    full_content = base_prompt + "\n"

    if len(history_text) + len(new_message) > 12000:
        full_content += "Lịch sử hội thoại quá dài.\n"

    full_content += history_text + new_message

    # In thời gian truy vấn và augmentation
    print(f"⏱️ Thời gian truy vấn (Qdrant): {t1 - t0:.3f} giây")
    print(f"⏱️ Thời gian augmentation (load markdown & chuẩn bị prompt): {t2 - t1:.3f} giây")

    response = model.generate_content(full_content, generation_config=generation_config)
    final_text = response.text
    
    return final_text

# --- API Views ---
@api_view(['GET', 'POST', 'DELETE'])
def conversation_handler(request):
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return Response({'error': 'Unauthorized'}, status=401)

    if request.method == "GET":
        conversation_index = request.GET.get("conversation_index")
        conversation = get_object_or_404(Conversation, conversation_index=conversation_index, user_id=user_id)
        messages = ChatMessage.objects.filter(conversation=conversation).order_by("index")
        return Response({
            "conversation_index": conversation.conversation_index,
            "messages": ChatMessageSerializer(messages, many=True).data
        })

    elif request.method == "POST":
        message = request.data.get('message', '')
        conversation_index = request.GET.get("conversation_index") or request.data.get('conversation_index')

        if not message:
            return Response({'error': 'Message is required'}, status=400)

        if conversation_index:
            conversation = get_object_or_404(Conversation, conversation_index=conversation_index, user_id=user_id)
        else:
            conversation = Conversation.objects.create(user_id=user_id)

        current_message_count = ChatMessage.objects.filter(conversation=conversation).count()
        history_messages = ChatMessage.objects.filter(conversation=conversation).order_by("index")

        response = get_chat_response(message, history_messages)
        chat = ChatMessage.objects.create(
            conversation=conversation, index=current_message_count,
            user_message=message, bot_response=response
        )

        return Response({
            "conversation_index": conversation.conversation_index,
            "chat": ChatMessageSerializer(chat).data
        })

    elif request.method == "DELETE":
        conversation_index = request.GET.get("conversation_index") or request.data.get("conversation_index")
        conversation = get_object_or_404(Conversation, conversation_index=conversation_index, user_id=user_id)
        conversation.delete()
        return Response({"message": "Deleted successfully"}, status=200)

@api_view(['GET'])
def conversation_history(request):
    user_id = request.headers.get('X-User-ID')
    conversations = Conversation.objects.filter(user_id=user_id).order_by('-conversation_index')
    if not conversations.exists():
        return Response({"error": "Không có hội thoại nào."}, status=404)
    return Response(ConversationSerializer(conversations, many=True).data)

@api_view(['POST'])
def create_new_conversation(request):
    user_id = request.headers.get('X-User-ID')
    conversation = Conversation.objects.create(user_id=user_id)
    return Response({"conversation_index": conversation.conversation_index})
