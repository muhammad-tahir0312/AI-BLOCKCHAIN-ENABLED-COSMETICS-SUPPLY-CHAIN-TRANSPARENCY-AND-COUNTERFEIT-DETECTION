import React from "react";
import { Outlet } from "react-router-dom";
import AppHeader from "../header/Header";
import AppFooter from "../footer/Footer";

export default function Layout({ children }) {
  return (
    <div className="d-flex flex-column vh-100">
      {/* Header */}
      <AppHeader />

      {/* Main Content */}
      <main className="flex-grow-1 d-flex justify-content-center align-items-center">
        {children || <Outlet />}
      </main>

      {/* Footer */}
      <AppFooter />
    </div>
  );
}