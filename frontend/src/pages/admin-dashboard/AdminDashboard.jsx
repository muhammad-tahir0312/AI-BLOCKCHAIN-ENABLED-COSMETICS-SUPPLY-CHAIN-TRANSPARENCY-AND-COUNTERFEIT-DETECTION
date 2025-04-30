import React from 'react'

const AdminDashboard = () => {
  const access_token =  localStorage.getItem("token");
  return (
    <div>
    <>
      <h1>Welcome to the Dashboard</h1>
      <p>Here you'll see supply chain insights and AI alerts.</p>
    </>
    </div>
  )
}

export default AdminDashboard;