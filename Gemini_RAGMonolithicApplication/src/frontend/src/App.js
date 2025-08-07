import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Header from "./components/Header";
import BottomBar from "./components/BottomBar";
import DashboardPage from "./pages/DashboardPage";
import SessionPage from "./pages/SessionPage";
import LoginPage from "./pages/LoginPage";
import { AuthProvider } from "./contexts/AuthContext";
import "./styles/global.css";

// PUBLIC_INTERFACE
// Main App component (compatible with Create React App)

function App() {
  return (
    <AuthProvider>
      <div className="main-app-layout">
        <Header />
        <main className="main-content-area">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/session/:id" element={<SessionPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
        <BottomBar />
      </div>
    </AuthProvider>
  );
}

export default App;
