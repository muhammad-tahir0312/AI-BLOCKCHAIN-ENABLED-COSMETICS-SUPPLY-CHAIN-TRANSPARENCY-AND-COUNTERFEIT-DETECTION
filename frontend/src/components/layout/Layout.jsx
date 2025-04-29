import React from "react";

export default function Layout({ children }) {
  return (
    <div className="d-flex flex-column vh-100">
      {/* Header */}
      <header className="bg-primary text-white py-3">
        <div className="container">
          <h1 className="text-center">AI Blockchain Cosmetics Supply Chain</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow-1 d-flex justify-content-center align-items-center">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-dark text-white py-3">
        <div className="container text-center">
          <p>&copy; 2025 AI Blockchain Cosmetics Supply Chain. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}