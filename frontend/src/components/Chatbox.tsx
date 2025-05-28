import { useState, useRef, useEffect } from "react";
import axios, { CancelTokenSource } from "axios";
import DOMPurify from 'dompurify';
import { FaPaperPlane, FaStop } from "react-icons/fa";

// Định nghĩa kiểu message
type Message = {
  text: string;
  sender: "user" | "bot";
  index: number;
};

export default function Chatbox() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const cancelTokenRef = useRef<CancelTokenSource | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      text: input,
      sender: "user",
      index: messages.length,
    };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const cancelToken = axios.CancelToken.source();
      cancelTokenRef.current = cancelToken;

      const payload = { message: userMessage.text };
      const response = await axios.post(
        "http://127.0.0.1:8000/chatbot/conversation/",
        payload,
        {
          cancelToken: cancelToken.token,
          headers: {
            "X-User-ID": localStorage.getItem("user_id") || "",
          },
        }
      );

      const botMessage: Message = {
        text: response.data.chat?.bot_response || "Không nhận được phản hồi.",
        sender: "bot",
        index: messages.length + 1,
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      if (axios.isCancel(error)) {
        setMessages(prev => [...prev, {
          text: "Response cancelled",
          sender: "bot",
          index: messages.length + 1
        }]);
      } else {
        setMessages(prev => [...prev, {
          text: "Error getting response",
          sender: "bot",
          index: messages.length + 1
        }]);
      }
    } finally {
      setIsLoading(false);
      cancelTokenRef.current = null;
    }
  };

  const cancelRequest = () => {
    cancelTokenRef.current?.cancel("User cancelled request");
    setIsLoading(false);
  };

  const formatMessage = (message: string) => {
    const formatted_message = message
      .replace(/(?:\r\n|\r|\n)/g, "<br />")
      .replace(/(\*\*|__)(.*?)\1/g, "<strong>$2</strong>")
      .replace(/(\*|_)(.*?)\1/g, "<em>$2</em>")
      .replace(/~~(.*?)~~/g, "<del>$1</del>");
    return DOMPurify.sanitize(formatted_message, {
      ALLOWED_TAGS: ['strong', 'em', 'del', 'br', 'p']
    });
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => (
          <div key={msg.index} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-xs md:max-w-md lg:max-w-lg rounded-lg px-4 py-2 ${
              msg.sender === "user" ? "bg-blue-900 text-white" : "bg-gray-200 text-gray-800"
            }`}
              dangerouslySetInnerHTML={{ __html: formatMessage(msg.text) }}
            />
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Nhập câu hỏi..."
            className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={isLoading ? cancelRequest : sendMessage}
            className={`px-4 py-2 rounded-lg text-white flex items-center justify-center ${
              isLoading ? "bg-red-500 hover:bg-red-600" : "bg-blue-900 hover:bg-blue-500"
            }`}
            title={isLoading ? "Dừng" : "Gửi"}
          >
            {isLoading ? <FaStop /> : <FaPaperPlane />}
          </button>
        </div>
      </div>
    </div>
  );
}
