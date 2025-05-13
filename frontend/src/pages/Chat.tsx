import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useUser } from "@clerk/clerk-react";
import Sidebar from "../components/Sidebar";
import Chatbox from "../components/Chatbox";

export default function Chat() {
  const { user } = useUser();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [conversationIndex, setConversationIndex] = useState<number | null>(null);

  useEffect(() => {
    const index = searchParams.get("conversation_index");
    setConversationIndex(index ? parseInt(index) : null);
  }, [searchParams]);

  const handleSelectConversation = (index: number) => {
    setConversationIndex(index);
    navigate(`/chat?conversation_index=${index}`);
  };

  if (!user) {
    return <div className="flex items-center justify-center h-full">Loading user data...</div>;
  }

  return (
    <div className="container mx-auto max-w-screen-2xl h-screen bg-transparent p-4">
      <div className="flex gap-5 h-full bg-transparent">
        <div className="w-1/5 rounded-lg border border-gray-100 p-4 shadow-lg">
          <Sidebar 
          onSelectConversation={handleSelectConversation}
          currentConversationIndex={conversationIndex} />
        </div>
        <div className="w-4/5 rounded-lg border border-gray-100 p-4 shadow-lg">
          <Chatbox conversationIndex={conversationIndex} setConversationIndex={handleSelectConversation} />
        </div>
      </div>
    </div>
  );
}
