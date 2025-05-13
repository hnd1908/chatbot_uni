import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useUser } from "@clerk/clerk-react";

type Conversation = {
  conversation_index: number;
  created_at: string;
};

type SidebarProps = {
  onSelectConversation: (conversation_index: number | null) => void;
  currentConversationId: number | null;
};

export default function Sidebar({ onSelectConversation, currentConversationId }: SidebarProps) {
  const { user } = useUser();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [menuOpenId, setMenuOpenId] = useState<number | null>(null);
  const [menuPosition, setMenuPosition] = useState<"top" | "bottom">("bottom");
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!user?.id) return;

    const fetchConversations = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/chatbot/conversation/history/", {
          headers: { "X-User-ID": user.id }
        });
        setConversations(response.data);
      } catch (error) {
        console.error("Error fetching conversations:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchConversations();
  }, [user?.id]);

  const createNewConversation = async () => {
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/chatbot/conversation/create_new_conversation/",
        {},
        { headers: { "X-User-ID": user?.id } }
      );
      const newConv = { 
        conversation_index: response.data.conversation_index, 
        created_at: new Date().toISOString() 
      };
      setConversations([newConv, ...conversations]);
      onSelectConversation(newConv.conversation_index);
    } catch (error) {
      console.error("Error creating conversation:", error);
    }
  };

  const deleteConversation = async (conversation_index: number) => {
    try {
      await axios.delete(`http://127.0.0.1:8000/chatbot/conversation/?conversation_index=${conversation_index}`, {
        headers: { "X-User-ID": user?.id }
      });
      setConversations(conversations.filter(conv => conv.conversation_index !== conversation_index));
      if (currentConversationId === conversation_index) {
        onSelectConversation(null);
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
    }
  };

  const handleOpenInNewTab = (conversation_index: number) => {
    window.open(`/chat?conversation_index=${conversation_index}`, "_blank");
  };

  const toggleMenu = (e: React.MouseEvent, conversation_index: number) => {
    e.stopPropagation();
    
    if (menuOpenId === conversation_index) {
      setMenuOpenId(null);
      return;
    }
    if (menuRef.current) {
      const mouseY = e.clientY;
      const spaceBelow = window.innerHeight - mouseY;
      const spaceAbove = mouseY;
      setMenuPosition(spaceBelow < 20 && spaceAbove > spaceBelow ? "top" : "bottom");
    }
    setMenuOpenId(conversation_index);
  };
  

  return (
    <div className="bg-white rounded-lg border border-gray-300 shadow-lg h-full w-full flex flex-col p-2">
      <button
        onClick={createNewConversation}
        className="mb-4 p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Tạo hội thoại mới
      </button>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <ul className="mt-2 overflow-y-auto flex-grow">
          {conversations.length === 0 ? (
            <p className="text-gray-500 text-center py-4">Chưa có hội thoại nào</p>
          ) : (
            conversations.map((conv) => (
              <li
                key={conv.conversation_index}
                className={`group p-2 hover:bg-gray-200 cursor-pointer flex items-center justify-between rounded-lg ${
                  currentConversationId === conv.conversation_index ? "bg-blue-100" : ""
                }`}
                onClick={() => onSelectConversation(conv.conversation_index)}
              >
                <div className="flex items-center gap-2">
                  <span>💬</span>
                  <span className="truncate">Hội thoại #{conv.conversation_index}</span>
                </div>

                {/* Hiển thị nút menu khi hover vào hội thoại */}
                <div className="relative">
                  <button
                    onClick={(e) => toggleMenu(e, conv.conversation_index)}
                    className="p-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 rounded"
                  >
                    <img src="/icons8-menu.svg" alt="Menu Icon" className="w-4 h-4" />
                  </button>

                  {/* Menu pop-up */}
                  {menuOpenId === conv.conversation_index && (
                    <div
                      ref={menuRef}
                      className={`absolute right-0 w-40 bg-white border border-gray-300 rounded-lg shadow-lg z-10 ${
                        menuPosition === "top" ? "bottom-full mb-2" : "top-full mt-2"
                      }`}
                    >
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenInNewTab(conv.conversation_index);
                          setMenuOpenId(null);
                        }}
                        className="w-full text-left px-4 py-2 hover:bg-gray-200"
                      >
                        Mở trong tab mới
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteConversation(conv.conversation_index);
                          setMenuOpenId(null);
                        }}
                        className="w-full text-left px-4 py-2 hover:bg-gray-200"
                      >
                        Xóa hội thoại
                      </button>
                    </div>
                  )}
                </div>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
