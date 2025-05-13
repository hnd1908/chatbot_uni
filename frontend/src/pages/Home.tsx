import { Link } from "react-router-dom";
import { SignedIn, SignedOut } from "@clerk/clerk-react";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] p-4">
      <div className="max-w-2xl text-center">
        <h1 className="text-4xl font-bold text-blue-600 mb-6">Welcome to ChatBot_uni</h1>
        <p className="text-lg text-gray-700 mb-8">
          An intelligent chatbot powered by AI. Start chatting to get instant answers to your questions.
        </p>

        <div className="flex justify-center gap-4">
          <SignedOut>
            <Link
              to="/login"
              className="bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 px-6 rounded-lg transition"
            >
              Sign In to Start Chatting
            </Link>
          </SignedOut>
          <SignedIn>
            <Link
              to="/chat"
              className="bg-green-500 hover:bg-green-600 text-white font-medium py-3 px-6 rounded-lg transition"
            >
              Go to Chat
            </Link>
          </SignedIn>
        </div>
      </div>
    </div>
  );
}