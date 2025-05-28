import { useEffect } from "react";
import Home from "./pages/Home";

function generateGuestId() {
  return "guest_" + Math.random().toString(36).slice(2, 18);
}

export default function App() {
  useEffect(() => {
    const userId = generateGuestId();
    localStorage.setItem("user_id", userId);
  }, []);
  return <Home />;
}
