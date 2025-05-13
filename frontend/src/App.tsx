import { Routes, Route } from "react-router-dom";
import { SignedIn, SignedOut, RedirectToSignIn } from "@clerk/clerk-react";
import Home from "./pages/Home";
import Chat from "./pages/Chat";
import Login from "./pages/Login";
import Navbar from "./components/Navbar";

export default function App() {
  return (
    <>
      <div className="flex flex-col h-screen">
        <div className="sticky top-0 z-10">
          <Navbar />
        </div>
        <div className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route
              path="/chat"
              element={
                <SignedIn>
                  <Chat />
                </SignedIn>
              }
            />
            <Route
              path="*"
              element={
                <SignedOut>
                  <RedirectToSignIn />
                </SignedOut>
              }
            />
          </Routes>
        </div>
      </div>
    </>
  );
}
