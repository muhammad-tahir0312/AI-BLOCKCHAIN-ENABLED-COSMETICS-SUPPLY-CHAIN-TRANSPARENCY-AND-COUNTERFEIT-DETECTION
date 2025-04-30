import React from 'react';
import { jwtDecode } from "jwt-decode";

const AdminDashboard = () => {
  const token = localStorage.getItem("token");
  const decoded = jwtDecode(token);
  return (
    <div>
    <>
      <h1>Welcome to the Dashboard</h1>
      <h1 className='dflex text-center'>{decoded.sub}</h1>
      <p>Here you'll see supply chain insights and AI alerts.</p>
    </>
    </div>
  )
}

export default AdminDashboard;