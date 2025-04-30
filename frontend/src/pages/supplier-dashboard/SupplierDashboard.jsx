import React, { useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";

const SupplierDashboard = () => {
  const token = localStorage.getItem("token");
  const decoded = jwtDecode(token);

  return (
    <div className="container mt-5">
      <h2 className="text-center mb-4">Supplier Dashboard</h2>
      <h2 className="text-center mb-4">Email: {decoded.sub}</h2>
    </div>
  );
};

export default SupplierDashboard;