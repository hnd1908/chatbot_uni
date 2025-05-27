import { useEffect } from "react";
import Home from "./pages/Home";

function generateGuestId() {
  return "guest_" + Math.random().toString(36).slice(2, 18);
}

export default function App() {
  useEffect(() => {
    let userId = localStorage.getItem("user_id");
    if (!userId) {
      userId = generateGuestId();
      localStorage.setItem("user_id", userId);
    }
  }, []);
  return <Home />;
}
