import google.generativeai as genai
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from .models import ChatMessage, Conversation
from .serializers import ChatMessageSerializer, ConversationSerializer
from datetime import datetime
import pytz
import torch
import numpy as np
from typing import List, Dict
from qdrant_client import QdrantClient
from transformers import AutoTokenizer, AutoModel
from dotenv import load_dotenv
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)

load_dotenv()

# --- Qdrant cấu hình ---
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EMBEDDING_MODEL = "VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"
MAX_LENGTH = 256

# Qdrant client và model
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL, use_fast=False)
model = AutoModel.from_pretrained(EMBEDDING_MODEL)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
model.eval()

def get_query_embedding(query: str) -> List[float]:
    inputs = tokenizer(query, padding='max_length', truncation=True, max_length=MAX_LENGTH, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
    return embedding[0].tolist()

def retrieve_documents(query: str, top_k: int = 3) -> List[Dict]:
    try:
        query_embedding = get_query_embedding(query)
        results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True
        )
        return [{
            "score": hit.score,
            "title": hit.payload.get("title", ""),
            "content": hit.payload.get("content", ""),
            "source": hit.payload.get("source_file", "")
        } for hit in results]
    except Exception as e:
        print(f"Lỗi khi truy vấn Qdrant: {e}")
        return []

def format_response(documents: List[Dict]) -> str:
    if not documents:
        return "Không tìm thấy tài liệu phù hợp."
    response = ""
    for i, doc in enumerate(documents):
        response += f"\nTài liệu {i} (score {doc['score']:.2f}):\nTiêu đề: {doc['title']}\nNội dung: {doc['content']}\n"
    return response

# --- Google Gemini cấu hình ---
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_chat_response(user_message, history):
    model = genai.GenerativeModel("gemini-2.0-flash")
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    current_date = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
    # print(f"Current date: {current_date}")
    generation_config = {
        "temperature": 0.3,
        "max_output_tokens": 2048,
        "top_k": 20,
        "top_p": 0.95,
    }

    documents = retrieve_documents(user_message)
    docs_summary = format_response(documents)
    # print(docs_summary)

    base_prompt = f'''
    Bạn là một chatbot, trợ lý ảo thông minh và được sinh ra với mục đích tư vấn tuyển sinh cho trường Đại học Công nghệ Thông tin - ĐHQG TP.HCM (UIT). Bạn có thể trả lời các câu hỏi liên quan đến tuyển sinh, ngành học, chương trình đào tạo và các thông tin khác liên quan đến trường dựa vào các tài liệu tham khảo.
    ❗️QUAN TRỌNG: Bạn phải sử dụng toàn bộ nội dung từ các tài liệu tham khảo để trả lời. Hãy đánh giá, so sánh và tổng hợp thông tin từ nhiều tài liệu nếu cần thiết để tạo ra câu trả lời chính xác và đầy đủ nhất.

    📌 Nguyên tắc bắt buộc:
    1. Từ tất cả các tài liệu tham khảo, bạn cần đọc hết một cách chi tiết các tài liệu đó sau đó xác định câu hỏi có liên quan đến tất cả tài liệu được cung cấp không và trả lời câu hỏi một cách chính xác, đầy đủ nhất.
    2. Nếu câu hỏi liên quan đến các tài liệu hiện tại, bạn cần trả lời dựa trên các tài liệu đã được cung cấp.
    3. Nếu câu hỏi không liên quan đến tài liệu hiện tại, bạn vẫn có thể trả lời bằng kiến thức chung, nhưng phải mở đầu rõ ràng:
    → "Câu hỏi này không nằm trong các tài liệu được cung cấp. Tôi sẽ sử dụng kiến thức chung để trả lời:"
    4. Sử dụng font Unicode tiêu chuẩn.
    5. Nếu người dùng hỏi bằng ngôn ngữ khác, không phải tiếng Việt, hãy hỏi lại lịch sự:
    → "Bạn có muốn tôi trả lời bằng tiếng Việt không?"

    📅 Ngày hiện tại: {current_date}
    🏫 Trường: Đại học Công nghệ Thông tin - ĐHQG TP.HCM (UIT)
    📚 Danh sách các tài liệu tham khảo:
    {docs_summary}

    '''

    history_text = "".join(
        f"Người dùng: {msg.user_message}\nChatbot_uni: {msg.bot_response}\n" for msg in history
    )
    new_message = f"Người dùng: {user_message}\nChatbot_uni:"

    full_content = base_prompt + "\n"

    if len(history_text) + len(new_message) > 12000:
        full_content += "Lịch sử hội thoại quá dài.\n"

    full_content += history_text + new_message

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
