import React from "react";
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from "react-router-dom";
import { ClerkProvider } from "@clerk/clerk-react";
import './index.css'
import App from './App.tsx'

const clerkPubKey = "pk_test_YWN0aXZlLW1hc3RpZmYtNzIuY2xlcmsuYWNjb3VudHMuZGV2JA"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ClerkProvider publishableKey={clerkPubKey}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ClerkProvider>
  </React.StrictMode>
);
